from aipl import defop, Table, Column

# assumes header row
@defop('csv-parse', None, 1.5)
def op_csv_load(aipl, fname:str) -> dict:
    import csv
    ret = []
    with open(fname, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ret.append(row)
    return ret
