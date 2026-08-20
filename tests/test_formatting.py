import pytest
from app.workflows.news_blog import NewsBlogWorkflow


def test_unicode_escape_decoding():
    workflow = NewsBlogWorkflow()
    raw = r"> \u2728 **TL;DR:** This week\'s 2.11\u00d7 speedup is \u22655% faster with reward \u22121."
    cleaned = workflow.rem_extra(raw)
    assert "✨ **TL;DR:**" in cleaned
    assert "2.11× speedup" in cleaned
    assert "≥5% faster" in cleaned
    assert "reward −1" in cleaned
    assert r"\u" not in cleaned


def test_escaped_quotes_and_apostrophes():
    workflow = NewsBlogWorkflow()
    raw = r"""Alibaba\'s Qwen3.8-27B is great. As Willison noted, \"The fact that a 17GB file works is a miracle.\" It doesn\'t fail."""
    cleaned = workflow.rem_extra(raw)
    assert "Alibaba's Qwen3.8-27B is great." in cleaned
    assert 'As Willison noted, "The fact that a 17GB file works is a miracle."' in cleaned
    assert "It doesn't fail." in cleaned
    assert r"\'" not in cleaned
    assert r'\"' not in cleaned


def test_escaped_markdown_formatting():
    workflow = NewsBlogWorkflow()
    raw = r"""This is \*italic\* and this is \*\*bold\*\* and \_\_underline\_\_ and \| table \| and \# Heading"""
    cleaned = workflow.rem_extra(raw)
    assert "*italic*" in cleaned
    assert "**bold**" in cleaned
    assert "__underline__" in cleaned
    assert "| table |" in cleaned
    assert "# Heading" in cleaned
    assert r"\*" not in cleaned
    assert r"\_" not in cleaned
    assert r"\|" not in cleaned


def test_latex_math_preservation():
    workflow = NewsBlogWorkflow()
    raw = r"""Here is inline math: $O(N \log N)$ and $\theta \times \tau$ and $\nabla L(\theta)$ and $\left[ \frac{\alpha}{\beta} \right]$
and display math:
$$
\begin{aligned}
a &= b \\
c &= d
\end{aligned}
$$
"""
    cleaned = workflow.rem_extra(raw)
    assert r"$O(N \log N)$" in cleaned
    assert r"$\theta \times \tau$" in cleaned
    assert r"$\nabla L(\theta)$" in cleaned
    assert r"$\left[ \frac{\alpha}{\beta} \right]$" in cleaned
    assert r"\begin{aligned}" in cleaned
    assert r"\end{aligned}" in cleaned
    assert "a &= b \\\\" in cleaned or "a &= b \\" in cleaned


def test_tldr_quote_cleanup():
    workflow = NewsBlogWorkflow()
    # Case 1: summary wrapped in quotes
    c1 = workflow.rem_extra(r'> 💡 **TL;DR:** "This is a summary of the article."')
    assert c1.strip() == "> 💡 **TL;DR:** This is a summary of the article."

    # Case 2: quote before emoji and at end
    c2 = workflow.rem_extra(r'> "💡 **TL;DR:** This is a summary of the article."')
    assert c2.strip() == "> 💡 **TL;DR:** This is a summary of the article."

    # Case 3: whole line wrapped in quotes
    c3 = workflow.rem_extra(r'"> 💡 **TL;DR:** This is a summary of the article."')
    assert c3.strip() == "> 💡 **TL;DR:** This is a summary of the article."

    # Case 4: unicode escape in TL;DR
    c4 = workflow.rem_extra(r'> \u2728 **TL;DR:** "This is a summary."')
    assert c4.strip() == "> ✨ **TL;DR:** This is a summary."


def test_code_block_preservation():
    workflow = NewsBlogWorkflow()
    raw = """Here is code:
```python
def test_func():
    print("Hello world")
    return True
```
"""
    cleaned = workflow.rem_extra(raw)
    assert '```python\ndef test_func():\n    print("Hello world")\n    return True\n```' in cleaned


def test_format_frontmatter():
    workflow = NewsBlogWorkflow()
    workflow._NewsBlogWorkflow__result = {
        "title": r"The AI Revolution: Qwen3.8-27B & \"New Agents\"",
        "summary": r"Alibaba\'s model and 2.11\u00d7 speedup.",
        "tags": ["AI", "Tech"],
        "content": r"> \u2728 **TL;DR:** \"This week\'s AI landscape is moving fast.\""
    }
    workflow._NewsBlogWorkflow__output_type = "blog"

    formatted = workflow.format()
    assert 'title: "The AI Revolution: Qwen3.8-27B & \\"New Agents\\""' in formatted
    assert "summary: \"Alibaba's model and 2.11× speedup.\"" in formatted
    assert "> ✨ **TL;DR:** This week's AI landscape is moving fast." in formatted
    assert r"\u2728" not in formatted
    assert r"\'" not in formatted


def test_user_example_cleanup():
    workflow = NewsBlogWorkflow()
    user_snippet = r"""
> \u2728 **TL;DR:** This week\'s AI landscape witnesses a seismic shift: Alibaba\'s Qwen3.8-27B delivers frontier-class multimodal capabilities in a locally deployable 27B-parameter model, ByteDance\'s CUDA Agent uses agentic RL to outperform compilers in GPU kernel generation, Cursor\'s Origin platform reimagines code hosting for an AI-native workflow, and loop engineering emerges as the critical discipline for robust RAG systems. Together, these innovations democratize access to cutting-edge AI, redefine performance optimization, and address the scalability challenges of agent-driven development.

| Metric / Innovation Area | Insight / Takeaway |
|-------------------------|---------------------|
| **Qwen3.8-27B Model** | 27B parameters, 262K token context, native image/video understanding; 4-bit quantization enables 17GB local deployment; benchmarks rival proprietary models like GPT-5.6 Luna and Claude Opus 4.8. |
| **CUDA Agent Performance** | 98.8% pass rate, 96.8% faster-than-torch.compile on KernelBench; 2.11\u00d7 geomean speedup; discrete milestone rewards outperform raw speedup ratios by 36.4%. |
| **Cursor Origin Adoption** | AI-native code hosting with integrated PR reviews and agent-driven changes; syncs with GitHub as source of truth; 35% of Cursor\'s merged PRs are agent-generated. |
| **Loop Engineering for RAG** | Introduces trigger, termination, and recovery as control surfaces; small loops (per-brick) and big loops (cross-brick) prevent spinning and ensure robustness. |
"""
    cleaned = workflow.rem_extra(user_snippet)
    assert "> ✨ **TL;DR:** This week's AI landscape" in cleaned
    assert "Alibaba's" in cleaned
    assert "ByteDance's" in cleaned
    assert "Cursor's" in cleaned
    assert "2.11× geomean speedup" in cleaned
    assert r"\u" not in cleaned
    assert r"\'" not in cleaned
    assert r'\"' not in cleaned
