Model Context Protocol (MCP) Server
===================================

Argos includes a Model Context Protocol (MCP) server that exposes its RSS feed collection and search tools to MCP-compatible AI clients (such as Claude Desktop, Cursor, Windsurf, or custom AI agents). 

This allows your AI assistant to search for, discover, read, and extract content from RSS feeds directly using Argos's robust underlying tools.

Exposed Tools
-------------

The Argos MCP server (defined in `mcp_server.py`) exposes the following tools:

1. ``read_feed``
~~~~~~~~~~~~~~~~

Read and extract article information from a single RSS feed URL.

* **Arguments:**
  * ``url`` (str): The URL of the RSS feed to read.
  * ``time_limit`` (int, optional): Look back window in days (default: ``7``).
  * ``include_images`` (bool, optional): Whether to parse and include image/media links (default: ``False``).
* **Returns:** A list of dictionaries, where each dictionary contains article details (title, author, date, link, summary, content, etc.).

2. ``read_feeds_from_config``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read and extract article information from multiple RSS feeds defined in a YAML configuration file.

* **Arguments:**
  * ``config_path`` (str): Path to the YAML configuration file (e.g., ``feeds/ai_research.yaml``).
  * ``time_limit`` (int, optional): Look back window in days. If not provided, uses the config value or defaults to ``7``.
  * ``include_images`` (bool, optional): Whether to include image/media links. If not provided, uses the config value or defaults to ``False``.
* **Returns:** Combined list of extracted articles from all sources listed in the configuration file.

3. ``get_feed_from_url``
~~~~~~~~~~~~~~~~~~~~~~~~

Find the RSS feed URL for a given website URL.

* **Arguments:**
  * ``base_url`` (str): Base URL of the website to find the RSS feed for.
* **Returns:** The URL of the RSS feed if found, or an empty/null value.

4. ``get_feeds_from_subject``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find RSS feeds for a given subject/topic by searching blogs using DuckDuckGo and resolving their feeds.

* **Arguments:**
  * ``subject`` (str): The subject or topic to search feeds for.
* **Returns:** A list of RSS feed URLs matching the subject.

Running the MCP Server
----------------------

You can run the MCP server using ``fastmcp`` or directly via Python.

Using FastMCP CLI (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the server using ``fastmcp`` from your environment:

.. code-block:: bash

    uv run fastmcp run mcp_server.py

To run the server in development mode with the interactive **MCP Inspector** web UI (which lets you test the tools in a browser):

.. code-block:: bash

    uv run fastmcp dev mcp_server.py

Running directly with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternatively, you can run the server directly:

.. code-block:: bash

    uv run python mcp_server.py

Integration with Clients
------------------------

To connect the Argos MCP server to your AI clients, use the configuration templates below.

Claude Desktop
~~~~~~~~~~~~~~

Add the following to your Claude Desktop configuration file (typically located at ``%APPDATA%\Claude\claude_desktop_config.json`` on Windows or ``~/Library/Application Support/Claude/claude_desktop_config.json`` on macOS/Linux):

.. code-block:: json

    {
      "mcpServers": {
        "argos": {
          "command": "uv",
          "args": [
            "--directory",
            "./argos",
            "run",
            "fastmcp",
            "run",
            "mcp_server.py"
          ]
        }
      }
    }

.. note::
   Make sure to replace the directory path with the actual absolute path to your Argos workspace directory.

Cursor / Windsurf / Other Editors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure a new command-based MCP server in your editor's settings:

* **Name:** ``argos``
* **Type:** ``command``
* **Command:**

  .. code-block:: bash

      uv --directory "C:/Users/Neil Farmer/Documents/GitHub/argos" run fastmcp run mcp_server.py
