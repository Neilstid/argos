from app.workflows.news_blog import NewsBlogWorkflow
import click
from datetime import datetime
from dotenv import load_dotenv
import mlflow

@click.command()
@click.option('--config', type=click.Path(), help='Path to the configuration file (hint: check in feeds folder). Configuration file must be in .yaml format.')
@click.option('--output', type=click.Path(), help='Blog post or podcast saving path. You may include date with {date}.')
@click.option('--output-type', type=click.Choice(['blog', 'podcast', 'blogcast']), default='blog', help='Type of output to generate: blog (.md), podcast (.wav), or blogcast (.md + .wav).')
@click.option('--include-images/--no-include-images', default=False, help='Include or exclude images/media in the blog post (defaults to False).')
@click.option('--image-folder', type=click.Path(), default="", help='Path to the folder where the image should be stored')
@click.option('--fact-check/--no-fact-check', default=False, help='Whether or not to fact check data (defaults to False).')
def write_blog(
    config: str,
    output: str,
    output_type: str,
    include_images: bool,
    image_folder: str,
    fact_check: bool
):
    """Generate and write the news blog or podcast.

    :param config: Path to the configuration file (e.g. in feeds folder)
    :type config: str
    :param output: Blog post or podcast saving path
    :type output: str
    :param output_type: Type of output to generate
    :type output_type: str
    :param include_images: Include or exclude images/media in the blog post, defaults to None
    :type include_images: bool, optional
    :param image_folder: Path to the folder where the image should be stored, defaults to ""
    :type image_folder: str, optional
    :param fact_check: Whether or not to fact check data, defaults to False
    :type fact_check: bool, optional
    :return: None
    :rtype: None
    """
    # Formatted output path
    data = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    if output:
        output = output.format(**data)
    else:
        output = f"blog_{data['date']}"

    tw = NewsBlogWorkflow()
    tw.build(config)
    tw.run(
        include_images=include_images,
        fact_check=fact_check,
        output_type=output_type,
        image_folder=image_folder
    )
    tw.format(output)

if __name__ == '__main__':
    load_dotenv()
    # mlflow.set_experiment("argos-news-blog")
    # mlflow.crewai.autolog()
    write_blog()
