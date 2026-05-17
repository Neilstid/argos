from typing import List

from pydantic import BaseModel, Field


class Article(BaseModel):
    title: str = Field(description="Title of the article")
    summary: str = Field(description="Summary of the article")
    tags: List[str] = Field(description="List of tags for the article")
    content: str = Field(description="Content of the article")