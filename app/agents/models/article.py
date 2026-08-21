from typing import List

from pydantic import Field
from app.agents.models.base import RobustBaseModel


class Article(RobustBaseModel):
    title: str = Field(description="Title of the article")
    summary: str = Field(description="Summary of the article")
    tags: List[str] = Field(description="List of tags for the article")
    content: str = Field(description="Content of the article")