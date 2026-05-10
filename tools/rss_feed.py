"""
Blog collectors for scraping technical blog RSS feeds.

Provides `BlogCollector` to collect recent articles from configured RSS
sources and a `trending_blog_tool` wrapper for use by agent tools.
"""

from datetime import datetime

import feedparser
from trafilatura import fetch_url, extract
import re
from dateutil.parser import ParserError, parser
from uuid import uuid4
from typing import List, Dict, Any, Optional, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from urllib.parse import urlparse

from utils.date import days_ago
from utils.exceptions import SourceValidationError


class BlogCollector:
    """
    Collector for trending subjects from technical blogs.

    :ivar sources: List of RSS feed URLs configured for collection
    """

    def __init__(self):
        super().__init__()
        self.sources = []

    def add_source(self, source: str):
        """
        Add an RSS feed URL as a source.

        :param source: RSS feed URL
        :type source: str
        :raises SourceValidationError: If the source is not a valid URL.
        """
        if not source or not isinstance(source, str):
            raise SourceValidationError("Source must be a non-empty string")

        try:
            parsed = urlparse(source)
            if not parsed.scheme or not parsed.netloc:
                raise SourceValidationError("Source must be a valid URL")
        except Exception:
            raise SourceValidationError("Source must be a valid URL")

        self.sources.append(source)

    def remove_source(self, index: int):
        self.sources.pop(index)


    def collect(self, time_limit: int = 7) -> List[Dict[str, Any]]:
        """
        Collect recent articles from all configured sources.

        :param limit_per_source: Max items to consider per source, defaults to 5
        :type limit_per_source: int, optional
        :param time_limit: Number of days to look back, defaults to 7
        :type time_limit: int, optional
        :return: List of article metadata dicts
        :rtype: List[Dict[str, Any]]
        """
        all_articles: List[Dict[str, Any]] = []
        limit_per_source = 5  # Default limit per source
        for source in self.sources:
            entries = self.process_feed(source, limit_per_source=limit_per_source, time_limit=time_limit)
            all_articles.extend(entries)

        return all_articles


    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=False
    )
    def fetch_content(url: str) -> Optional[str]:
        try:
            return extract(fetch_url(url))
        except Exception:
            return None

    @staticmethod
    def process_feed(feed_url: str, limit_per_source: int = -1, time_limit: Union[int, datetime] = 7) -> List[Dict[str, Any]]:
        """
        Parse an RSS feed URL and return a list of cleaned article dicts.

        :param feed_url: RSS feed URL to parse
        :type feed_url: str
        :param limit_per_source: Maximum entries to retrieve, defaults to 5
        :type limit_per_source: int, optional
        :param time_limit: Days to look back or date limit for published articles, defaults to 7
        :type time_limit: int, optional
        :return: List of article dicts
        :rtype: List[Dict[str, Any]]
        """
        try:
            feed = feedparser.parse(feed_url)
            limited_feed = []

            for i, entry in enumerate(feed.entries):
                entry_safe_dict = {
                    "paperId": str(uuid4()),
                    "title": BlogCollector.remove_html(getattr(entry, 'title', "")),
                    "abstract": BlogCollector.remove_html(getattr(entry, 'description', "")),
                    "link": getattr(entry, 'link', ""),
                    "content": BlogCollector.fetch_content(getattr(entry, 'link', "")),
                    "timestamp": BlogCollector.get_published_date(entry),
                    "publishedDate": BlogCollector.get_published_date(entry, format='%Y-%m-%dT%H:%M:%SZ'),
                    "source": getattr(feed.feed, 'title', None) if hasattr(feed, 'feed') else None,
                    "language": getattr(feed.feed, 'language', None) if hasattr(feed, 'feed') else None,
                    "authors": getattr(feed.feed, 'author', None) if hasattr(feed, 'feed') else None,
                    "type": "url"
                }

                # Verify the validity of the entry
                if BlogCollector.verify_entry(
                    entry=entry_safe_dict, n_entry=i, limit_per_source=limit_per_source, time_limit=time_limit
                ):
                    break

                # If the break condition is not raised then add the entry
                limited_feed.append(entry_safe_dict)
                
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            return []
        
        return limited_feed


    @staticmethod
    def verify_entry(entry: Dict[str, Any], n_entry: int, limit_per_source: int, time_limit: Union[int, datetime]) -> bool:
        """
        Determine if the feed parsing should stop based on limits or age.

        :return: True if processing should stop for this feed
        :rtype: bool
        """
        condition_num = not entry["timestamp"] and n_entry > -1 and n_entry > limit_per_source

        if isinstance(time_limit, datetime):
            condition_time = entry["timestamp"] and entry["timestamp"] < time_limit
        else:
            # If number of date
            condition_time = entry["timestamp"] and entry["timestamp"] < days_ago(time_limit)

        return condition_num or condition_time

    @staticmethod
    def remove_html(html_str: str) -> str:
        """Strip HTML tags and collapse whitespace from `html_str`."""
        return re.sub(" +", " ", re.sub(r"<[^>]*>", "", html_str))


    @staticmethod
    def get_published_date(entry: dict, format: str = None) -> Optional[Union[int, str]]:
        """
        Extract a published date from a feed entry.

        :param entry: Feed entry mapping
        :type entry: dict
        :param format: Optional strftime format to return, defaults to None
        :type format: str, optional
        :return: Unix timestamp (int) or formatted string, or None
        :rtype: Optional[Union[int, str]]
        """
        keys = ["published", "pubDate"]
        parsed_date = None

        for key in keys:
            date_entry = entry.get(key, None)
            if date_entry:
                try:
                    parsed_date = parser().parse(date_entry)

                    if format:
                        parsed_date = parsed_date.strftime(format)
                    else:
                        parsed_date = parsed_date.timestamp()

                    break
                except ParserError:
                    continue

        return parsed_date
