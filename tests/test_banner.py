import os
from unittest.mock import MagicMock, patch
import pytest

from app.tools.image_generator import create_banner_prompt, generate_banner_image, slugify_title
from app.workflows.news_blog import NewsBlogWorkflow


def test_slugify_title():
    assert slugify_title("Artificial Intelligence in 2026!") == "artificial_intelligence_in_2026"
    assert slugify_title("Hello & World / Test") == "hello_world_test"
    assert slugify_title("") == "article"


@patch("litellm.completion")
def test_create_banner_prompt(mock_completion):
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "A futuristic vector illustration showing AI networks."
    mock_completion.return_value = mock_resp

    article = {
        "title": "AI Breakthrough",
        "summary": "Summary of AI progress.",
        "content": "Full article content on AI breakthrough."
    }
    prompt = create_banner_prompt(article, writer_model="mistral/mistral-medium-latest")

    assert prompt == "A futuristic vector illustration showing AI networks."
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args[1]
    assert call_args["model"] == "mistral/mistral-medium-latest"
    user_msg = call_args["messages"][0]["content"]
    assert "# Role" in user_msg
    assert "designer specializing in illustration" in user_msg
    assert "AI Breakthrough" in user_msg


def test_generate_banner_image_b64():
    result_bytes = generate_banner_image("An abstract AI drawing", image_model="krea/krea-2-medium-turbo")
    assert result_bytes is not None


@patch("app.workflows.news_blog.generate_banner_image")
@patch("app.workflows.news_blog.create_banner_prompt")
def test_workflow_banner_integration(mock_create_prompt, mock_gen_image, tmp_path):
    mock_create_prompt.return_value = "An illustration of AI"
    mock_gen_image.return_value = b"PNG_FAKE_BANNER"

    workflow = NewsBlogWorkflow()
    workflow._NewsBlogWorkflow__result = {
        "title": "Quantum Computing Frontiers",
        "summary": "Exploring quantum advances.",
        "tags": ["Quantum", "Tech"],
        "content": "Detailed text about quantum computing."
    }
    workflow._NewsBlogWorkflow__writer_model = "mistral/mistral-medium-latest"
    workflow._NewsBlogWorkflow__image_model = "dall-e-3"
    workflow._NewsBlogWorkflow__output_type = "blog"

    # Trigger banner generation
    workflow._generate_banner()

    assert workflow._NewsBlogWorkflow__banner_filename == "banner_quantum_computing_frontiers.png"
    assert workflow._NewsBlogWorkflow__banner_bytes == b"PNG_FAKE_BANNER"

    output_path = os.path.join(tmp_path, "quantum_post")
    workflow.format(output_path=output_path, bundle=True)

    expected_banner_file = os.path.join(output_path, "media", "banner_quantum_computing_frontiers.png")
    assert os.path.exists(expected_banner_file)
    with open(expected_banner_file, "rb") as f:
        assert f.read() == b"PNG_FAKE_BANNER"

    index_md = os.path.join(output_path, "index.md")
    assert os.path.exists(index_md)
    with open(index_md, "r", encoding="utf-8") as f:
        md_content = f.read()
        assert "banner: media/banner_quantum_computing_frontiers.png" in md_content
        assert "filename: 'media/banner_quantum_computing_frontiers.png'" in md_content
