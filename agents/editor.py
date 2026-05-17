from crewai import Agent


def build_editor_agent(
    interest: str,
    model_name: str = "mistral/mistral-medium-latest"
) -> Agent:
    return Agent(
        role="Chief Editor",
        goal=f"Your task is to choose and produce blog articles that will catch the interest of most readers on {interest}. Select 2-3 topics to cover on the blog post based on the provided news/sources.",
        backstory=f"""
        You are the chief editor of a popular blog on {interest}.

        Your role is to create a plan based on the latest new you have been provided for your blog articles that will catch interest of most of your readers.
        You define which news should be covered. You should cover 2 or 3 topics (where each topic can be a single news or multiple ones).
        """,
        verbose=True,
        allow_delegation=False,
        llm=model_name,
    )