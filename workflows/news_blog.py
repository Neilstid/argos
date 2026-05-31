from datetime import datetime
import json
import os
from typing import Union

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


    def build(self, config_path: str):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        for source in config.get("sources", []):
            self.__feed_reader.add_source(source)

        self.__interest = config.get("interest", "")
        self.__model = config.get("model", "mistral/mistral-medium-latest")


    def add_feed(self, url: str):
        self.__feed_reader.add_source(url)


    def run(
        self,
        time_limit: Union[int, datetime] = 1,
    ):
        news = self.__feed_reader.collect(time_limit=time_limit)
        news = map_and_reduce(news, interest=self.__interest, model_name=self.__model)

        redaction_crew = build_redaction_crew(interest=self.__interest, model_name=self.__model)

        result = redaction_crew.kickoff(inputs={"topic": json.dumps(news)})

        self.__result = result.json_dict
        return result


    def format(self, output_path: str = None):
        article = self.__result
        date_str = datetime.now().strftime("%Y-%m-%d")

        formatted = f"""---
title: "{article["title"] if 'title' in article.keys() else 'AI News Blog'}"
summary: "{article["summary"] if 'summary' in article.keys() else ''}"
date: {date_str}
math: true
authors:
  - admin
tags:\n\t- {'\n\t- '.join(article["tags"])}
image:
  caption: 'Embed rich media such as videos and LaTeX math'
---

{article["content"] if 'content' in article.keys() else str(article)}

Written with [Argos](https://github.com/Neilstid/argos)"""

        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted)
        else:
            return formatted