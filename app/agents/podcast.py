from crewai import Crew, Process, Task, Agent
from app.agents.models.podcast import PodcastScript

def build_podcast_crew(
    interest: str,
    writer_model: str = "mistral/mistral-medium-latest",
    summary_model: str = "mistral/mistral-small-latest"
) -> Crew:
    # Anna (Interviewer)
    interviewer = Agent(
        role="Podcast Interviewer (Anna)",
        goal=f"Lead a natural, engaging discussion about {interest}, asking insightful questions, rephrasing complex ideas, and steering the conversation.",
        backstory="""
        You are Anna, a charismatic and curious tech podcast host. Your job is to make advanced topics accessible.
        You lead the discussion by asking questions, prompting clarifications, summarizing/rephrase what Paul says, and guiding the dialogue flow smoothly.
        Your tone is engaging, conversational, and inquisitive.
        """,
        verbose=True,
        allow_delegation=False,
        llm=writer_model,
    )

    # Paul (Specialist)
    specialist = Agent(
        role="Tech Specialist (Paul)",
        goal=f"Explain advanced technical concepts and news about {interest} clearly, giving keys of understanding, details of how it works, why it matters, and future implications.",
        backstory="""
        You are Paul, an expert technology specialist and researcher. You possess deep knowledge of the topics being discussed.
        You provide clear, structured, and insightful answers to Paul's questions, highlighting the core technical innovations and their impact.
        Your tone is professional, authoritative, yet clear and accessible.
        """,
        verbose=True,
        allow_delegation=False,
        llm=writer_model,
    )

    podcast_task = Task(
        description="""
        Based on the following table of contents and the selected news, write a natural, high-quality podcast discussion transcript. The podcast has no name.
        
        The discussion must involve Anna (the interviewer) and Paul (the specialist).
        Anna asks questions, rephrases, and guides the discussion, while Paul answers, explains the technical details, and explains why it matters.
        
        Make sure the conversation flows naturally, like a real podcast episode. Avoid dry, academic reading.
        Each turn must attribute the speaker as either 'Paul' or 'Anna' exactly.
        
        # Table of Contents
        {plan}

        # News
        {topic}
        """,
        expected_output="""
        A valid JSON object matching the PodcastScript schema, consisting of a title and a list of dialogue turns.
        Each turn must have 'speaker' (either 'Paul' or 'Anna') and the 'text' they speak.
        """,
        agent=interviewer,
        output_pydantic=PodcastScript
    )

    podcast_crew = Crew(
        manager_llm=writer_model,
        agents=[interviewer, specialist],
        process=Process.sequential,
        verbose=True,
        tasks=[podcast_task],
    )

    return podcast_crew
