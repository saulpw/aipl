'''
Provides !json which converts Table into json blob,
and !json_parse which converts json blob into row.
'''

import json

from aipl import defop, Table, Column


class _jsonEncoder(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


@defop('json', 100, 0)
def op_json(aipl, t:Table, indent:int = None) -> str:
    'Convert Table into a json blob.'
    jsonenc = _jsonEncoder(indent=indent)
    return jsonenc.encode(t._asdict())


def _json_find(v:dict|list|int|float|str, args):
    if not args:
        yield v
    elif isinstance(v, (str, int, float)):
        yield v
    elif isinstance(v, (list, tuple)):
        for item in v:
            yield from _json_find(item, args)
    elif isinstance(v, dict):
        for k, item in v.items():
            if args and k != args[0]:
                continue
            yield from _json_find(item, args[1:])
    else:
        raise 'error'


class FlatteningDict(dict):
    def __init__(self, d:dict):
        for k, v in d.items():
            self[k] = v

    def __setitem__(self, k, v):
        if isinstance(v, dict):
            for newk, newv in v.items():
                self[k+'_'+newk] = newv  # should recurse
        else:
            super().__setitem__(k, v)

def test_flattening_dict():
    r = FlatteningDict(dict(a=dict(b=1, c=2), d=4, e=dict(f=dict(g=5))))
    assert r == dict(a_b=1, a_c=2, d=4, e_f_g=5)

def pyobj_to_table(r, key:str='value') -> Table|dict|int|float|str:
    '''Convert a parsed json object into a Table (for lists), a dict (for objects), or a scalar.
       Non-object items in a list become rows with a single column named *key*.'''
    if r is None:
        return None
    elif isinstance(r, (list, tuple)):
        keys = set()
        ret = Table()
        for inobj in r:
            outobj = pyobj_to_table(inobj, key)
            if not isinstance(outobj, dict):
                outobj = {key: outobj}
            ret.rows.append(outobj)
            keys |= set(outobj.keys())

        for k in keys:
            ret.add_column(Column(k, k))
        return ret
    elif isinstance(r, dict):
        # = {'__parent': parent_row} if parent_row is not None else {}
        return FlatteningDict({k:pyobj_to_table(v, k) for k, v in r.items()})
    else:
        assert isinstance(r, (str, int, float)), type(r)
        return r


def _json_find_value(r, colname:str, findstr:str):
    'Return the value at dotted path *findstr* in *r*: a single match as-is, multiple matches as a Table with column *colname*.'
    matches = list(_json_find(r, findstr.split('.')))
    if not matches:
        return None
    if len(matches) == 1:
        return pyobj_to_table(matches[0], colname)
    return pyobj_to_table(matches, colname)


@defop('json-parse', 0, 1.5)
def op_json_parse(aipl, v:str, **kwargs) -> Table:
    '''Convert a json blob into a Table.
       With kwargs, each colname=path.to.field extracts that field into column *colname* of a single row.
       A single kwarg that selects a list returns that list as a Table, one row per item.'''
    r = json.loads(v)
    if not kwargs:
        if isinstance(r, dict):
            return pyobj_to_table([r], aipl.unique_key)
        else:
            return pyobj_to_table(r, aipl.unique_key)

    row = {colname: _json_find_value(r, colname, findstr) for colname, findstr in kwargs.items()}
    if len(row) == 1:
        (ret,) = row.values()
        if isinstance(ret, Table):
            return ret

    return Table([row])
