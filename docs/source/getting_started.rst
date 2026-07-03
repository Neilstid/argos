Getting Started
===============

Installation
------------

To install Argos, clone the repository and use ``uv`` to manage the environment and install dependencies.

.. code-block:: bash

    uv sync
    # OR
    uv pip install -e .

Environment Variables
---------------------

Argos requires access to the Mistral API (or other LLMs) to process and summarize the news.
Create a ``.env`` file in the root directory:

.. code-block:: bash

    MISTRAL_API_KEY=your_mistral_api_key_here
