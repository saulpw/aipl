from functools import cached_property
import sqlite3


class Row(dict):
    pass


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return Row((k,v) for k,v in zip(fields, row))


class Database:
    def __init__(self, dbfn):
        self.dbfn = dbfn
        self.tables = set()

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

    def insert(self, tblname, **kwargs):
        def sqltype(v):
            if isinstance(v, int): return 'INTEGER'
            if isinstance(v, float): return 'REAL'
            return 'TEXT'

        if tblname not in self.tables:
            fieldstr = ', '.join(f'{k} {sqltype(v)}' for k,v in kwargs.items())
            self.con.execute(f'CREATE TABLE IF NOT EXISTS {tblname} ({fieldstr})')
            self.tables.add(tblname)

        fieldnames = ','.join(kwargs.keys())
        valholders = ','.join(['?']*len(kwargs))
        self.con.execute(f'INSERT INTO {tblname} ({fieldnames}) VALUES ({valholders})', tuple(str(x) for x in kwargs.values()))
        self.con.commit()
        return Row(kwargs)

    def table(self, tblname):
        return self.query(f'SELECT * FROM {tblname}')

    def query(self, qstr, *args):
        try:
            cur = self.con.cursor()
            res = cur.execute(qstr, args)
            return res.fetchall()
        except sqlite3.OperationalError as e:
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
