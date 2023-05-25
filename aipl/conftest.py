import pytest

from aipl import AIPLInterpreter

@pytest.fixture()
def aipl():
    r = AIPLInterpreter(debug=True)
    return r
