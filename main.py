from workflows.news_blog import NewsBlogWorkflow
import click
from datetime import datetime
from dotenv import load_dotenv

@click.command()
@click.option('--config', type=click.Path(), help='Path to the configuration file (hint: check in feeds folder). Configuration file must be in .yaml format.')
@click.option('--output', type=click.Path(), help='Blog post saving path. You may include date with {date}. Blog post must be .md')
@click.option('--include-images/--no-include-images', default=None, help='Include or exclude images/media in the blog post (defaults to False).')
def write_blog(
    config: str,
    output: str,
    include_images: bool
):
    # Formatted output path
    data = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    output = output.format(**data)

    tw = NewsBlogWorkflow()
    tw.build(config)
    tw.run(include_images=include_images)
    tw.format(output)

if __name__ == '__main__':
    load_dotenv()
    write_blog()
