from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import FIXTURE


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE
