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




def build_redaction_crew(
    interest: str,
    model_name: str = "mistral/mistral-medium-latest"
) -> Crew:
    # Agents
    writer = build_writer_agent(interest=interest, model_name=model_name)
    fact_checker = build_fact_checker_agent(interest=interest, model_name=model_name)
    editor = build_editor_agent(interest=interest, model_name=model_name)

    plan_task = Task(
        description="""
        Here are sources from today feeds. Pick some sources (3/4 subjects) that most fits to your blog's readers interest. 
        Then create an attractive blog plan based on these selected sources

        # News
        {topic}
        """,
        expected_output="""
        Provide a structured table of content that covers the news you have selected
        """,
        agent=editor,
    )

    redaction_task = Task(
        description="""
        Base only on the table of content in your context and the following news, 
        write a blog post content, with a title, a summary and tags. 
        You can fact check informations with the fact checker.

        DO NOT:
         - Include incitations to follow a newsletter (there is none)
         - Include incitations to follow social networks (there is none)

        # News
        {topic}
        """,
        
        expected_output="""
        An attractive blog post content, with a title, a summary and tags.

        STRICT FORMATTING REQUIREMENTS:
            1. Return ONLY a valid JSON object.
            2. **Do NOT include any line breaks (\n), carriage returns (\r), or tabs (\t) outside of string values.**
            3. Never start your response with introductory text (“Here is the JSON:”) and do not end it with a conclusion. Start directly with ‘{’ and end with ‘}’.
        """,
        agent=writer,
        output_json=Article,
        response_model=Article,
        context=[plan_task]
    )

    redaction_crew = Crew(
        manager_llm=model_name,
        agents=[writer, fact_checker, editor],
        process=Process.sequential,
        verbose=True,
        tasks=[plan_task, redaction_task],
    )

    return redaction_crew