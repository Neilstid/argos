import os
from app.workflows.news_blog import NewsBlogWorkflow

def test_bundle_blog(tmp_path):
    workflow = NewsBlogWorkflow()
    # Mock result and private variables
    workflow._NewsBlogWorkflow__result = {
        "title": "Test Title",
        "summary": "Test Summary",
        "tags": ["AI", "Tech"],
        "content": "Test content with media-12345"
    }
    workflow._NewsBlogWorkflow__media_map = {
        "media-12345": "https://example.com/image.jpg"
    }
    workflow._NewsBlogWorkflow__include_images = True
    workflow._NewsBlogWorkflow__output_type = "blog"
    
    # Mock the _download_media method to not make network requests
    workflow._download_media = lambda url, output_dir, media_id: "media/media-12345.jpg"
    
    output_path = os.path.join(tmp_path, "my_bundled_post")
    
    workflow.format(output_path=output_path, bundle=True)
    
    # Verify index.md was created in output_path folder
    assert os.path.exists(os.path.join(output_path, "index.md"))
    
    with open(os.path.join(output_path, "index.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "Test Title" in content
        assert "media/media-12345.jpg" in content


def test_bundle_blogcast(tmp_path, monkeypatch):
    workflow = NewsBlogWorkflow()
    # Mock result and private variables
    workflow._NewsBlogWorkflow__result = {
        "article": {
            "title": "Test Blogcast Title",
            "summary": "Test Blogcast Summary",
            "tags": ["AI"],
            "content": "Test blogcast content"
        },
        "podcast": {
            "dialogue": []
        }
    }
    workflow._NewsBlogWorkflow__include_images = False
    workflow._NewsBlogWorkflow__output_type = "blogcast"
    
    # Mock synth_podcast to not generate real audio
    monkeypatch.setattr("app.workflows.news_blog.synth_podcast", lambda podcast, wav_path: open(wav_path, "w").close())
    
    output_path = os.path.join(tmp_path, "my_bundled_blogcast")
    
    workflow.format(output_path=output_path, bundle=True)
    
    # Verify index.md and index.wav were created in output_path folder
    assert os.path.exists(os.path.join(output_path, "index.md"))
    assert os.path.exists(os.path.join(output_path, "index.wav"))
    
    with open(os.path.join(output_path, "index.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "Test Blogcast Title" in content
        assert "index.wav" in content
