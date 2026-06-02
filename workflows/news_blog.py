from datetime import datetime
import json
import os
from typing import Union, Optional

import yaml
from crewai import Crew

from agents.redaction import build_redaction_crew
from news_handler.map_reduce import map_and_reduce
from tools.rss_feed import BlogCollector


class NewsBlogWorkflow:
    """
    AI news blog generator workflow.

    Collects RSS feeds, maps/reduces articles via LLM agents, and produces
    a Markdown blog post formatted for Hugo.
    """

    def __init__(self):
        self.__feed_reader = BlogCollector()
        self.__interest = ""
        self.__result = None
        self.__media_map = {}


    def build(self, config_path: str):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        for source in config.get("sources", []):
            self.__feed_reader.add_source(source)

        self.__interest = config.get("interest", "")
        self.__model = config.get("model", "mistral/mistral-medium-latest")
        self.__time_limit = config.get("time_limit", 1)


    def add_feed(self, url: str):
        self.__feed_reader.add_source(url)


    def run(
        self,
        time_limit: Union[int, datetime] = None,
    ):
        # Get the correct time limit
        time_limit = time_limit if not time_limit is None else self.__time_limit

        news = self.__feed_reader.collect(time_limit=time_limit)
        news = map_and_reduce(news, interest=self.__interest, model_name=self.__model)

        # Build media map from selected articles
        self.__media_map = {}
        for item in news:
            for m in item.get("media", []):
                self.__media_map[m["id"]] = m["url"]

        redaction_crew = build_redaction_crew(interest=self.__interest, model_name=self.__model)

        result = redaction_crew.kickoff(inputs={"topic": json.dumps(news)})

        self.__result = result.json_dict
        return result


    def _download_media(self, url: str, output_dir: str, media_id: str) -> Optional[str]:
        import urllib.request
        import mimetypes
        import os
        from urllib.parse import urlparse

        media_dir = os.path.join(output_dir, "media")
        os.makedirs(media_dir, exist_ok=True)

        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                content_type = response.headers.get("Content-Type", "")
                ext = mimetypes.guess_extension(content_type.split(";")[0])
                if not ext:
                    parsed_url = urlparse(url)
                    ext = os.path.splitext(parsed_url.path)[1]
                if not ext:
                    ext = ".jpg"

                filename = f"{media_id}{ext}"
                dest_path = os.path.join(media_dir, filename)

                with open(dest_path, "wb") as f:
                    f.write(response.read())

                return f"media/{filename}"
        except Exception as e:
            print(f"Error downloading media from {url}: {e}")
            return None


    def format(self, output_path: str = None):
        import re
        import os

        article = self.__result

        # Post-process content to download referenced media and replace with relative paths
        if output_path and article and "content" in article:
            output_dir = os.path.dirname(output_path) or "."
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            media_ids = re.findall(r"media-[0-9a-fA-F]+", article["content"])
            media_ids = list(set(media_ids))

            for m_id in media_ids:
                if m_id in self.__media_map:
                    url = self.__media_map[m_id]
                    rel_path = self._download_media(url, output_dir, m_id)
                    if rel_path:
                        article["content"] = article["content"].replace(m_id, rel_path)
                    else:
                        article["content"] = article["content"].replace(m_id, url)

        date_str = datetime.now().strftime("%Y-%m-%d")

        formatted = f"""---
title: "{article["title"] if 'title' in article.keys() else 'AI News Blog'}"
summary: "{article["summary"] if 'summary' in article.keys() else ''}"
date: {date_str}
math: true
authors:
  - admin
tags:\n  - {'\n  - '.join(article["tags"])}
image:
  caption: 'Embed rich media such as videos and LaTeX math'
---

{article["content"] if 'content' in article.keys() else str(article)}

Written with [Argos](https://github.com/Neilstid/argos)"""

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted)
        else:
            return formatted