from __future__ import annotations

import pytest

from urbancode.errors import MissingExtraError, require_extra


def test_require_extra_message() -> None:
    with pytest.raises(MissingExtraError, match='pip install "urbancode\\[imagery\\]"'):
        require_extra("definitely_not_a_real_module_xyz", "imagery")
