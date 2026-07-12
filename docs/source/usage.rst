Usage & Options
===============

Running the Application
-----------------------

Use the ``main.py`` script to run the blog generator. It accepts command-line arguments using ``click``.

.. code-block:: bash

To generate a blog article:

.. code-block:: bash

    python main.py --config app/feeds/ai_research.yaml --output "blog_posts/news_{date}.md" --output-type blog --include-images

To generate a podcast (audio wav + transcript):

.. code-block:: bash

    python main.py --config app/feeds/ai_research.yaml --output "podcasts/news_{date}.wav" --output-type podcast

Command-Line Options
--------------------

- ``--config``: Path to the configuration file (e.g., ``app/feeds/ai_research.yaml``). The configuration file must be in ``.yaml`` format.
- ``--output``: The destination path where the generated blog post or podcast audio will be saved. You can use the ``{date}`` placeholder to dynamically insert the current date.
- ``--output-type``: The output format to generate: ``blog`` or ``podcast`` (default: ``blog``).
- ``--include-images`` / ``--no-include-images``: Override the configuration file parameter to either include or exclude media in the generated blog post.

Tracing and Monitoring
----------------------

Argos uses MLflow to automatically log and trace the activity of the CrewAI agents. 
When the blog generator is run, all traces are stored in a local experiment named ``argos-news-blog``.

You can view these traces by launching the MLflow UI:

.. code-block:: bash

    uv run mlflow ui

After running the command, navigate to ``http://localhost:5000`` in your web browser to monitor agent progress and history.
