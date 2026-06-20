from typing import List

from pydantic import BaseModel, Field, field_validator


class Article(BaseModel):
    title: str = Field(description="Title of the article")
    summary: str = Field(description="Summary of the article")
    tags: List[str] = Field(description="List of tags for the article")
    content: str = Field(description="Content of the article")

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_json_string(cls, v):
        if isinstance(v, str):
            # Repair common LLM escaping artifacts for newlines
            return v.replace("\n", "\\n").replace("\t", "\\t")
        return v