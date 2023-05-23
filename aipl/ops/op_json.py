import json

from aipl import defop, AIPLException


class _jsonEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return obj.text  # for e.g. xmlElements
        except Exception:
            return str(obj)


@defop('json', 100, 0, 1)
def op_json(aipl, d:'LazyRow'):
    jsonenc = _jsonEncoder()
    return jsonenc.encode(d._asdict())


@defop('parse-json', 0, 0.5, 1)
def op_parse_json(aipl, v:str):
    return json.loads(v)


@defop('assert-json', 100, None)
def op_assert_json(aipl, t:'Table', prompt:str=''):
    if t._asdict() != json.loads(prompt):
        jsonenc = _jsonEncoder()
        raise AIPLException(f'assert failed! value not equal\n  ' + jsonenc.encode(t._asdict()))
