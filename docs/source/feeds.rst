Feeds & Personalization
=======================

Argos uses YAML configuration files to define the RSS feeds it collects news from. You can specify any number of RSS feeds.

Creating a New Feed
-------------------

Create a new ``.yaml`` file inside the ``feeds/`` directory.
For example, ``feeds/my_custom_feed.yaml``:

.. code-block:: yaml

    sources:
      - "https://example.com/rss"
      - "https://another-blog.com/feed"
    interest: "Machine Learning and Artificial Intelligence"
    model: "mistral/mistral-medium-latest"
    include_images: true
    time_limit: 7

Personalizing Options
---------------------

- **interest**: Provides context to the AI agents about what kind of articles to prioritize or focus on. Make it as specific as you need.
- **include_images**: Set to ``true`` if you want the collector to extract and include images in the generated markdown.
- **time_limit**: Specify how many days back the collector should fetch articles (e.g., ``7`` for a weekly summary, ``1`` for daily).
- **model**, **summary_model**, **writer_model**: Specify the specific model IDs for the redaction agents to use.
