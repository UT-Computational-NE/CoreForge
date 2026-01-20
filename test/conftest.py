import os

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--num-procs", action="store", type=int, default=1)


@pytest.fixture
def num_procs(request: pytest.FixtureRequest) -> int:
    max_procs = os.cpu_count() or 1
    requested = request.config.getoption("--num-procs")
    return max(1, min(requested, max_procs))
