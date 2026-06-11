Usage & Options
===============

Running the Application
-----------------------

Use the ``main.py`` script to run the blog generator. It accepts command-line arguments using ``click``.

.. code-block:: bash

    python main.py --config feeds/ai_research.yaml --output "blog_posts/news_{date}.md" --include-images

Command-Line Options
--------------------

- ``--config``: Path to the configuration file (e.g., ``feeds/ai_research.yaml``). The configuration file must be in ``.yaml`` format.
- ``--output``: The destination path where the generated blog post will be saved. You can use the ``{date}`` placeholder to dynamically insert the current date. Output must be a ``.md`` file.
- ``--include-images`` / ``--no-include-images``: Override the configuration file parameter to either include or exclude media in the generated blog post.
