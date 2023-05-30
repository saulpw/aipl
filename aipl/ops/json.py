'''
Provides !json which converts Table into json blob,
and !json_parse which converts json blob into row.
'''

import json

from aipl import defop, Table


class _jsonEncoder(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


@defop('json', 100, 0)
def op_json(aipl, t:Table) -> str:
    'Convert a Table into a json blob.'
    jsonenc = _jsonEncoder()
    return jsonenc.encode(t._asdict())


@defop('json-parse', 0, 0.5, 1)
def op_json_parse(aipl, v:str) -> dict:
    'Convert a json blob into a LazyRow.'
    return json.loads(v)
