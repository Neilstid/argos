from typing import List

from crewai import Agent
from pydantic import BaseModel, Field


class Mapped(BaseModel):
    paperId: str = Field(description="Id of the article to reduce")
    abstract: str = Field(description="A short (4/5 sentences) description of the content of the article")


class MappedList(BaseModel):
    articles: List[Mapped] = Field(description="List of mapped articles (containing the paperId and the article abstract)")


class Reduced(BaseModel):
    paperIds: List[str] = Field(description="List of paperId of the article to select")


def split_on_key(articles: List[dict], key: str):
    has, has_not = [], []

    for art in articles:
        if art[key] is None or art[key] == "":
            has_not.append(art)
        else:
            has.append(art)

    return has, has_not


def find_with_key_value(articles: List[dict], key: str, value: str):
    for art in articles:
        if art[key] == value:
            return art
    return None


def keep_key(articles: List[dict], keys: List[str]):
    result = []
    for art in articles:
        result.append({k: art[k] for k in keys if k in art})
    return result


def map_articles(
    articles: List[dict],
    batch_size: int = 5,
    model_name: str = "mistral/mistral-medium-latest",
) -> List[dict]:
    result, to_map = split_on_key(articles, "abstract")

    mapper = Agent(
        role="Article Summarizer",
        goal="Summarize each article concisely (4/5 sentences) with clear interest and subject description",
        backstory="""
        You are an experienced director, and your task is to summarize the articles fed to you.
        You will be provided articles, and you will sum up each article (by providing their paperId and their abstract)
        Your summary must be concise (4/5 sentences) and clear about the interest and subject about the article.
        You must be objective and factual in your summary. Keep the same paperId as the one provided.
        """,
        verbose=True,
        llm=model_name,
    )

    for i in range(0, len(to_map), batch_size):
        batch = to_map[i:i+batch_size]
        agent_articles = str(keep_key(batch, ["paperId", "title", "content"]))

        response = mapper.kickoff(
            messages=f"Bellow you will find all the article to sum up: \n {agent_articles}",
            response_format=MappedList
        )

        mapped = response.pydantic
        for ra in mapped.articles:
            found = find_with_key_value(batch, "paperId", ra.paperId)
            if found is not None:
                result.append({**found, **ra.model_dump()})

    return result


def reduce_articles(
    articles: List[dict],
    interest: str,
    min_article: int = 5,
    max_article: int = 15,
    model_name: str = "mistral/mistral-medium-latest"
):
    reducer = Agent(
        role="Article Selector",
        goal=f"Select at least {min_article} and at most {max_article} articles by giving their paperId",
        backstory=f"""
        You are editor-in-chief that choose which subject will be analysed by your team.
        Your newspaper is specialized in {interest}.
        Your role is to select at least {min_article} and at most {max_article} articles by giving their paperId.
        Select articles that may have a great impact, or articles that your readers will find interesting.
        """,
        verbose=True,
        llm=model_name,
    )

    agent_articles = str(keep_key(articles, ["paperId", "abstract"]))
    response = reducer.kickoff(
        messages=f"Bellow you will find all the article where you have to select: \n {agent_articles} \n Selected Articles:\n",
        response_format=Reduced
    )

    reduced = response.pydantic
    result = []
    for ra in reduced.paperIds:
        found = find_with_key_value(articles, "paperId", ra)
        if found is not None:
            result.append(found)

    return result


def map_and_reduce(articles: List[dict], interest: str, model_name: str = "mistral/mistral-medium-latest"):
    mapped_articles = map_articles(articles=articles, model_name=model_name)
    reduced_articles = reduce_articles(articles=mapped_articles, interest=interest, model_name=model_name)

    return keep_key(reduced_articles, ["title", "content", "media"])