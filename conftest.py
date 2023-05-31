import pytest

from aipl.main import parse_args
from aipl import AIPL

@pytest.fixture()
def aipl():
    args = parse_args(['-d', '--script-or-global foo=bar'])
    r = AIPL(**vars(args))
    return r
