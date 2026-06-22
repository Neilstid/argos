from urllib.parse import urljoin

import requests
import feedparser


def rss_finder(base_url: str):
    urls = generate_rss_urls(base_url=base_url)
    for url in urls:
        if verify_rss(rss_url=url):
            return url
        
    return None


def generate_rss_urls(base_url):
    suffixes = [
        "feed", "rss", "feed.xml", "rss.xml", 
        "atom.xml", "index.xml", "?feed=rss2",
        "feeds/posts/default", "articles.xml", "blog.xml"
    ]
    
    if not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url
        
    if not base_url.endswith("/"):
        base_url += "/"
        
    urls = []
    for suffixe in suffixes:
        url_complete = urljoin(base_url, suffixe)
        urls.append(url_complete)
        
    return urls


def fast_verify_rss(rss_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(rss_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return False
        
    except requests.exceptions.RequestException as e:
        return False
    except Exception as e:
        return False
    
    return True



def verify_rss(rss_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(rss_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return False

        flux = feedparser.parse(response.content)
        if hasattr(flux.feed, "title") and isinstance(flux.entries, list):
            return True
        else:
            return False

    except requests.exceptions.RequestException as e:
        return False
    except Exception as e:
        return False
