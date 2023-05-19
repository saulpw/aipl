from aipl import defop


@defop('json', 0.5, 0, 1)
def op_json(aipl, d:'LazyRow'):
    import json
    class _jsonEncoder(json.JSONEncoder):
        def default(self, obj):
            try:
                return obj.text  # for e.g. xmlElements
            except Exception:
                return str(obj)

    jsonenc = _jsonEncoder()
    return jsonenc.encode(d._asdict())


@defop('parse-json', 0, 0.5, 1)
def op_parse_json(aipl, v:str):
    import json
    return json.loads(v)
