# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
base_dir = os.path.abspath('../../app/')
sys.path.insert(0, os.path.abspath('../../'))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'agents'))
sys.path.insert(0, os.path.join(base_dir, 'news_handler'))
sys.path.insert(0, os.path.join(base_dir, 'tools'))
sys.path.insert(0, os.path.join(base_dir, 'utils'))
sys.path.insert(0, os.path.join(base_dir, 'workflows'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Argos'
copyright = '2026, Neil FARMER'
author = 'Neil FARMER'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    # 'sphinx_markdown_builder',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
