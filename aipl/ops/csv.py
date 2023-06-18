from aipl import defop
from typing import List

# assumes header row
@defop('csv-parse', None, 1.5)
def op_csv_parse(aipl, fname:str) -> List[dict]:
    'Converts a .csv into a table of rows.'
    import csv
    with open(fname, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yield row
