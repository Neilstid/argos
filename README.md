# Argos

Argos is an AI-powered news blog generator. It automatically collects articles from configured RSS feeds, processes and summarizes them using LLM agents, and compiles them into a clean Markdown blog post.

## Features

- **RSS Feed Collection**: Parses and extracts content from multiple RSS feeds.
- **LLM Processing**: Utilizes `crewai` and `litellm` (with Mistral by default) to map and reduce articles, summarizing and selecting the most relevant news.
- **Markdown Output**: Generates a ready-to-publish Markdown file.
- **Configurable**: Define your feed sources in simple `.yaml` files.

## Dependencies

- Python >= 3.12
- Project dependencies are managed with `uv`.

## Installation

1. Clone the repository and navigate to the `argos` directory.
2. Install dependencies using `uv`:

```bash
uv sync
# OR
uv pip install -e .
```

## Configuration

### Environment Variables

You need to provide your API keys for the LLM providers you are using. Create a `.env` file in the root directory (this file is excluded from git) and add your keys. For example, if using Mistral:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
```

### Feed Configuration

Feeds are configured using `.yaml` files in the `feeds/` directory. An example configuration is available at `feeds/ai_research.yaml`.

## Usage

You can run the blog generator using the `main.py` script. 

```bash
python main.py --config feeds/ai_research.yaml --output "blog_posts/news_{date}.md" --include-images
```

### Command-Line Options

- `--config`: Path to the configuration file (e.g., `feeds/ai_research.yaml`). The configuration file must be in `.yaml` format.
- `--output`: Path where the generated blog post will be saved. You can use `{date}` to automatically include the current date in the filename (e.g., `output_{date}.md`). Must be a `.md` file.
- `--include-images` / `--no-include-images`: Flag to include or exclude images/media in the generated blog post (defaults to False).

## Project Structure

- `main.py`: The entry point script to run the blog generator.
- `workflows/news_blog.py`: Defines the `NewsBlogWorkflow`, which orchestrates the collection, processing, and formatting of the articles.
- `feeds/`: Directory containing `.yaml` configuration files for RSS feeds.
- `agents/`: Contains the specific agent logic (e.g., `redactor.py`).
- `tools/`: Contains utility scripts like `rss_feed.py` for feed parsing.
- `news_handler/`: Contains logic for mapping and reducing the articles (`map_reduce.py`).
