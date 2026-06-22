import yaml
import json
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
from tools.rss_feed import BlogCollector

# Initialize FastMCP Server
mcp = FastMCP("Argos RSS Feed Reader")

@mcp.tool
def read_feed(
    url: str,
    time_limit: int = 7,
    include_images: bool = False
) -> List[Dict[str, Any]]:
    """
    Read and extract article information from a single RSS feed URL using BlogCollector.

    Args:
        url (str): The URL of the RSS feed to read.
        time_limit (int): Look back window in days (default: 7).
        include_images (bool): Whether to parse and include image/media links (default: False).

    Returns:
        List[Dict[str, Any]]: List of extracted articles with title, abstract, link, content, etc.
    """
    collector = BlogCollector()
    collector.add_source(url)
    articles = collector.collect(time_limit=time_limit, include_images=include_images)
    return articles

@mcp.tool
def read_feeds_from_config(
    config_path: str,
    time_limit: Optional[int] = None,
    include_images: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Read and extract article information from multiple RSS feeds defined in a YAML configuration file.

    Args:
        config_path (str): Path to the YAML configuration file (e.g., 'feeds/ai_research.yaml').
        time_limit (Optional[int]): Look back window in days. If not provided, uses time_limit from config or defaults to 7.
        include_images (Optional[bool]): Whether to include image/media links. If not provided, uses config value or defaults to False.

    Returns:
        List[Dict[str, Any]]: Combined list of extracted articles from all configured sources.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    collector = BlogCollector()
    sources = config.get("sources", [])
    for src in sources:
        collector.add_source(src)

    # Resolve arguments override vs config values
    resolved_time_limit = time_limit if time_limit is not None else config.get("time_limit", 7)
    resolved_include_images = include_images if include_images is not None else config.get("include_images", False)

    articles = collector.collect(time_limit=resolved_time_limit, include_images=resolved_include_images)
    return articles

if __name__ == "__main__":
    mcp.run()
