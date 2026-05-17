from crewai import Agent

def build_seo_agent(
    interest: str,
    model_name: str = "mistral/mistral-medium-latest"
) -> Agent:
    return Agent(
        role="SEO Expert",
        goal=f"Optimize the referencement of the blog by optimizing tags and title.",
        backstory=f"""
        You are the SEO (Search Engine Optimization) Expert. 
        Your role is to optimize the title and tags of the blog post to have the best referencement on web search.

        You keep the style, expression, topics, ... of the writing. 
        """,
        verbose=True,
        allow_delegation=False,
        llm=model_name,
    )