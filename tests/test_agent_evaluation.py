import json
import os
import pytest
from datetime import datetime
from pydantic import BaseModel, Field
import litellm
from dotenv import load_dotenv
import pandas as pd
import mlflow
from mlflow.metrics.genai import make_genai_metric

# Ensure environment variables are loaded
load_dotenv()

from app.workflows.news_blog import NewsBlogWorkflow
from app.tools.rss_feed import BlogCollector

# Pydantic schemas for structured LLM evaluation response
class CriteriaEvaluation(BaseModel):
    score: int = Field(..., description="Score from 1 to 5 (integer). 1 is poor, 5 is excellent.")
    justification: str = Field(..., description="Reasoning and explanation for the score, citing specific content.")

class EvaluationReport(BaseModel):
    tone_and_style: CriteriaEvaluation = Field(
        ...,
        description="Evaluates storytelling-driven, authoritative, senior tech journalist tone, readability, light wit, and absolute lack of emojis."
    )
    technical_richness: CriteriaEvaluation = Field(
        ...,
        description="Evaluates integration of LaTeX math equations, valid Mermaid diagrams, and code blocks."
    )
    structure_adherence: CriteriaEvaluation = Field(
        ...,
        description="Evaluates presence of TL;DR callout, key highlights table, section breaks, and absence of newsletter/social CTAs."
    )
    factuality_accuracy: CriteriaEvaluation = Field(
        ...,
        description="Evaluates consistency/accuracy compared to original source articles, citation of sources, and absence of hallucinated facts."
    )
    overall_score: float = Field(..., description="The overall average or weighted score for the generated blog post (1.0 to 5.0).")
    summary_of_strengths: str = Field(..., description="Details of what the agent did well.")
    summary_of_improvements: str = Field(..., description="Specific areas for improvement or issues identified.")


@pytest.mark.eval
def test_agent_workflow_evaluation(use_live_feeds, monkeypatch):
    """
    Evaluates the news blog workflow agents (Editor and Writer crews) using LLM-as-a-judge.
    Runs on mock fixtures by default, or live feeds when --live-feeds is passed.
    """
    # 1. Initialize workflow
    workflow = NewsBlogWorkflow()
    workflow.build("app/feeds/ai_research.yaml")

    source_articles = []

    # 2. Setup data source (mock fixtures or live feeds)
    if not use_live_feeds:
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "mock_news.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            mock_data = json.load(f)
        
        # Monkeypatch feed reader to return mock data immediately without fetching from web
        monkeypatch.setattr(BlogCollector, "collect", lambda *args, **kwargs: mock_data)
        source_articles = mock_data
        print("\n[EVAL] Running with static mock fixtures...")
    else:
        print("\n[EVAL] Running with live RSS feeds...")
        # To get the source articles in case of live feeds, we inspect what collect gathers
        original_collect = BlogCollector.collect
        def mock_collect_spy(self, *args, **kwargs):
            res = original_collect(self, *args, **kwargs)
            source_articles.extend(res)
            return res
        monkeypatch.setattr(BlogCollector, "collect", mock_collect_spy)
 
    # 3. Run the workflow to produce the blog post
    # Set include_images=True to test visual richness (Mermaid/LaTeX/Media)
    workflow.run(include_images=True)
    formatted_post = workflow.format()

    assert formatted_post is not None
    assert len(formatted_post) > 0

    # If live feeds, check that we successfully captured source articles
    if use_live_feeds:
        assert len(source_articles) > 0

    # 4. Invoke LLM-as-a-Judge via MLflow evaluate
    judge_model = os.environ.get("EVAL_JUDGE_MODEL", "mistral/mistral-large-latest")
    api_key = os.environ.get("MISTRAL_API_KEY")

    if not api_key:
        pytest.fail("MISTRAL_API_KEY environment variable is required to run evaluations.")

    print(f"[EVAL] Evaluating generated article using MLflow with judge model: {judge_model}...")

    # MLflow expects the judge model URI format as provider:/model_name (e.g. mistral:/mistral-large-latest)
    judge_model_uri = judge_model.replace("/", ":/", 1) if "/" in judge_model else f"mistral:/{judge_model}"

    # Define custom GenAI metrics
    tone_and_style_metric = make_genai_metric(
        name="tone_and_style",
        definition=(
            "Evaluates storytelling-driven, authoritative, senior tech journalist tone, "
            "readability, light wit, and absolute lack of emojis."
        ),
        grading_prompt=(
            "Evaluate the tone and style of the generated blog post. "
            "Grade the output based on the following rubric:\n"
            "5: Excellent, professional, storytelling-driven, authoritative tech journalist persona. "
            "Light, intelligent wit. Absolutely no emojis or smileys.\n"
            "3: Good writing, but may contain emojis, smileys, or overly casual language/jokes.\n"
            "1: Extremely casual, boring, or inappropriate tone.\n\n"
            "Generated Blog Post (Output):\n{output}"
        ),
        model=judge_model_uri,
        greater_is_better=True,
    )

    technical_richness_metric = make_genai_metric(
        name="technical_richness",
        definition=(
            "Evaluates integration of LaTeX math equations, valid Mermaid diagrams, and code blocks."
        ),
        grading_prompt=(
            "Evaluate the technical and visual richness of the generated blog post. "
            "Grade the output based on the following rubric:\n"
            "5: Successfully includes LaTeX math equations ($...$ or $$...$$) where relevant to describe formulas, "
            "valid Mermaid diagrams (```mermaid) explaining concept flows, and structured markdown code blocks.\n"
            "3: Includes some code blocks but misses LaTeX math or Mermaid diagrams where they would be highly relevant.\n"
            "1: Lacks code blocks, math, and diagrams entirely.\n\n"
            "Generated Blog Post (Output):\n{output}"
        ),
        model=judge_model_uri,
        greater_is_better=True,
    )

    structure_adherence_metric = make_genai_metric(
        name="structure_adherence",
        definition=(
            "Evaluates presence of TL;DR callout, key highlights table, section breaks, and absence of newsletter/social CTAs."
        ),
        grading_prompt=(
            "Evaluate the structure and layout adherence of the generated blog post. "
            "Grade the output based on the following rubric:\n"
            "5: Perfect adherence to the premium layout. Starts with a blockquote callout `> 💡 **TL;DR:** ` with a 2-3 sentence summary. "
            "Immediately followed by a 2-column markdown table (`| Metric / Innovation Area | Insight / Takeaway |`). Uses `###` headings for sections with 2-5 paragraphs each. "
            "No newsletter or social network follow CTAs.\n"
            "3: Follows some structural elements but misses others (e.g. table is missing or wrongly structured, missing the TL;DR format, or has newsletter calls).\n"
            "1: Standard unstructured text without required sections.\n\n"
            "Generated Blog Post (Output):\n{output}"
        ),
        model=judge_model_uri,
        greater_is_better=True,
    )

    factuality_accuracy_metric = make_genai_metric(
        name="factuality_accuracy",
        definition=(
            "Evaluates consistency/accuracy compared to original source articles, "
            "citation of sources, and absence of hallucinated facts."
        ),
        grading_prompt=(
            "Evaluate the factuality and accuracy of the generated blog post compared to the source articles. "
            "Grade the output based on the following rubric:\n"
            "5: Completely faithful to the source articles. Cites details/paperIds correctly. No hallucinated parameter sizes, release dates, or benchmarking numbers.\n"
            "3: Mostly accurate but has minor inconsistencies or makes claims not fully supported by sources.\n"
            "1: Heavy hallucinations, incorrect facts, or fails to cite or reference anything.\n\n"
            "Source News Articles (Inputs):\n{inputs}\n\n"
            "Generated Blog Post (Output):\n{output}"
        ),
        model=judge_model_uri,
        greater_is_better=True,
    )

    # Build evaluation DataFrame
    eval_df = pd.DataFrame({
        "inputs": [json.dumps(source_articles, indent=2)],
        "outputs": [formatted_post]
    })

    # Set experiment for evaluation
    mlflow.set_experiment("argos-evaluations")

    # Run evaluation
    with mlflow.start_run():
        eval_results = mlflow.evaluate(
            data=eval_df,
            predictions="outputs",
            extra_metrics=[
                tone_and_style_metric,
                technical_richness_metric,
                structure_adherence_metric,
                factuality_accuracy_metric
            ],
            evaluator_config={
                "col_mapping": {
                    "inputs": "inputs",
                    "outputs": "outputs"
                }
            }
        )

    # Extract results from evaluation results table
    eval_results_table = eval_results.tables["eval_results_table"]
    row = eval_results_table.iloc[0]

    def get_metric_values(metric_name):
        score_val = row.get(f"{metric_name}/score")
        if score_val is None:
            score_val = row.get(f"{metric_name}/v1/score")
        
        justification_val = row.get(f"{metric_name}/justification")
        if justification_val is None:
            justification_val = row.get(f"{metric_name}/v1/justification")
            
        return int(score_val) if score_val is not None else 0, str(justification_val) if justification_val is not None else ""

    tone_score, tone_just = get_metric_values("tone_and_style")
    tech_score, tech_just = get_metric_values("technical_richness")
    struct_score, struct_just = get_metric_values("structure_adherence")
    fact_score, fact_just = get_metric_values("factuality_accuracy")

    overall_score = (tone_score + tech_score + struct_score + fact_score) / 4.0

    strengths_list = []
    improvements_list = []
    for metric_name, score, justification in [
        ("Tone & Style", tone_score, tone_just),
        ("Technical Richness", tech_score, tech_just),
        ("Structure Adherence", struct_score, struct_just),
        ("Factuality & Accuracy", fact_score, fact_just)
    ]:
        if score >= 4:
            strengths_list.append(f"- **{metric_name}** (Score: {score}/5): {justification}")
        else:
            improvements_list.append(f"- **{metric_name}** (Score: {score}/5): {justification}")
            
    summary_of_strengths = "\n".join(strengths_list) if strengths_list else "No major strengths identified."
    summary_of_improvements = "\n".join(improvements_list) if improvements_list else "No major improvements needed."

    # 5. Output results to console
    print("\n" + "="*30 + " EVALUATION RESULTS " + "="*30)
    print(f"Judge Model: {judge_model}")
    print(f"Date:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data Source: {'Live Feeds' if use_live_feeds else 'Mock Fixtures'}")
    print("-" * 80)
    
    headers = ["Metric / Criteria", "Score", "Justification Summary"]
    row_format = "{:<25} | {:<5} | {:<45}"
    print(row_format.format(*headers))
    print("-" * 80)
    print(row_format.format("Tone & Style", f"{tone_score}/5", tone_just[:45] + "..."))
    print(row_format.format("Technical Richness", f"{tech_score}/5", tech_just[:45] + "..."))
    print(row_format.format("Structure Adherence", f"{struct_score}/5", struct_just[:45] + "..."))
    print(row_format.format("Factuality & Accuracy", f"{fact_score}/5", fact_just[:45] + "..."))
    print("-" * 80)
    print(row_format.format("OVERALL SCORE", f"{overall_score}/5", "Average overall rating."))
    print("=" * 80)
    print(f"\nStrengths:\n{summary_of_strengths}")
    print(f"\nImprovements Needed:\n{summary_of_improvements}")
    print("=" * 80)

    # 6. Save report to JSON file
    reports_dir = os.path.join(os.path.dirname(__file__), "eval_reports")
    os.makedirs(reports_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"eval_report_{timestamp}.json"
    report_path = os.path.join(reports_dir, report_filename)

    full_report = {
        "timestamp": datetime.now().isoformat(),
        "judge_model": judge_model,
        "data_source": "live_feeds" if use_live_feeds else "mock_fixtures",
        "generated_article": {
            "title": workflow._NewsBlogWorkflow__result.get("title") if workflow._NewsBlogWorkflow__result else "N/A",
            "content": formatted_post
        },
        "scores": {
            "tone_and_style": {"score": tone_score, "justification": tone_just},
            "technical_richness": {"score": tech_score, "justification": tech_just},
            "structure_adherence": {"score": struct_score, "justification": struct_just},
            "factuality_accuracy": {"score": fact_score, "justification": fact_just},
            "overall_score": overall_score,
            "summary_of_strengths": summary_of_strengths,
            "summary_of_improvements": summary_of_improvements
        }
    }

    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(full_report, rf, indent=2)
    print(f"\n[EVAL] Saved detailed report to: {report_path}")

    # 7. Assert minimum overall score threshold
    assert overall_score >= 3.0, f"Agent evaluation failed: overall score is {overall_score} (threshold: 3.0)"
