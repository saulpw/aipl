from typing import Mapping, List
from copy import copy

from .utils import fmtargs, fmtkwargs, stderr, strify


class Row(dict):
    pass


class Column:
    def __init__(self, key, name=''):
        self.name = name or key
        self.key = key
        self.table = None

    def get_value(self, row:Row):
        if isinstance(self.key, (list, tuple)):
            obj = row
            for k in self.key:
                obj = obj.get(k)
                if obj is None:
                    return None
            return obj

        return row.get(self.key)

    def __str__(self):
        return f'[Column {self.name}]'

    @property
    def deepname(self):
        if self.table.rows:
            r = self.get_value(self.table.rows[0])
            if isinstance(r, Table):
                return f'{self.name}:{r.deepcolnames}'

        return self.name or self.key


class LazyRow(Mapping):
    def __init__(self, table:'Table', row:Row):
        self._row = row
        self._table = table

    def __copy__(self):
        return LazyRow(self._table, self._row)

    def __len__(self):
        return len(self._table.columns)

    def __iter__(self):
        assert isinstance(self.value, Table), type(self.value)
        return iter(self.value)

    def __getitem__(self, k):
        obj = self
        while True:
            c = obj._table.get_column(k)
            if c:
                return c.get_value(self._row)

            if '__parent__' not in obj._row:
                break

            obj = obj._row['__parent']

        raise KeyError(k)

    @property
    def value(self):
        return self._table.columns[-1].get_value(self._row)

    def items(self):
        return self._asdict().items()

    def _asdict(self):
        d = {}
        for c in self._table.columns:

            v = c.get_value(self._row)
            if isinstance(v, Table):
                v = [r._asdict() for r in v]
            if v is not None:
                d[c.name] = v
        return d

    def __repr__(self):
        return strify(self._asdict())


class Table:
    def __init__(self, rows:List[Mapping|LazyRow]=[]):
        self.rows = []  # list of Row
        self.columns = []  # list of Column

        for row in rows:
            self.add_row(row)

    def __copy__(self):
        ret = Table()

        for c in self.columns:
            ret.add_column(copy(c))

        ret.rows = self.rows
        return ret

    def axis(self, rank:int=0):
        if self.rank > rank:
            firstrowval = self.columns[-1].get_value(self.rows[0])
            return firstrowval.axis(rank)

        return self

    @property
    def values(self):
        return [r.value for r in self]

    @property
    def shape(self):
        if not self.rows:
            return []
        dims = [len(self.rows)]
        firstrowval = self.columns[-1].get_value(self.rows[0])
        if isinstance(firstrowval, Table):
            dims += firstrowval.shape
        return dims

    @property
    def rank(self):
        return len(self.shape)

    @property
    def colnames(self):
        return [c.name for c in self.columns]

    @property
    def colkeys(self):
        return [c.key for c in self.columns]

    @property
    def deepcolnames(self) -> str:
        return ','.join(f'{c.deepname}' for c in self.columns)

    def __getitem__(self, k:int):
        #return LazyRow(self, self.rows[k])
        if not self.columns:
            raise Exception('no columns!')
        if k >= len(self.rows):
            raise Exception('not enough rows!')

        return self.columns[-1].get_value(self.rows[k])

    def _asdict(self):
        return [r._asdict() for r in self]

    def __repr__(self):
        shapestr = 'x'.join(map(str, self.shape))
        contentstr = ''
        if not self.rows:
            contentstr += '(nothing)'
        else:
            contentstr += strify(self[0], maxlen=20)
        if len(self.rows) > 1:
            contentstr += ' ...'
        return f'[{shapestr} {self.deepcolnames}] {contentstr}'

    def __iter__(self):
        for r in self.rows:
            yield LazyRow(self, r)

    def add_row(self, row:Row|LazyRow):
        if isinstance(row, LazyRow):
            self.rows.append(row._row)
        else:
            self.rows.append(row)
            self.add_new_columns(row)

    def add_new_columns(self, d:dict):
        for k in d:
            if not str(k).startswith('__') and k not in self.colnames:
                self.add_column(Column(k, k))

    def add_column(self, col:Column):
        if col.key in self.colkeys:
            return
        col.table = self
        self.columns.append(col)

    def get_column(self, name:str) -> Column:
        if name == 'input':
            return self.columns[-1]

        for c in self.columns:
            if c.name == name:
                return c

    def apply(self, aipl, opfunc, args, kwargs, contexts=[]):
        newkey = aipl.unique_key
        lastcolname = self.columns[-1].name

        array_output = None  # directly returnable from rank >= 1
        row_outputs = None  # (parent_row, result_value)

        if opfunc.rankin == -1 or opfunc.arity == 0:  # generator
            assert opfunc.rankin == -1 and opfunc.arity == 0
            array_output = opfunc(aipl, *args, **kwargs)

        elif self.rank == 0:
            raise Exception('no rows')

        elif self.rank > opfunc.rankin+1:  # go out to edge
            row_outputs = [
                (row, row.value.apply(aipl, opfunc, args, kwargs,
                                      contexts=contexts+[row]))
                for row in self
            ]

        else:  # self.rank == 1   # a simple array (column of scalars)
            if opfunc.rankin == 2:  # table
                array_output = opfunc(aipl, self, *fmtargs(args, contexts), **fmtkwargs(kwargs, contexts))

            elif opfunc.rankin == 1:  # column
                array_output = opfunc(aipl, self.values, *fmtargs(args, contexts), **fmtkwargs(kwargs, contexts))

            elif opfunc.rankin == 0.5:  # row
                row_outputs = []
                for row in self:
                    try:
                        r = opfunc(aipl, row,
                                        *fmtargs(args, contexts+[row]),
                                        **fmtkwargs(kwargs, contexts+[row]))
                        if r:
                            row_outputs.append((row, r))
                    except Exception as e:
                        stderr(e) # and skip output row

            elif opfunc.rankin == 0:  # scalar
                row_outputs = []
                for row in self:
                    try:
                        r = opfunc(aipl, row.value,
                                        *fmtargs(args, contexts+[row]),
                                        **fmtkwargs(kwargs, contexts+[row]))
                        row_outputs.append((row, r))
                    except Exception as e:
                        stderr(e) # and skip output row

        # now deal with the result

        if opfunc.rankout == 0 and self.rank == 1:  # returns scalar
            if array_output is not None:
                return Table([dict([(lastcolname, array_output)])])

            self.add_column(Column(newkey))

            newrows = []
            for row, v in row_outputs:
                row._row[newkey] = v
                newrows.append(row._row)
            self.rows = newrows

        elif opfunc.rankout == 0.5 and self.rank == 1:  # returns dict/Bag; add to table
            if array_output:
                return Table([array_output])

            assert row_outputs

            newrows = []
            for row, bag in row_outputs:
                if bag:
                    for k, v in bag.items():
                        nk = f'{newkey}_{k}'
                        row._row[nk] = v

                    if not newrows:  # first time, assume keys are the same for all
                        for k in bag:
                            nk = f'{newkey}_{k}'
                            self.add_column(Column(nk, k))

                    newrows.append(row._row)

            self.rows = newrows


        elif opfunc.rankout == 1 and self.rank == 1:  # returns vector; add to each row
            self.add_column(Column(newkey))
            if array_output is not None:
                # XXX: may be a Table
                for row, v in zip(self.rows, array_output):
                    row[newkey] = v
            else:
                for row, v in row_outputs:
                    row._row[newkey] = Table([{'__parent':row, newkey:r} for r in v])

        elif opfunc.rankout == 2:  # returns List[dict|LazyRow] or Table
            if array_output:
                if isinstance(array_output, Table):
                    assert self.rank == 1
                    return array_output

                rows = list(array_output)
                assert rows
                if isinstance(rows[0], dict):
                    return Table(rows)
                elif isinstance(rows[0], LazyRow):
                    return Table(r._asdict() for r in rows)
                else:
                    assert False, type(rows[0])

#            if self.rank != 1:
#                return self  # ???

            for row, rows in row_outputs:
                if not isinstance(rows, Table):
                    rowlist = list(rows)
                    out = Table(rowlist)
                else:
                    out = rows

                for v in out.rows:
                    v['__parent'] = row

                self.add_column(Column(newkey))
                row._row[newkey] = out

        return self  # rankout == -1 or rankout >= 2
