from aipl import defop

@defop('save', 0, None, 1)
def op_save(aipl, v:str, filename=''):
    'Save to given filename.'
    assert '{' not in filename, filename
    with open(filename, 'w') as fp:
        fp.write(v)

