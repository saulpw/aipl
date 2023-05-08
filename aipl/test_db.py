from . import Database


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
