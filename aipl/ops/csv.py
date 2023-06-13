from aipl import defop
from typing import List

# assumes header row
@defop('csv-parse', None, 1.5)
def op_csv_load(aipl, fname:str) -> List[dict]:
    import csv
    with open(fname, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yield row
