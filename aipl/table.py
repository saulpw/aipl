from typing import Mapping, List
from copy import copy

from .utils import fmtargs, fmtkwargs, stderr, strify


class Row(dict):
    pass


class Column:
    def __init__(self, key, name=''):
        self.name = name or key
        self.key = key
        self.table = None  # set later by Table.add_column()

    @property
    def hidden(self) -> bool:
        return self.name.startswith('_')

    @property
    def last(self) -> bool:
        'is this the last column in the table?'
        return self is self.table.columns[-1]

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


class ParentColumn(Column):
    def __init__(self, name, origcol):
        super().__init__(name)
        self.origcol = origcol

    def get_value(self, row):
        return self.origcol.get_value(row['__parent']._row)


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
                return c.get_value(obj._row)

            if '__parent' not in obj._row:
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

            if c.hidden:
                if not c.last:
                    continue

#                if not d:
#                    return v  # simple scalar if no other named cols in the row

                k = 'input'
            else:
                k = c.name

            if isinstance(v, Table):
                v = [r._asdict() for r in v]

            if v is not None:
                d[k] = v
        return d

    @property
    def parent(self):
        return self._row.get('__parent', None)

    def __repr__(self):
        return f"<LazyRow row={self._asdict()} parent={self.parent!r}>"


class Table:
    def __init__(self, rows:List[Mapping|LazyRow]=[], parent:'Table'=None):
        self.rows = []  # list of dict
        self.columns = []  # list of Column
        self.parent = parent

        for row in rows:
            if isinstance(row, LazyRow):
                self.rows.append(row._row)
            elif isinstance(row, Mapping):
                self.rows.append(row)
                self.add_new_columns(row)
            else:
                raise TypeError(f"row must be Mapping or LazyRow not {type(row)}")

        if parent:
            for col in parent.columns:
                if not col.hidden:
                    self.add_column(ParentColumn(col.name, col))

    def __bool__(self):
        return len(self.rows) > 0

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
            return [0]
        dims = [len(self.rows)]
        if self.columns:
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
        return ','.join(f'{c.deepname}' for c in self.columns) or "no cols"

    def __getitem__(self, k:int):
        #return LazyRow(self, self.rows[k])
        if not self.columns:
            raise IndexError('table has no columns')
        if k >= len(self.rows):
            raise IndexError('table index out of range')

        return self.columns[-1].get_value(self.rows[k])

    def _asdict(self):
        return [r._asdict() for r in self]

    def __repr__(self):
        shapestr = 'x'.join(map(str, self.shape))
        contentstr = ''
        if self.rows:
            contentstr += strify(self[0], maxlen=20)
        if len(self.rows) > 1:
            contentstr += ' ...'
        return f'<Table [{shapestr} {self.deepcolnames}] {contentstr}>'

    def __iter__(self):
        for r in self.rows:
            yield LazyRow(self, r)

    def add_new_columns(self, row:Row):
        for k in row.keys():
            if not k.startswith('__'):
                self.add_column(Column(k, k))

    def add_column(self, col:Column):
        if col.key in self.colkeys or col.name in self.colnames:
            return
        col.table = self
        self.columns.append(col)

    def get_column(self, name:str) -> Column:
        if name == 'input':
            return self.columns[-1]

        for c in self.columns:
            if c.name == name:
                return c

        if self.parent:
            return self.parent.get_column(name)
        return None
