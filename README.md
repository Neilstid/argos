![Argos Banner](./assets/argos_banner.png)

# 🏛️ Argos

[![Documentation Status](https://readthedocs.org/projects/argos-rss/badge/?version=latest)](https://argos-rss.readthedocs.io/en/latest/?badge=latest)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Built with CrewAI](https://img.shields.io/badge/built%20with-CrewAI-red.svg)](https://github.com/crewAIInc/crewAI)
[![MCP Powered](https://img.shields.io/badge/MCP-FastMCP-green.svg)](https://github.com/modelcontextprotocol)

**Argos** is a professional, AI-powered news blog generator and podcast synthesizer. It automatically aggregates articles from configured RSS feeds, performs intelligent Map-Reduce summarization and content selection via collaborative **CrewAI** agents, and outputs polished, publication-ready Markdown blogs, engaging podcast audio/transcripts, or combined "Blogcasts" complete with an embedded audio player.

---

## ✨ Features

- 📥 **RSS Feed Aggregation**: Automatically fetches, parses, and extracts full text content from configured RSS feeds using `feedparser` and `trafilatura` with robust retry logic (`tenacity`).
- 🤖 **Multi-Agent Editorial workflows (CrewAI)**:
  - **Editor Agent**: Picks the most relevant papers/topics aligned with the configured target interests and constructs a logical table of contents.
  - **Writer Agent**: Produces a comprehensive, high-quality article featuring executive TL;DR callouts, highlights tables, dynamic **Mermaid diagrams**, and **LaTeX mathematical equations** (Hugo-compatible).
  - **Fact-Checker Agent**: Optional step to verify data and ground claims in source texts.
- 🎙️ **Automated Podcast & Text-to-Speech (TTS)**:
  - Generates conversational dialogue between two hosts: **Paul** (interviewer) and **Anna** (subject matter expert).
  - Synthesizes speech locally into high-quality WAV audio using `pocket-tts` or `kokoro`.
- 🎛️ **Versatile Output Types**:
  - `blog`: A Hugo-compatible Markdown file (`.md`).
  - `podcast`: A synthesized audio file (`.wav`) along with its text script.
  - `blogcast`: A Markdown article with a built-in HTML5 `<audio>` player referencing the synthesized WAV podcast.
- 🖼️ **Media Manager**: Automatically downloads source media files locally to include in your final blog post.
- 🌐 **Built-in FastMCP Server**: Exposes RSS feed extraction, feed discovery, and search tools to Model Context Protocol (MCP) clients (e.g., Claude Desktop, Cursor).
- 📊 **Agent Tracing**: Auto-logs agent execution traces to **MLflow** for debugging, optimization, and auditing.

---

## 🛠️ Installation

Argos requires **Python 3.12+**. It is managed using **`uv`**, a fast Python package installer and resolver.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Neilstid/argos.git
   cd argos
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   # OR
   uv pip install -e .
   ```

---

## ⚙️ Configuration

### Environment Variables

Argos leverages LiteLLM under the hood, allowing compatibility with many LLM providers. By default, it uses Mistral. Create a `.env` file in the root directory:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Feed Configuration

Feeds are defined in `.yaml` files. A sample configuration is available at [ai_research.yaml](./app/feeds/ai_research.yaml):

```yaml
interest: "Artificial Intelligence, Deep Learning, Agents, LLMs"
time_limit: 1  # Number of days to look back
summary_model: "mistral/mistral-small-latest"
writer_model: "mistral/mistral-medium-latest"
sources:
  - https://huggingface.co/api/daily_papers.rss
```

---

## 🚀 Usage

You can run the generator using the `main.py` CLI script.

### 1. Generate a Blog Article
Generates a structured Hugo Markdown blog post with highlights, Mermaid diagrams, and LaTeX math.
```bash
python main.py --config app/feeds/ai_research.yaml --output "blog_posts/news_{date}.md" --output-type blog --include-images
```

### 2. Generate a Podcast Script & Audio
Synthesizes a discussion podcast WAV file from RSS feed articles.
```bash
python main.py --config app/feeds/ai_research.yaml --output "podcasts/news_{date}.wav" --output-type podcast
```

### 3. Generate a Blogcast
Outputs a Markdown article with an embedded HTML5 audio player referencing the generated WAV file.
```bash
python main.py --config app/feeds/ai_research.yaml --output "blogcasts/news_{date}.md" --output-type blogcast
```

### Command-Line Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--config` | Path to the YAML feed configuration file. | *Required* |
| `--output` | Save path (supports `{date}` placeholder). | `blog_{date}` |
| `--output-type` | Format to generate: `blog`, `podcast`, or `blogcast`. | `blog` |
| `--include-images` / `--no-include-images` | Download and embed external images locally. | `--no-include-images` |
| `--fact-check` / `--no-fact-check` | Enable the Fact-Checker agent to verify source claims. | `--no-fact-check` |

---

## 📊 Agent Tracing and Monitoring

Argos integrates with **MLflow** for transparent tracing of LLM and agent actions. To view execution logs, ensure MLflow autologging is enabled in `main.py` and run:

```bash
uv run mlflow ui
```
Then navigate to `http://localhost:5000` in your web browser.

---

## 🌐 Model Context Protocol (MCP) Server

Argos exposes its internal RSS collection, search, and discovery tools via an MCP server powered by `fastmcp`. This allows compatible AI clients (like Claude Desktop) to read and search feeds directly.

### Running the Server
```bash
# Production mode
uv run fastmcp run mcp_server.py

# Development mode (launches the MCP Inspector UI)
uv run fastmcp dev mcp_server.py
```

### Desktop Client Configuration (Claude)
Add this entry to your `claude_desktop_config.json` (adjust path as necessary):
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

### Available MCP Tools
- 📰 `read_feed(url, time_limit, include_images)`: Reads a single RSS feed.
- 📂 `read_feeds_from_config(config_path, time_limit, include_images)`: Extracts articles from a configured YAML list.
- 🔍 `get_feed_from_url(base_url)`: Discovers the RSS feed URL associated with a website.
- 🗺️ `get_feeds_from_subject(subject)`: Uses DuckDuckGo to search for relevant RSS feeds based on a topic.

---

## 📁 Project Structure

```
argos/
├── app/
│   ├── agents/            # CrewAI Agents (editor, redactor, fact-checker, etc.)
│   ├── feeds/             # YAML configurations for RSS feeds
│   ├── news_handler/      # Map-Reduce summarization orchestration
│   ├── tools/             # Feed collectors, search scrapers, RSS finders
│   ├── utils/             # TTS and audio synthesis utilities
│   └── workflows/         # NewsBlogWorkflow logic
├── main.py                # Command-Line entrypoint
├── mcp_server.py          # FastMCP server definition
├── pyproject.toml         # Packaging & project metadata
└── README.md              # Project documentation
```

