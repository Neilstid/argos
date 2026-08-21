from typing import List
from pydantic import Field
from app.agents.models.base import RobustBaseModel

class DialogueTurn(RobustBaseModel):
    speaker: str = Field(description="The speaker of the turn. MUST be either 'Paul' (interviewer) or 'Anna' (specialist).")
    text: str = Field(description="The dialog text spoken by the speaker.")

class PodcastScript(RobustBaseModel):
    title: str = Field(description="Title of the podcast episode")
    turns: List[DialogueTurn] = Field(description="Chronological dialogue turns of the podcast")

