[![Documentation Status](https://readthedocs.org/projects/argos-rss/badge/?version=latest)](https://argos-rss.readthedocs.io/fr/latest/?badge=latest)

# Argos

Argos is an AI-powered news blog generator. It automatically collects articles from configured RSS feeds, processes and summarizes them using LLM agents, and compiles them into a clean Markdown blog post.

## Features

- **RSS Feed Collection**: Parses and extracts content from multiple RSS feeds.
- **LLM Processing**: Utilizes `crewai` and `litellm` (with Mistral by default) to map and reduce articles, summarizing and selecting the most relevant news.
- **Multiple Output Formats**:
  - **Blog Article**: Generates a ready-to-publish Markdown file.
  - **Podcast**: Generates an engaging discussion dialogue between two characters—Paul (interviewer) and Anna (specialist)—and synthesizes the dialogue locally into a WAV audio file (`.wav`) along with a markdown transcript (`.md`) using `pocket-tts`.
- **Configurable**: Define your feed sources in simple `.yaml` files.

## Dependencies

- Python >= 3.12
- Project dependencies are managed with `uv`. Includes `pocket-tts` for text-to-speech.

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
OPENAI_API_KEY=your_openai_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

### Feed Configuration

Feeds are configured using `.yaml` files in the `feeds/` directory. An example configuration is available at `app/feeds/ai_research.yaml`.

## Usage

You can run the generator using the `main.py` script. 

To generate a blog article:
```bash
python main.py --config app/feeds/ai_research.yaml --output "blog_posts/news_{date}.md" --output-type blog --include-images
```

To generate a podcast (audio + transcript):
```bash
python main.py --config app/feeds/ai_research.yaml --output "podcasts/news_{date}.wav" --output-type podcast
```

### Command-Line Options

- `--config`: Path to the configuration file (e.g., `app/feeds/ai_research.yaml`). The configuration file must be in `.yaml` format.
- `--output`: Path where the generated blog post or podcast audio will be saved. You can use `{date}` to automatically include the current date in the filename.
- `--output-type`: Type of output to generate. Choices are `blog` (generates `.md` file) or `podcast` (generates `.wav` audio and matching `.md` transcript). Defaults to `blog`.
- `--include-images` / `--no-include-images`: Flag to include or exclude images/media in the generated blog post (defaults to False).

### Tracing and Monitoring

Argos integrates with [MLflow](https://mlflow.org/) to provide tracing for the underlying CrewAI agents. When you run `main.py`, traces and agent events are automatically logged to a local MLflow experiment named `argos-news-blog`.

To view these traces, launch the MLflow UI:

```bash
uv run mlflow ui
```

Then navigate to `http://localhost:5000` in your web browser.

## MCP Server

Argos includes a Model Context Protocol (MCP) server that exposes RSS feed collection and search tools to MCP-compatible AI clients (such as Claude Desktop, Cursor, Windsurf, or custom AI agents).

### Running the Server

Run the server using `fastmcp`:

```bash
# Run the MCP server
uv run fastmcp run mcp_server.py

# Run in development mode with the interactive MCP Inspector web UI
uv run fastmcp dev mcp_server.py
```

### Configuration with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "argos": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Users/Neil Farmer/Documents/GitHub/argos",
        "run",
        "fastmcp",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

Make sure to replace the path with the actual absolute path to your Argos workspace directory.

### Available Tools

- `read_feed(url, time_limit, include_images)`: Extracts articles from a single RSS URL.
- `read_feeds_from_config(config_path, time_limit, include_images)`: Extracts articles from feeds configured in a YAML file.
- `get_feed_from_url(base_url)`: Finds the RSS feed URL for a given website URL.
- `get_feeds_from_subject(subject)`: Searches for RSS feeds matching a topic using DuckDuckGo.

## Project Structure

- `main.py`: The entry point script to run the blog generator.
- `mcp_server.py`: FastMCP server exposing Argos RSS feed tools.
- `workflows/news_blog.py`: Defines the `NewsBlogWorkflow`, which orchestrates the collection, processing, and formatting of the articles.
- `feeds/`: Directory containing `.yaml` configuration files for RSS feeds.
- `agents/`: Contains the specific agent logic (e.g., `redactor.py`).
- `tools/`: Contains utility scripts like `rss_feed.py` for feed parsing.
- `news_handler/`: Contains logic for mapping and reducing the articles (`map_reduce.py`).
