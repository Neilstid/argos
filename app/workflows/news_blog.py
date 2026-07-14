from datetime import datetime
import json
import re
import os
from typing import Union, Optional

import yaml

from app.agents.models.article import Article
from app.agents.models.podcast import PodcastScript
from app.agents.redaction import build_redaction_crew, build_editor_crew
from app.agents.podcast import build_podcast_crew
from app.news_handler.map_reduce import map_and_reduce, keep_key
from app.tools.rss_feed import BlogCollector
from app.utils.podcast import synth_podcast


class NewsBlogWorkflow:
    """
    AI news blog generator workflow.

    Collects RSS feeds, maps/reduces articles via LLM agents, and produces
    a Markdown blog post formatted for Hugo.
    """

    def __init__(self):
        """Initialize the NewsBlogWorkflow.

        :return: None
        :rtype: None
        """
        self.__feed_reader = BlogCollector()
        self.__interest = ""
        self.__result: Union[Article, PodcastScript] = None
        self.__media_map = {}
        self.__include_images = False
        self.__output_type = "blog"


    def build(self, config_path: str):
        """Build the workflow configuration from a file.

        :param config_path: Path to the configuration yaml file
        :type config_path: str
        :return: None
        :rtype: None
        """
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
        """Add a feed to the workflow.

        :param url: URL of the feed
        :type url: str
        :return: None
        :rtype: None
        """
        self.__feed_reader.add_source(url)


    def run(
        self,
        time_limit: Union[int, datetime] = None,
        include_images: Optional[bool] = None,
        fact_check: Optional[bool] = None,
        output_type: str = "blog",
    ) -> Union[Article, PodcastScript]:
        """Run the workflow to collect, map and reduce articles.

        :param time_limit: Time limit for fetching articles, defaults to None
        :type time_limit: Union[int, datetime], optional
        :param include_images: Whether to include images in the output, defaults to None
        :type include_images: Optional[bool], optional
        :param fact_check: Whether to fact check information, defaults to None
        :type fact_check: Optional[bool], optional
        :param output_type: The output format (blog or podcast)
        :type output_type: str
        :return: The generated blog post or podcast script result
        :rtype: Any
        """
        self.__output_type = output_type

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
        
        plan_data = editor_result.json_dict
        selected_ids = plan_data.get("selected_paper_ids", [])
        table_of_contents = plan_data.get("table_of_contents", "")

        # 2. Filter news to only include full content for selected articles
        selected_news = []
        for item in news:
            if item.get("paperId") in selected_ids:
                selected_news.append(item)

        # Fallback if no valid selection was returned
        if not selected_news:
            selected_news = news[:3]

        if output_type == "podcast":
            # Run Podcast Crew (using writer and summary models)
            podcast_crew = build_podcast_crew(
                interest=self.__interest,
                writer_model=self.__writer_model,
                summary_model=self.__summary_model,
            )
            result = podcast_crew.kickoff(inputs={
                "topic": json.dumps(selected_news),
                "plan": table_of_contents
            })
            if result.pydantic:
                self.__result = result.pydantic.model_dump()
            elif result.json_dict:
                self.__result = result.json_dict
            else:
                try:
                    self.__result = json.loads(result.raw)
                except Exception:
                    self.__result = None
            return result

        if output_type == "blogcast":
            # Build media map first for the article
            self.__media_map = {}
            if self.__include_images:
                for item in selected_news:
                    for m in item.get("media", []):
                        self.__media_map[m["id"]] = m["url"]

            # 1. Run Redaction Crew to write the blog post
            redaction_crew = build_redaction_crew(
                interest=self.__interest,
                writer_model=self.__writer_model,
                summary_model=self.__summary_model,
                include_images=self.__include_images,
                fact_check=fact_check
            )
            article_result = redaction_crew.kickoff(inputs={
                "topic": json.dumps(selected_news),
                "plan": table_of_contents
            })

            article_data = None
            if article_result.pydantic:
                article_data = article_result.pydantic.model_dump()
            elif article_result.json_dict:
                article_data = article_result.json_dict
            else:
                try:
                    article_data = json.loads(article_result.raw)
                except Exception:
                    article_data = None

            # 2. Run Podcast Crew to write the dialogue script
            podcast_crew = build_podcast_crew(
                interest=self.__interest,
                writer_model=self.__writer_model,
                summary_model=self.__summary_model,
            )
            podcast_result = podcast_crew.kickoff(inputs={
                "topic": json.dumps(selected_news),
                "plan": table_of_contents
            })

            podcast_data = None
            if podcast_result.pydantic:
                podcast_data = podcast_result.pydantic.model_dump()
            elif podcast_result.json_dict:
                podcast_data = podcast_result.json_dict
            else:
                try:
                    podcast_data = json.loads(podcast_result.raw)
                except Exception:
                    podcast_data = None

            self.__result = {
                "article": article_data,
                "podcast": podcast_data
            }
            return article_result

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
            include_images=self.__include_images,
            fact_check=fact_check
        )

        result = redaction_crew.kickoff(inputs={
            "topic": json.dumps(selected_news),
            "plan": table_of_contents
        })

        if result.pydantic:
            self.__result = result.pydantic.model_dump()
        elif result.json_dict:
            self.__result = result.json_dict
        else:
            try:
                self.__result = json.loads(result.raw)
            except Exception:
                self.__result = None
        return result


    def _download_media(self, url: str, output_dir: str, media_id: str) -> Optional[str]:
        """Download media from an URL.

        :param url: Media URL
        :type url: str
        :param output_dir: Directory to save the media
        :type output_dir: str
        :param media_id: Unique identifier for the media
        :type media_id: str
        :return: Path to the downloaded media or None
        :rtype: Optional[str]
        """
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


    def rem_extra(self, article):
        article = re.sub(r"\\+", r"\\", article)

        return article


    def format(
        self, 
        output_path: str = None,
        image_folder: Optional[str] = "",
    ):
        """Format the generated result as a Markdown string and save it.

        :param output_path: Path to save the Markdown file, defaults to None
        :type output_path: str, optional
        :return: Formatted Markdown string if output_path is None, else None
        :rtype: Union[str, None]
        """

        # Init variable
        base_path, _ = os.path.splitext(output_path)
        audio_player = ""
        wav_path = ""
        md_path = ""
        image_frontmatter = ""
        article = None
        podcast = None

        match self.__output_type:
            case "blogcast":
                include_audio = True
                include_markdown = True

                wav_path = base_path + ".wav"
                md_path = base_path + ".md"
                audio_player = f"> 🎙️ **Listen to the podcast version of this article:**\n> <audio controls src=\"{os.path.basename(wav_path)}\"></audio>\n\n"

                article = self.__result.get("article") if self.__result else None
                podcast: PodcastScript = self.__result.get("podcast") if self.__result else None
            case "podcast":
                include_audio = True
                include_markdown = False

                wav_path = base_path + ".wav"

                podcast: PodcastScript = self.__result
            case "blog":
                include_audio = False
                include_markdown = True

                md_path = base_path + ".md"

                article = self.__result
            case _:
                raise ValueError(f"Unknown output value: self.__output_type. Expected one of the following: blogcast, podcast, blog")

        if include_audio:
            synth_podcast(podcast=podcast, wav_path=wav_path)
        
        if include_markdown:
            # Post-process content to download referenced media and replace with relative paths
            if self.__include_images and output_path and article and article["content"]:
                output_dir = image_folder or os.path.dirname(output_path) or "."
                dir_name = os.path.splitext(os.path.basename(output_path))[0]

                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)

                media_ids = re.findall(r"media-[0-9a-fA-F]+", article["content"])
                media_ids = list(set(media_ids))

                for m_id in media_ids:
                    if m_id in self.__media_map:
                        url = self.__media_map[m_id]
                        all_path = self._download_media(url, os.path.join(output_dir, dir_name), m_id)
                        rel_path = os.path.join(dir_name, os.path.basename(all_path))

                        if rel_path:
                            article["content"] = article["content"].replace(m_id, rel_path)
                        else:
                            article["content"] = article["content"].replace(m_id, url)

                image_frontmatter = "image:\ncaption: 'Embed rich media such as videos and LaTeX math'\n"

            date_str = datetime.now().strftime("%Y-%m-%d")

            formatted = f"""---
title: "{article["title"] if article["title"] else 'AI News Blog'}"
summary: "{article["summary"] if article["summary"] else ''}"
date: {date_str}
math: true
authors:
    - admin
tags:\n  - {'\n  - '.join(article["tags"])}
{image_frontmatter}
---

{audio_player}

---

{self.rem_extra(article["content"]) if article["content"] else str(article)}

Written with [Argos](https://github.com/Neilstid/argos)
"""

            # Save the result
            if md_path:
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(formatted)
            else:
                return formatted
            
        else:
            # Case of podcast
            return wav_path