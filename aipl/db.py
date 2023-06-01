from functools import cached_property, wraps
import sys
import json
import sqlite3

from .utils import AttrDict


def dict_factory(cursor, row):
    return AttrDict((k, v) for (k, *_), v in zip(cursor.description, row))


def sqlite_to_pyobj(v, t:str):
    if t == 'JSON':
        return json.loads(v)
    return v


def pyobj_to_sqlite(v):
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(v)
    return v


def sqlite_type(v):
    if isinstance(v, int): return 'INTEGER'
    if isinstance(v, float): return 'REAL'
    if isinstance(v, (dict, list, tuple)): return 'JSON'
    return 'TEXT'


class Database:
    def __init__(self, dbfn):
        self.dbfn = dbfn
        self.tables = {}  # tablename -> { colname -> { .type:str, ... } }

    @cached_property
    def con(self):
        con = sqlite3.connect(self.dbfn)
        con.row_factory = dict_factory
        return con

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if not tb:
            self.con.commit()
        return False

    def get_table_info(self, tblname:str):
        if tblname not in self.tables:
            tinfo = self.query(f'PRAGMA table_info("{tblname}")')
            if not tinfo:
                return {}

            self.tables[tblname] = {c['name']:c for c in tinfo}

        return self.tables[tblname]

    def insert(self, tblname, **kwargs):
        if tblname not in self.tables:
            fieldstr = ', '.join(f'"{k}" {sqlite_type(v)}' for k,v in kwargs.items())
            self.con.execute(f'CREATE TABLE IF NOT EXISTS "{tblname}" ({fieldstr})')

        fieldnames = ','.join(f'"{x}"' for x in kwargs.keys())
        valholders = ','.join(['?']*len(kwargs))
        self.con.execute(f'INSERT INTO "{tblname}" ({fieldnames}) VALUES ({valholders})', tuple(pyobj_to_sqlite(v) for v in kwargs.values()))
        self.con.commit()
        return kwargs

    def table(self, tblname):
        return self.query(f'SELECT * FROM "{tblname}"')

    def select(self, tblname, **kwargs):
        tinfo = self.get_table_info(tblname)
        if not tinfo:
            return []

        wheres = [f'"{k}"=?' for k in kwargs.keys()]
        wherestr = ' AND '.join(wheres)
        results = self.query(f'SELECT * FROM "{tblname}" WHERE {wherestr}',
                              *tuple(kwargs.values()))

        return [AttrDict((k, sqlite_to_pyobj(v, tinfo[k]['type']))
                    for k, v in row.items()
                ) for row in results]

    def query(self, qstr, *args):
        try:
            cur = self.con.cursor()
            res = cur.execute(qstr, args)
            return res.fetchall()
        except sqlite3.OperationalError as e:
            print(e, file=sys.stderr)
            return []

    def sql(self, qstr):
        return self.con.execute(qstr)


def expensive(mockfunc=None):
    'Decorator to persistently cache result from func(r, kwargs).  Use as @expensive(mock_func) where mock_func has identical signature to func and returns a compatible result for --dry-run.'
    def _decorator(func):
        @wraps(func)
        def cachingfunc(db:Database, *args, **kwargs):
            if db.options.dry_run:
                if mockfunc:
                    return mockfunc(db, *args, **kwargs)
                else:
                    return f'<{func.__name__}({args} {kwargs})>'

            key = f'{args} {kwargs}'
            tbl = 'cached_'+func.__name__
            ret = db.select(tbl, key=key)
            if ret:
                row = ret[-1]
                if 'output' in row:
                    return row['output']

                del row['key']
                return row

            result = func(db, *args, **kwargs)

            if isinstance(result, dict):
                db.insert(tbl, key=key, **result)
            else:
                db.insert(tbl, key=key, output=result)

            return result

        return cachingfunc
    return _decorator
