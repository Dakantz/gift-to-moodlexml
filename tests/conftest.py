from pathlib import Path

import pytest

import gift_to_moodlexml as g

EXAMPLES = Path(__file__).parent / "examples.gift"


@pytest.fixture
def items():
    return g.load_gift_files([EXAMPLES])
