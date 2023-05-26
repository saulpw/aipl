from io import StringIO
from glob import glob
import pytest
from aipl.interpreter import AIPL

@pytest.mark.parametrize("input_file", glob("tests/*.aipl"))
def test_script(input_file):
    aipl = AIPL(debug=False)
    aipl.stdout = StringIO()

    with open(input_file) as fh:
        aipl.run(fh.read(), '')
