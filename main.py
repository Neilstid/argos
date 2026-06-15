from workflows.news_blog import NewsBlogWorkflow
import click
from datetime import datetime
from dotenv import load_dotenv
import mlflow

@click.command()
@click.option('--config', type=click.Path(), help='Path to the configuration file (hint: check in feeds folder). Configuration file must be in .yaml format.')
@click.option('--output', type=click.Path(), help='Blog post saving path. You may include date with {date}. Blog post must be .md')
@click.option('--include-images/--no-include-images', default=False, help='Include or exclude images/media in the blog post (defaults to False).')
@click.option('--fact-check/--no-fact-check', default=False, help='Whether or not to fact check data (defaults to False).')
def write_blog(
    config: str,
    output: str,
    include_images: bool,
    fact_check: bool
):
    """Generate and write the news blog.

    :param config: Path to the configuration file (e.g. in feeds folder)
    :type config: str
    :param output: Blog post saving path
    :type output: str
    :param include_images: Include or exclude images/media in the blog post, defaults to None
    :type include_images: bool, optional
    :return: None
    :rtype: None
    """
    # Formatted output path
    data = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    output = output.format(**data)

    tw = NewsBlogWorkflow()
    tw.build(config)
    tw.run(
        include_images=include_images,
        fact_check=fact_check
    )
    tw.format(output)

if __name__ == '__main__':
    load_dotenv()
    mlflow.set_experiment("argos-news-blog")
    mlflow.crewai.autolog()
    write_blog()
