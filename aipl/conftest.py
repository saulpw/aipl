import pytest

from aipl import AIPL

@pytest.fixture()
def aipl():
    r = AIPL(debug=True)
    return r
