from app.tools.rss_finder import rss_finder


def test_rss_finder_feed():
    assert rss_finder("https://bair.berkeley.edu/blog/") == "https://bair.berkeley.edu/blog/feed"

def test_rss_finder_rss():
    assert rss_finder("https://openai.com/news") == "https://openai.com/news/rss.xml"