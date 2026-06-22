import json
import os
import pytest
from datetime import datetime
from pydantic import BaseModel, Field
import litellm
from dotenv import load_dotenv

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
    workflow.build("feeds/ai_research.yaml")

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

    # 4. Invoke LLM-as-a-Judge
    judge_model = os.environ.get("EVAL_JUDGE_MODEL", "mistral/mistral-large-latest")
    api_key = os.environ.get("MISTRAL_API_KEY")

    if not api_key:
        pytest.fail("MISTRAL_API_KEY environment variable is required to run evaluations.")

    print(f"[EVAL] Evaluating generated article using judge model: {judge_model}...")

    system_prompt = (
        "You are an expert, objective AI-as-a-judge system designed to evaluate the outputs of AI content generation agents.\n"
        "Your task is to grade the provided blog post against a set of source news articles and a strict set of style, structure, and quality guidelines.\n"
        "Provide objective, honest scores from 1 to 5 and thorough, constructive justifications.\n"
        "Return your evaluation conforming strictly to the requested JSON schema."
    )

    user_prompt = f"""Please evaluate the following generated blog post.

### Source News Articles (Original Context):
{json.dumps(source_articles, indent=2)}

### Generated Blog Post (Output):
{formatted_post}

### Grading Criteria & Rubrics:
1. **Tone & Style** (Score 1-5):
   - 5: Excellent, professional, storytelling-driven, authoritative tech journalist persona. Light, intelligent wit. Absolutely no emojis or smileys.
   - 3: Good writing, but may contain emojis, smileys, or overly casual language/jokes.
   - 1: Extremely casual, boring, or inappropriate tone.
2. **Technical & Visual Richness** (Score 1-5):
   - 5: Successfully includes LaTeX math equations ($...$ or $$...$$) where relevant to describe formulas, valid Mermaid diagrams (```mermaid) explaining concept flows, and structured markdown code blocks.
   - 3: Includes some code blocks but misses LaTeX math or Mermaid diagrams where they would be highly relevant.
   - 1: Lacks code blocks, math, and diagrams entirely.
3. **Structure & Layout Adherence** (Score 1-5):
   - 5: Perfect adherence to the premium layout. Starts with a blockquote callout `> 💡 **TL;DR:** ` with a 2-3 sentence summary. Immediately followed by a 2-column markdown table (`| Metric / Innovation Area | Insight / Takeaway |`). Uses `###` headings for sections with 2-5 paragraphs each. No newsletter or social network follow CTAs.
   - 3: Follows some structural elements but misses others (e.g. table is missing or wrongly structured, missing the TL;DR format, or has newsletter calls).
   - 1: Standard unstructured text without required sections.
4. **Factuality & Accuracy** (Score 1-5):
   - 5: Completely faithful to the source articles. Cites details/paperIds correctly. No hallucinated parameter sizes, release dates, or benchmarking numbers.
   - 3: Mostly accurate but has minor inconsistencies or makes claims not fully supported by sources.
   - 1: Heavy hallucinations, incorrect facts, or fails to cite or reference anything.

Return the JSON response.
"""

    try:
        response = litellm.completion(
            model=judge_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=EvaluationReport,
            temperature=0.0
        )
        raw_content = response.choices[0].message.content
        eval_report = EvaluationReport.model_validate_json(raw_content)
    except Exception as e:
        print(f"[EVAL] Structured parsing failed or LLM error: {e}. Attempting standard parsing...")
        # Fallback parsing in case response_format isn't fully supported by the model/endpoint
        try:
            response = litellm.completion(
                model=judge_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt + "\nIMPORTANT: Return ONLY a valid JSON object matching the schema."}
                ],
                temperature=0.0
            )
            raw_content = response.choices[0].message.content
            # Clean potential markdown wrapping
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0].strip()
            eval_report = EvaluationReport.model_validate_json(raw_content)
        except Exception as fallback_err:
            pytest.fail(f"Failed to generate/parse evaluation report from LLM: {fallback_err}")

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
    print(row_format.format("Tone & Style", f"{eval_report.tone_and_style.score}/5", eval_report.tone_and_style.justification[:45] + "..."))
    print(row_format.format("Technical Richness", f"{eval_report.technical_richness.score}/5", eval_report.technical_richness.justification[:45] + "..."))
    print(row_format.format("Structure Adherence", f"{eval_report.structure_adherence.score}/5", eval_report.structure_adherence.justification[:45] + "..."))
    print(row_format.format("Factuality & Accuracy", f"{eval_report.factuality_accuracy.score}/5", eval_report.factuality_accuracy.justification[:45] + "..."))
    print("-" * 80)
    print(row_format.format("OVERALL SCORE", f"{eval_report.overall_score}/5", "Average overall rating."))
    print("=" * 80)
    print(f"\nStrengths:\n{eval_report.summary_of_strengths}")
    print(f"\nImprovements Needed:\n{eval_report.summary_of_improvements}")
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
        "scores": eval_report.model_dump()
    }

    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(full_report, rf, indent=2)
    print(f"\n[EVAL] Saved detailed report to: {report_path}")

    # 7. Assert minimum overall score threshold
    assert eval_report.overall_score >= 3.0, f"Agent evaluation failed: overall score is {eval_report.overall_score} (threshold: 3.0)"
