import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--live-feeds",
        action="store_true",
        default=False,
        help="Run agent evaluations using live RSS feed fetches instead of mock fixtures."
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "eval: mark test as an agent evaluation using LLM-as-a-judge")

@pytest.fixture
def use_live_feeds(request):
    return request.config.getoption("--live-feeds")
