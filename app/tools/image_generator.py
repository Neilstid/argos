import os
import re
import urllib.request
import requests
import json
import base64

import litellm


def slugify_title(title: str) -> str:
    """Convert an article title into a clean filename slug.

    :param title: The title of the article
    :type title: str
    :return: Sanitized slug suitable for filenames
    :rtype: str
    """
    if not title:
        return "article"
    # Replace non-alphanumeric characters with underscores
    slug = re.sub(r"[^\w\-_]", "_", title.lower())
    # Collapse multiple underscores
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "article"


def create_banner_prompt(article: dict, writer_model: str = "mistral/mistral-medium-latest") -> str:
    """Generate a descriptive prompt for an article illustrative banner image using writer_model.

    :param article: Article dictionary containing title, summary, content
    :type article: dict
    :param writer_model: The LLM model to generate the prompt description
    :type writer_model: str
    :return: The generated image description prompt
    :rtype: str
    """
    title = article.get("title", "")
    summary = article.get("summary", "")
    content = article.get("content", "")

    user_prompt = f"""# Role
You are a designer specializing in illustration. You’re particularly skilled at creating a distinctive visual style to illustrate articles, books, and blogs—even on complex and vague topics. You’re especially known for your drawing style.

# Task
Based on a blog post, you will write the text describing the article’s illustrative image (**you will not create the image**). The text should accurately represent the article while incorporating your artistic touch. **Do not include any text in your illustration.**

# Article 
Title: {title}
Summary: {summary}

---

Content:
{content}
"""

    response = litellm.completion(
        model=writer_model,
        messages=[{"role": "user", "content": user_prompt}]
    )

    return response.choices[0].message.content.strip()


def generate_banner_image(prompt: str, image_model: str) -> bytes:
    """Generate an image using the specified image_model and prompt.

    :param prompt: Text prompt describing the image to generate
    :type prompt: str
    :param image_model: Name of the image model (e.g. dall-e-3, recraft, etc.)
    :type image_model: str
    :return: Image file bytes
    :rtype: bytes
    """


    response = requests.post(
        url="https://openrouter.ai/api/v1/images",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": image_model,
            "prompt": prompt
        })
    )

    result = response.json()
    data = result.get("data", [])[0]
    image_bytes = base64.b64decode(data["b64_json"])

    return image_bytes