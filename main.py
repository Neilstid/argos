from workflows.news_blog import NewsBlogWorkflow
import click
from datetime import datetime
from dotenv import load_dotenv

@click.command()
@click.option('--config', type=click.Path(), help='Path to the configuration file (hint: check in feeds folder). Configuration file must be in .yaml format.')
@click.option('--output', type=click.Path(), help='Blog post saving path. You may include date with {date}. Blog post must be .md')
def write_blog(
    config: str,
    output: str
):
    # Formatted output path
    data = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    output = output.format(**data)

    tw = NewsBlogWorkflow()
    tw.build(config)
    tw.run(1)
    tw.format(output)

if __name__ == '__main__':
    load_dotenv()
    write_blog()
