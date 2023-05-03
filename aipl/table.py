from typing import Mapping, List


class Row(dict):  # dup from Database
    pass


class Column:
    def __init__(self, key):
        self.name = ''
        self.key = key
        self.table = None

    def get_value(self, row:Row):
        return row[self.key]

    def __str__(self):
        return f'[Column {self.name}]'


class LazyRow(Mapping):
    def __init__(self, table:'Table', row:Row):
        self._row = row
        self._table = table

    def __len__(self):
        return len(self._table.columns)

    def __iter__(self):
        return iter(self._asdict())

    def __getattr__(self, k):
        return self.__getitem__(k)

    def __getitem__(self, k):
        return self._table.get_column(k).get_value(self._row)

    @property
    def value(self):
        return self._table.columns[-1].get_value(self._row)

    def _asdict(self):
        d = {}
        for c in self._table.columns:
            k = c.name
            if not k and c is self._table.columns[-1]:
                k = 'value'

            if not k:
                continue

            v = c.get_value(self._row)
            if isinstance(v, Table):
                v = [r._asdict() for r in v]
            d[k] = v
        return d

    def __repr__(self):
        return str(self._asdict())

    def __str__(self):
        return strify(self._asdict())



class Table:
    def __init__(self, rows:List[Mapping]):
        self.rows = []  # list of Row
        self.columns = []  # list of Column

        for row in rows:
            self.add_row(row)

    @property
    def value(self):
        return [r.value for r in self]

    @property
    def shape(self):
        if not self.rows:
            return []
        dims = [len(self.rows)]
        firstrow = LazyRow(self, self.rows[0])
        if isinstance(firstrow.value, Table):
            dims += firstrow.value.shape
        return dims

    @property
    def rank(self):
        return len(self.shape)

    @property
    def colnames(self):
        return [c.name for c in self.columns]

    def __str__(self):
        shapestr = 'x'.join(map(str, self.shape))
        colnamestr = ','.join(self.colnames)
        return f'[{shapestr} {colnamestr}]'

    def __iter__(self):
        for r in self.rows:
            yield LazyRow(self, r)

    def add_row(self, row:Row):
        self.rows.append(row)
        for k in row:
            if not str(k).startswith('__') and k not in self.colnames:
                self.add_column(Column(k))

    def add_column(self, col:Column):
        col.table = self
#        assert col.name not in self.colnames, col.name
#        if self.rows:
#            v = col.get_value(self.rows[0])
#            assert v, (v, col)
        if self.columns and not self.columns[-1].name:
            self.columns.pop()
        self.columns.append(col)

    def get_column(self, name) -> Column:
        for c in self.columns:
            if c.name == name:
                return c

        raise Exception(f'no column "{name}"')

    def apply(self, aipl, opfunc, args, kwargs):
        k = aipl.unique_key

        if opfunc.rankin == 2:  # table
            ret = opfunc(aipl, self, *args, **kwargs)
            if opfunc.rankout == 2:
                return ret

        elif opfunc.rankin == 1:  # column
            if self.rank < 1:
                raise Exception('rank not high enough')
            elif self.rank == 1:
                ret = opfunc(aipl, self.value, *args, **kwargs)
                if opfunc.rankout == 0:
                    return ret
                elif opfunc.rankout == 1:
                    return Table(ret)
            else:
                results = [(row, row.value.apply(aipl, opfunc, args, kwargs)) for row in self]

        elif opfunc.rankin == 0.5:  # row
            results = [(row, opfunc(aipl, row, *args, **kwargs)) for row in self]

        elif opfunc.rankin == 0:  # scalar
            results = [(row, opfunc(aipl, row.value, *args, **kwargs)) for row in self]


        # now deal with output

        if opfunc.rankout == 0:  # returns scalar
            self.add_column(Column(k))
            for row, v in results:
                row._row[k] = v
        elif opfunc.rankout == 1:  # returns vector; turn into table
            self.add_column(Column(k))
            for row, v in results:
                row._row[k] = Table([{'__parent':row, k:r} for r in v])

        return self
