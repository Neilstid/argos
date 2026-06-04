import json
import re
from typing import List

from pydantic import Field, BaseModel, field_validator, model_validator
from crewai import Crew, Agent, Process, Task

from agents.models.article import Article
from agents.seo_expert import build_seo_agent

from .fact_checker import build_fact_checker_agent
from .editor import build_editor_agent
from .redactor import build_writer_agent




from agents.models.plan import BlogPlan


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
        Provide a structured table of contents/outline and the list of selected paperIds.
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
    include_images: bool = False
) -> Crew:
    # Agents
    writer = build_writer_agent(interest=interest, model_name=writer_model, include_images=include_images)
    fact_checker = build_fact_checker_agent(interest=interest, model_name=summary_model)

    redaction_task = Task(
        description="""
        Base only on the following table of contents and the following news, 
        write a blog post content, with a title, a summary and tags. 
        You can fact check information with the fact checker.

        DO NOT:
         - Include incitations to follow a newsletter (there is none)
         - Include incitations to follow social networks (there is none)

        # Table of Contents
        {plan}

        # News
        {topic}
        """,
        expected_output="""
        An attractive blog post content, with a title, a summary and tags.

        STRICT FORMATTING REQUIREMENTS:
            1. Return ONLY a valid JSON object.
            2. **Do NOT include any line breaks (\\n), carriage returns (\\r), or tabs (\\t) outside of string values.**
            3. Never start your response with introductory text (“Here is the JSON:”) and do not end it with a conclusion. Start directly with ‘{’ and end with ‘}’.
        """,
        agent=writer,
        output_json=Article,
        response_model=Article,
    )

    redaction_crew = Crew(
        manager_llm=writer_model,
        agents=[writer, fact_checker],
        process=Process.sequential,
        verbose=True,
        tasks=[redaction_task],
    )

    return redaction_crew