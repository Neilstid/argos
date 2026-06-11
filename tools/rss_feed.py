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
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from utils.date import days_ago
from utils.exceptions import SourceValidationError


class BlogCollector:
    """
    Collector for trending subjects from technical blogs.

    :ivar sources: List of RSS feed URLs configured for collection
    """

    def __init__(self):
        """Initialize the BlogCollector.

        :return: None
        :rtype: None
        """
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
        """Remove a source from the collector by index.

        :param index: Index of the source to remove
        :type index: int
        :return: None
        :rtype: None
        """
        self.sources.pop(index)


    def collect(self, time_limit: int = 7, include_images: bool = False) -> List[Dict[str, Any]]:
        """
        Collect recent articles from all configured sources.

        :param limit_per_source: Max items to consider per source, defaults to 5
        :type limit_per_source: int, optional
        :param time_limit: Number of days to look back, defaults to 7
        :type time_limit: int, optional
        :param include_images: Whether to include images from the articles
        :type include_images: bool, optional
        :return: List of article metadata dicts
        :rtype: List[Dict[str, Any]]
        """
        all_articles: List[Dict[str, Any]] = []
        limit_per_source = 5  # Default limit per source
        for source in self.sources:
            entries = self.process_feed(source, limit_per_source=limit_per_source, time_limit=time_limit, include_images=include_images)
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
        """Fetch content from an URL.

        :param url: URL to fetch
        :type url: str
        :return: Fetched content
        :rtype: Optional[str]
        """
        try:
            return extract(fetch_url(url))
        except Exception:
            return None

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=False
    )
    def fetch_content_and_media(url: str) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Fetch content and media from an URL.

        :param url: URL to fetch
        :type url: str
        :return: Tuple of content and media
        :rtype: tuple[Optional[str], List[Dict[str, Any]]]
        """
        try:
            html_content = fetch_url(url)
            if not html_content:
                return None, []
            
            content = extract(html_content)
            media = []
            seen_urls = set()
            soup = BeautifulSoup(html_content, "html.parser")
            
            def get_figure_caption(img_node) -> Optional[str]:
                curr = img_node.parent
                while curr and curr.name not in [None, '[document]', 'html', 'body']:
                    if curr.name == 'figure':
                        figcaption = curr.find("figcaption")
                        if figcaption:
                            t = figcaption.get_text().strip()
                            if t:
                                return t
                        break
                    curr = curr.parent
                return None

            def get_adjacent_p_text(img_node) -> Optional[str]:
                p_ancestor = None
                curr = img_node.parent
                while curr and curr.name not in [None, '[document]', 'html', 'body']:
                    if curr.name == 'p':
                        p_ancestor = curr
                        break
                    curr = curr.parent
                
                target = p_ancestor if p_ancestor else img_node
                
                prev_p = target.find_previous_sibling("p")
                if prev_p:
                    t = prev_p.get_text().strip()
                    if t:
                        return t[:200]
                        
                next_p = target.find_next_sibling("p")
                if next_p:
                    t = next_p.get_text().strip()
                    if t:
                        return t[:200]
                        
                return None

            def get_nearest_title(img_node) -> Optional[str]:
                pred_heading = img_node.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
                if pred_heading:
                    t = pred_heading.get_text().strip()
                    if t:
                        return t
                        
                succ_heading = img_node.find_next(["h1", "h2", "h3", "h4", "h5", "h6"])
                if succ_heading:
                    t = succ_heading.get_text().strip()
                    if t:
                        return t
                        
                if soup.title:
                    t = soup.title.get_text().strip()
                    if t:
                        return t
                return None

            for img in soup.find_all("img"):
                src = img.get("src")
                if not src:
                    continue
                
                # Resolve relative URL to absolute
                absolute_src = urljoin(url, src)
                if absolute_src in seen_urls:
                    continue
                
                # Skip layout, tracking pixels, logos, avatars, icons
                src_lower = absolute_src.lower()
                if any(term in src_lower for term in ["avatar", "logo", "icon", "spinner", "pixel", "tracker", "wp-emoji", "/ad/"]):
                    continue
                if absolute_src.startswith("data:"):
                    continue
                
                # Try figure caption first
                desc = get_figure_caption(img)
                
                # Fallback to alt/title
                if not desc:
                    alt = img.get("alt", "").strip()
                    title_attr = img.get("title", "").strip()
                    desc = alt or title_attr
                
                # Fallback to adjacent paragraph
                if not desc:
                    desc = get_adjacent_p_text(img)
                
                # Fallback to nearest title/heading
                if not desc:
                    desc = get_nearest_title(img)
                
                # If all fallback strategies failed, skip this image
                if not desc:
                    continue
                
                # Generate unique ID for this media
                media_id = f"media-{uuid4().hex[:8]}"
                
                media.append({
                    "id": media_id,
                    "url": absolute_src,
                    "description": desc
                })
                seen_urls.add(absolute_src)
                
            return content, media
        except Exception:
            return None, []

    @staticmethod
    def process_feed(feed_url: str, limit_per_source: int = -1, time_limit: Union[int, datetime] = 7, include_images: bool = False) -> List[Dict[str, Any]]:
        """
        Parse an RSS feed URL and return a list of cleaned article dicts.

        :param feed_url: RSS feed URL to parse
        :type feed_url: str
        :param limit_per_source: Maximum entries to retrieve, defaults to 5
        :type limit_per_source: int, optional
        :param time_limit: Days to look back or date limit for published articles, defaults to 7
        :type time_limit: int, optional
        :param include_images: Whether to parse and include image media
        :type include_images: bool, optional
        :return: List of article dicts
        :rtype: List[Dict[str, Any]]
        """
        try:
            feed = feedparser.parse(feed_url)
            limited_feed = []

            for i, entry in enumerate(feed.entries):
                if include_images:
                    content, media = BlogCollector.fetch_content_and_media(getattr(entry, 'link', ""))
                else:
                    content = BlogCollector.fetch_content(getattr(entry, 'link', ""))
                    media = []
                entry_safe_dict = {
                    "paperId": str(uuid4()),
                    "title": BlogCollector.remove_html(getattr(entry, 'title', "")),
                    "abstract": BlogCollector.remove_html(getattr(entry, 'description', "")),
                    "link": getattr(entry, 'link', ""),
                    "content": content,
                    "media": media,
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
