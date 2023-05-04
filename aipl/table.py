from typing import Mapping, List

from .utils import fmtargs, fmtkwargs


class Row(dict):  # dup from Database
    pass


class Column:
    def __init__(self, key, name=''):
        self.name = name
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
        obj = self
        while not obj._table.get_column(k):
            obj = obj._row['__parent']

        return obj._table.get_column(k).get_value(self._row)

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
    def values(self):
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
        raise Exception('no str for table')

    def __repr__(self):
        shapestr = 'x'.join(map(str, self.shape))
        colnamestr = ','.join(self.colnames)
        return f'[{shapestr} {colnamestr}]'

    def __iter__(self):
        for r in self.rows:
            yield LazyRow(self, r)

    def add_row(self, row:Row):
        self.rows.append(row)
        self.add_new_columns(row)

    def add_new_columns(self, d:dict):
        for k in d:
            if not str(k).startswith('__') and k not in self.colnames:
                self.add_column(Column(k))

    def add_column(self, col:Column):
        col.table = self
        if self.columns and not self.columns[-1].name:
            self.columns.pop()
        self.columns.append(col)

    def get_column(self, name:str) -> Column:
        if name == 'input':
            return self.columns[-1]

        for c in self.columns:
            if c.name == name:
                return c

#        colnamestr = ','.join(self.colnames)
#        raise Exception(f'no column "{name}" in {colnamestr}')

    def apply(self, aipl, opfunc, args, kwargs, contexts=[]):
        newkey = aipl.unique_key
        lastcolname = self.columns[-1].name

        ret = None  # directly returnable from rank >= 1
        results = None  # (parent_row, result_value)

        if self.rank == 0:
            raise Exception('no rows')

        elif self.rank > 1:  # go out to edge
            results = [
                (row, row.value.apply(aipl, opfunc, args, kwargs,
                                      contexts=contexts+[row]))
                for row in self
            ]

        else:  # self.rank == 1   # a simple array (column of scalars)
            if opfunc.rankin == 2:  # table
                ret = opfunc(aipl, self, *fmtargs(args, contexts), **fmtkwargs(kwargs, contexts))

            elif opfunc.rankin == 1:  # column
                ret = opfunc(aipl, self.values, *fmtargs(args, contexts), **fmtkwargs(kwargs, contexts))

            elif opfunc.rankin == 0.5:  # row
                results = [(row, opfunc(aipl, row,
                                        *fmtargs(args, contexts+[row]),
                                        **fmtkwargs(kwargs, contexts+[row])))
                            for row in self]

            elif opfunc.rankin == 0:  # scalar
                results = [(row, opfunc(aipl, row.value,
                                        *fmtargs(args, contexts+[row]),
                                        **fmtkwargs(kwargs, contexts+[row]))) for row in self]

        # now deal with the result

        if opfunc.rankout == 0:  # returns scalar
            if ret is not None:
                return Table([dict([(lastcolname, ret)])])

            self.add_column(Column(newkey))
            for row, v in results:
                row._row[newkey] = v

        elif opfunc.rankout == 0.5:  # returns Bag; add to table
            if ret:
                return Table([ret])

            for row, v in results:
                for k in v:
                    nk = f'{newkey}_{k}'
                    row._row[nk] = v[k]

            for k in v:  # just use last row, they should all have the same keys
                nk = f'{newkey}_{k}'
                self.add_column(Column(nk, name=k))

        elif opfunc.rankout == 1:  # returns vector; turn into table
            assert ret is None, ret

            self.add_column(Column(newkey))
            for row, v in results:
                row._row[newkey] = Table([{'__parent':row, newkey:r} for r in v])

        return self  # rankout == -1 or rankout >= 2
