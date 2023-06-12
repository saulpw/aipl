from io import StringIO
from glob import glob
import pytest
from aipl.interpreter import AIPL

@pytest.mark.parametrize("input_file", glob("tests/*.aipl"))
def test_script(aipl, input_file):
    aipl.stdout = StringIO()
    aipl.options.test = True

    with open(input_file) as fh:
        aipl.run_test(fh.read(), '')
