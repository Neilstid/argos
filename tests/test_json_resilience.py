import pytest
from app.agents.models.article import Article
from app.agents.models.plan import BlogPlan
from app.agents.models.podcast import PodcastScript
from app.workflows.news_blog import NewsBlogWorkflow


def test_user_exact_payload_validation():
    r"""Test that Article model parses the user's exact LLM output containing unescaped bash line continuations."""
    user_payload = r'''{"title": "AI’s Next Frontier: Stripe’s OpenRouter Acquisition, Slack’s Multiplayer Coding, and Liquid AI’s 3.2x Faster LLM Inference", "summary": "This article explores three pivotal developments in AI: Stripe’s $8B acquisition of OpenRouter to revolutionize model routing and token-based billing, Slack Code’s introduction of collaborative AI coding agents in group chats, and Liquid AI’s LFM2.5-DSpark speculative decoding, which accelerates LLM inference by up to 3.2x without altering outputs. Each innovation addresses critical bottlenecks—cost, collaboration, and speed—reshaping how developers and enterprises interact with AI.", "tags": ["Artificial Intelligence", "LLMs", "AI Model Routing", "Collaborative Coding", "Speculative Decoding", "Stripe", "OpenRouter", "Slack Code", "Liquid AI", "LFM2.5-DSpark", "AI Agents", "Token Billing", "Enterprise AI"], "content": "> 💡 **TL;DR:** Stripe’s $8B acquisition of OpenRouter supercharges AI model routing and token-based billing for developers, while Slack Code brings AI coding agents into collaborative group chats to democratize software development. Meanwhile, Liquid AI’s LFM2.5-DSpark delivers up to 3.2x faster LLM inference via speculative decoding—without changing outputs—addressing speed, cost, and teamwork in AI workflows.\n\n| Metric / Innovation Area | Insight / Takeaway |\n|---|---|\n| **Stripe + OpenRouter** | $8B acquisition unifies model routing (400+ models, 80+ providers) with token-based billing, enabling dynamic cost/performance optimization. |\n| **Slack Code** | Embeds AI agents (Claude Code, Devin, GitHub Copilot) into group chats, turning coding into a \"multiplayer\" workflow with auditable trails. |\n| **Liquid AI LFM2.5-DSpark** | ~300M-parameter drafters achieve 3.2x faster decoding (H100) via speculative decoding, with identical greedy outputs. |\n\n---\n\n### Stripe’s $8B Bet: OpenRouter and the Future of AI Model Routing\n\n```bash\npython -m sglang.launch_server \ \n--model-path LiquidAI/LFM2.5-2.6B \ \n--speculative-algorithm DSPARK \ \n--speculative-draft-model-path LiquidAI/LFM2.5-2.6B-DSpark \ \n--speculative-draft-attention-backend flashinfer \ \n--disable-radix-cache --mem-fraction-static 0.75 --port 30000\n```\n\n**Key takeaways**:"}'''

    article = Article.model_validate_json(user_payload)
    assert article.title.startswith("AI’s Next Frontier")
    assert "OpenRouter" in article.summary
    assert len(article.tags) == 13
    assert "sglang.launch_server" in article.content


def test_latex_math_unescaped_backslashes():
    r"""Test that LaTeX equations with unescaped backslashes (\sigma, \log) are preserved and validated."""
    payload = r'''{"title": "Deep Learning Optimization", "summary": "Mathematical foundations", "tags": ["AI", "Math"], "content": "The loss function is $\sigma(W^T x + b)$ and gradient $\nabla L(\theta)$ with learning rate $\alpha \in (0, 1)$."}'''

    article = Article.model_validate_json(payload)
    assert article.title == "Deep Learning Optimization"
    assert r"\sigma" in article.content
    assert r"\nabla" in article.content
    assert r"\alpha" in article.content


def test_markdown_escaped_symbols():
    """Test that markdown symbols escaped with single backslashes in JSON parse properly."""
    payload = r'''{"title": "Markdown Escapes", "summary": "Summary", "tags": ["Tech"], "content": "Column \| Value and \*bold\* item \_italic\_"}'''

    article = Article.model_validate_json(payload)
    assert article.title == "Markdown Escapes"
    assert "Column" in article.content


def test_raw_unescaped_newlines_in_json():
    """Test that JSON strings with literal unescaped newlines parse successfully."""
    payload = '{"title": "Multiline Blog", "summary": "Summary", "tags": ["AI"], "content": "Line 1\nLine 2\nLine 3"}'

    article = Article.model_validate_json(payload)
    assert article.title == "Multiline Blog"
    assert "Line 1" in article.content
    assert "Line 3" in article.content


def test_single_quoted_json():
    """Test that single-quoted JSON strings from LLMs are repaired and parsed."""
    payload = "{'title': 'Single Quote Title', 'summary': 'Single Quote Summary', 'tags': ['AI'], 'content': 'Content here'}"

    article = Article.model_validate_json(payload)
    assert article.title == "Single Quote Title"
    assert article.summary == "Single Quote Summary"


def test_blog_plan_resilience():
    """Test that BlogPlan handles malformed escape sequences."""
    payload = r'''{"selected_paper_ids": ["id-1", "id-2"], "table_of_contents": "### Section 1: Intro \ \n### Section 2: Math $\log(x)$"}'''

    plan = BlogPlan.model_validate_json(payload)
    assert plan.selected_paper_ids == ["id-1", "id-2"]
    assert "Section 1" in plan.table_of_contents


def test_podcast_script_resilience():
    """Test that PodcastScript handles dialogue with unescaped escapes."""
    payload = r'''{"title": "Podcast Episode 1", "turns": [{"speaker": "Paul", "text": "Welcome to the show! Let\'s talk about $O(N \log N)$ algorithms."}, {"speaker": "Anna", "text": "Thanks Paul! It\'s great to be here."}]}'''

    podcast = PodcastScript.model_validate_json(payload)
    assert podcast.title == "Podcast Episode 1"
    assert len(podcast.turns) == 2
    assert podcast.turns[0].speaker == "Paul"


def test_workflow_extract_task_data():
    """Test NewsBlogWorkflow._extract_task_data fallback parsing on dirty JSON."""
    raw_article_json = r'''{"title": "Workflow Test", "summary": "Testing _extract_task_data", "tags": ["Test"], "content": "Bash cmd:\n```bash\nlaunch \ \n--flag\n```"}'''

    extracted = NewsBlogWorkflow._extract_task_data(raw_article_json, Article)
    assert extracted is not None
    assert extracted["title"] == "Workflow Test"
    assert "launch" in extracted["content"]
