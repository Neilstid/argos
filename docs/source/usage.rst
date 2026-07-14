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

To generate a blogcast (blog article with integrated podcast audio player):

.. code-block:: bash

    python main.py --config app/feeds/ai_research.yaml --output "blogcasts/news_{date}.md" --output-type blogcast

Command-Line Options
--------------------

- ``--config``: Path to the configuration file (e.g., ``app/feeds/ai_research.yaml``). The configuration file must be in ``.yaml`` format.
- ``--output``: The destination path where the generated blog post or podcast audio will be saved. You can use the ``{date}`` placeholder to dynamically insert the current date.
- ``--output-type``: The output format to generate: ``blog``, ``podcast``, or ``blogcast`` (default: ``blog``).
- ``--include-images`` / ``--no-include-images``: Override the configuration file parameter to either include or exclude media in the generated blog post.

Tracing and Monitoring
----------------------

Argos uses MLflow to automatically log and trace the activity of the CrewAI agents. 
When the blog generator is run, all traces are stored in a local experiment named ``argos-news-blog``.

You can view these traces by launching the MLflow UI:

.. code-block:: bash

    uv run mlflow ui

After running the command, navigate to ``http://localhost:5000`` in your web browser to monitor agent progress and history.

Automation with GitHub Actions
------------------------------

Since the application is lightweight it can run within github actions. To call argos within another github project, we need first to have it as a dependancy.

.. code-block:: bash

    git submodule add https://github.com/Neilstid/argos *path_where_you_want_it*

Then, we can run the argos script autonomously with teh command-line options inside GitHub Actions. Please find bellow an example of workflow:

.. code-block:: yaml

    # Name of the workflow
    name: Daily Blog Generator

    # Execution
    on:
    schedule:
        #        m h j M JJJ
        - cron: '0 7 * * 2-6' # Runs at 7 o'clock from tuesday to saturday included
    workflow_dispatch:

    jobs:
    build:
        runs-on: ubuntu-latest
        steps:
        - name: Checkout
            uses: actions/checkout@v6
            with:
            submodules: recursive
            token: ${{ secrets.GITHUB_TOKEN }}

        - name: "Set up Python"
            uses: actions/setup-python@v6
            with:
            python-version-file: "scripts/argos/.python-version"

        # Set up uv to install dependancies
        - name: "Install uv"
            uses: astral-sh/setup-uv@v5 # v8.1.0

        # Install argos dependancies
        - name: "Set up Python"
            working-directory: scripts/argos
            run: uv sync --locked --all-extras --dev

        # Modify here the arguments for argos base on what you desire
        - name: "run script"
            working-directory: scripts/argos
            run: uv run main.py --config app/feeds/ai_research.yaml --output-type blogcast  --output ../../content/post/daily_ai/daily_ai_{date}.md
            env:
            MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }} 

        # Commit and push the post
        - name: Commit and Push
            run: |
            git config --global user.name "github-actions[bot]"
            git config --global user.email "github-actions[bot]@users.noreply.github.com"
            git add .
            git commit -m "Auto: Nouveau post de blog du $(date +'%Y-%m-%d')" || echo "Rien à commiter"
            git push