from typing import List

from pydantic import Field
from app.agents.models.base import RobustBaseModel


class BlogPlan(RobustBaseModel):
    selected_paper_ids: List[str] = Field(
        description="List of paperIds of the articles selected to cover in the blog post."
    )
    table_of_contents: str = Field(
        description="A structured table of content / outline that covers the selected news."
    )

