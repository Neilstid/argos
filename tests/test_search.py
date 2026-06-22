from app.tools.blog_finder import search_blogs_ddg


def test_duckduckgo():
    blogs_site = search_blogs_ddg("Artificial Intelligence")
    assert len(blogs_site) > 0