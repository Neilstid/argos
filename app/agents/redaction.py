from crewai import Crew, Process, Task

from app.agents.models.article import Article

from .fact_checker import build_fact_checker_agent
from .editor import build_editor_agent
from .redactor import build_writer_agent




from app.agents.models.plan import BlogPlan


def build_editor_crew(
    interest: str,
    model_name: str = "mistral/mistral-small-latest"
) -> Crew:
    editor = build_editor_agent(interest=interest, model_name=model_name)

    plan_task = Task(
        description="""
        Here are sources from today's feeds. Pick some sources (3/4 subjects) that most fits your blog's readers' interest. 
        Then create an attractive blog plan based on these selected sources.
        Make sure to list the selected paperIds in the `selected_paper_ids` field.

        # News
        {topic}
        """,
        expected_output="""
        A valid JSON object matching the BlogPlan schema. 
        Crucial: The 'table_of_contents' field contains markdown. You must strictly escape  all newlines as '\\\\n'. 
        
        **Do not output any raw control characters (\n, \t, \\n, \\t)**, and do not mix terminal output commands within the JSON string.
        If you have to use quotation marks (\") use a backslash before, like this \\"
        """,
        agent=editor,
        output_json=BlogPlan,
        response_model=BlogPlan,
    )

    editor_crew = Crew(
        manager_llm=model_name,
        agents=[editor],
        process=Process.sequential,
        verbose=True,
        tasks=[plan_task],
    )

    return editor_crew


def build_redaction_crew(
    interest: str,
    writer_model: str = "mistral/mistral-medium-latest",
    summary_model: str = "mistral/mistral-small-latest",
    include_images: bool = False,
    fact_check: bool = False
) -> Crew:
    # Agents
    writer = build_writer_agent(
        interest=interest, 
        model_name=writer_model, 
        include_images=include_images,
        allow_delgation=not fact_check
    )
    fact_checker = build_fact_checker_agent(interest=interest, model_name=summary_model)

    redaction_task = Task(
        description="""
        Based on the following table of contents and the following news, 
        write a comprehensive, high-quality blog post.
        You can fact check information with the fact checker.

        The blog post `content` field must be written in Markdown and follow this PREMIUM HYBRID LAYOUT:

        1. **Executive Summary / TL;DR**:
           - Start the content with a blockquote callout. Use `> 💡 **TL;DR:** ` followed by a 2-3 sentence high-level executive summary of the main news covered.

        2. **Key Highlights Table**:
           - Immediately below the TL;DR, include a 2-column Markdown table summarizing key metrics, insights, or innovations.
           - Use the headers: `| Metric / Innovation Area | Insight / Takeaway |`.

        3. **Structured Section Breakdowns**:
           - Use `###` headings for each topic/subject from the table of contents.
           - For each topic, write 2 to 5 paragraphs covering: Context/Background, Tech/Innovation Explanation, and Why It Matters/Future Outlook.
           - Dynamically integrate rich technical elements:
             - **Mermaid diagrams**: Use a ` ```mermaid ` block (e.g. flowchart TD or sequenceDiagram) to visually explain a concept, architecture, or workflow. Ensure Mermaid syntax is valid.
             - **LaTeX Math notation**: Use `$ ... $` for inline math or `$$ ... $$` for standalone equations if describing formulas, objective functions, or neural architecture layers.
             - **Structured Code blocks**: If a tool, library, or repository is discussed, provide clean code snippets.

        DO NOT:
         - Include incitations to follow a newsletter (there is none).
         - Include incitations to follow social networks (there is none).

        # Table of Contents
        {plan}

        # News
        {topic}
        """,
        expected_output=r"""
        A valid JSON object matching the Article schema. 
        Crucial: The 'content' field contains markdown. You must strictly escape  all newlines as '\\\\n'. 
        
        **Do not output any raw control characters (\n, \t, \\n, \\t, \|, \\|)**, and do not mix terminal output commands within the JSON string. 
        If you include double quotes (for citation or anything) add 2 backslashs behind like that: \\"
        """,
        agent=writer,
        output_pydantic=Article
    )

    # Agents list
    agents = [writer]

    # Does it need fact checking
    if fact_check:
        agents.append(fact_checker)

    redaction_crew = Crew(
        manager_llm=writer_model,
        agents=agents,
        process=Process.sequential,
        verbose=True,
        tasks=[redaction_task],
    )

    return redaction_crew