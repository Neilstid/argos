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

    redaction_task = Task(
        description="""
        Base only on the table of content in your context and the following news, 
        write a blog post content, with a title, a summary and tags.

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
        response_model=Article
    )

    crew = Crew(
        agents=[writer],
        tasks=[redaction_task],
        verbose=True,
        process=Process.sequential,
    )

    return crew