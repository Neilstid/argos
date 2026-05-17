from typing import Dict, List

from crewai import Agent
from crewai.tools import tool
from ddgs.ddgs import DDGS

from agents.models.article import Article


@tool
def websearch(query: str) -> List[Dict[str, str]]:
    """
    Tool to do research on internet based on a query

    :param query: Query to search for
    :type query: str
    :return: Web search result pages
    :rtype: List[Dict[str, str]]
    """
    return DDGS().text(
        query=query,
        region="us-en",
        safesearch="moderate",
        timelimit=None,
        max_results=5,
        page=1,
        backend="auto"
    )



def build_fact_checker_agent(
    interest: str,
    model_name: str = "mistral/mistral-medium-latest"
) -> Agent:

    return Agent(
        role="Fact Checker",
        goal="Verify information, add context and explanation to be as clear as possible. Ensure all facts are accurate.",
        backstory=f"""
        You are an expert in fact checking and internet search. 
        You verify information, add context and more explanation to be as clear as possible.
        You keep your search query simple (only single or few words only) but yet effective.

        To verify your information you do internet research with your tool.
        You keep the style, expression, topics, ... of the writing. 
        You are helping on a blog that is specialized on {interest}.
        """,
        verbose=True,
        allow_delegation=False,
        tools=[websearch],
        llm=model_name,
        response_format=Article
    )