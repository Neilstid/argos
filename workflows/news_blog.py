from datetime import datetime
import json
import os
from typing import Union, Optional

import yaml
from crewai import Crew

from agents.redaction import build_redaction_crew, build_editor_crew
from news_handler.map_reduce import map_and_reduce, keep_key
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
        self.__include_images = False


    def build(self, config_path: str):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        for source in config.get("sources", []):
            self.__feed_reader.add_source(source)

        self.__interest = config.get("interest", "")
        self.__summary_model = config.get("summary_model", config.get("model", "mistral/mistral-small-latest"))
        self.__writer_model = config.get("writer_model", config.get("model", "mistral/mistral-medium-latest"))
        self.__time_limit = config.get("time_limit", 1)
        self.__include_images = config.get("include_images", False)


    def add_feed(self, url: str):
        self.__feed_reader.add_source(url)


    def run(
        self,
        time_limit: Union[int, datetime] = None,
        include_images: Optional[bool] = None,
    ):
        # Get the correct time limit
        time_limit = time_limit if not time_limit is None else self.__time_limit

        if include_images is not None:
            self.__include_images = include_images

        news = self.__feed_reader.collect(time_limit=time_limit, include_images=self.__include_images)
        # Use summary model for mapping and reducing articles
        news = map_and_reduce(news, interest=self.__interest, model_name=self.__summary_model)

        # 1. Run Editor Crew to choose articles and create plan (using summary model, abstracts only)
        editor_news = keep_key(news, ["paperId", "title", "abstract"])
        editor_crew = build_editor_crew(interest=self.__interest, model_name=self.__summary_model)
        editor_result = editor_crew.kickoff(inputs={"topic": json.dumps(editor_news)})
        
        plan_data = editor_result.pydantic
        selected_ids = getattr(plan_data, "selected_paper_ids", [])
        table_of_contents = getattr(plan_data, "table_of_contents", "")

        # 2. Filter news to only include full content for selected articles
        selected_news = []
        for item in news:
            if item.get("paperId") in selected_ids:
                selected_news.append(item)

        # Fallback if no valid selection was returned
        if not selected_news:
            selected_news = news[:3]

        # Build media map from selected articles
        self.__media_map = {}
        if self.__include_images:
            for item in selected_news:
                for m in item.get("media", []):
                    self.__media_map[m["id"]] = m["url"]

        # 3. Run Redaction Crew (using writer model and selected news with full content)
        redaction_crew = build_redaction_crew(
            interest=self.__interest,
            writer_model=self.__writer_model,
            summary_model=self.__summary_model,
            include_images=self.__include_images
        )

        result = redaction_crew.kickoff(inputs={
            "topic": json.dumps(selected_news),
            "plan": table_of_contents
        })

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
        if self.__include_images and output_path and article and "content" in article:
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

        image_frontmatter = ""
        if self.__include_images:
            image_frontmatter = """image:
  caption: 'Embed rich media such as videos and LaTeX math'\n"""

        formatted = f"""---
title: "{article["title"] if 'title' in article.keys() else 'AI News Blog'}"
summary: "{article["summary"] if 'summary' in article.keys() else ''}"
date: {date_str}
math: true
authors:
  - admin
tags:\n  - {'\n  - '.join(article["tags"])}
{image_frontmatter}---

{article["content"] if 'content' in article.keys() else str(article)}

Written with [Argos](https://github.com/Neilstid/argos)"""

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted)
        else:
            return formatted