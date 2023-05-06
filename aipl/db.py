from functools import cached_property
import sys
import json
import sqlite3


def dict_factory(cursor, row):
    return dict((k, v) for (k, *_), v in zip(cursor.description, row))


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
            tinfo = self.query(f'PRAGMA table_info({tblname})')
            if not tinfo:
                return {}

            self.tables[tblname] = {c['name']:c for c in tinfo}

        return self.tables[tblname]

    def insert(self, tblname, **kwargs):
        if tblname not in self.tables:
            fieldstr = ', '.join(f'{k} {sqlite_type(v)}' for k,v in kwargs.items())
            self.con.execute(f'CREATE TABLE IF NOT EXISTS {tblname} ({fieldstr})')

        fieldnames = ','.join(kwargs.keys())
        valholders = ','.join(['?']*len(kwargs))
        self.con.execute(f'INSERT INTO {tblname} ({fieldnames}) VALUES ({valholders})', tuple(pyobj_to_sqlite(v) for v in kwargs.values()))
        self.con.commit()
        return kwargs

    def table(self, tblname):
        return self.query(f'SELECT * FROM {tblname}')

    def select(self, tblname, **kwargs):
        tinfo = self.get_table_info(tblname)
        if not tinfo:
            return []

        wheres = [f'{k}=?' for k in kwargs.keys()]
        wherestr = ' AND '.join(wheres)
        results = self.query(f'SELECT * FROM {tblname} WHERE {wherestr}',
                              *tuple(kwargs.values()))

        return [{k:sqlite_to_pyobj(v, tinfo[k]['type'])
                    for k, v in row.items()
                } for row in results]

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


def test_db():
    import tempfile
    with tempfile.NamedTemporaryFile() as f:
        with Database(f.name) as db:
            db.insert('people', id=10, name='James Jones')
            db.insert('people', id=11, name='Maria Garcia')
            db.insert('people', id=12, name='Michael Smith')

        db = Database(f.name)
        assert len(db.table('people')) == 3
        assert db.query('SELECT * FROM people WHERE id=?', 12)[0].name == 'Michael Smith'


if __name__ == '__test__':
    test_db()
