# Argos

AI news blog generator. Collects RSS feeds, maps/reduces articles via LLM agents, and produces a Markdown blog post.

## Run

```bash
python main.py
```

Edit `main.py` to add/remove RSS feeds. Feeds are defined directly in `main.py` and in `feeds/ai_research.yaml`.

To view agent traces in your browser during or after a run:

```bash
uv run mlflow ui
```

`NewsBlogWorkflow` in `workflows/news_blog.py` is the main entry point. It:
1. Collects articles from feeds via `BlogCollector` (`tools/rss_feed.py`)
2. Maps summaries via `map_articles()` (`news_handler/map_reduce.py`)
3. Reduces to a selection via `reduce_articles()` 
4. Passes selected articles to the writer agent (`agents/redactor.py`)

## Env

`.env` contains API keys (excluded from git). Required: `MISTRAL_API_KEY`.

## Dependencies

Python 3.12, managed with `uv`. Install with `uv sync` or `uv pip install -e .`.

## Key libraries

- `agno` — agent framework (agents, workflows, models)
- `mistralai` — default LLM (Mistral Medium)
- `mlflow` — used for agent tracing and monitoring
- `feedparser`, `trafilatura` — RSS parsing and article extraction
- `llmlingua` — prompt compression
- `tenacity` — retry logic in `BlogCollector.fetch_content`