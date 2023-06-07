from typing import Mapping, List
from copy import copy

from aipl import AIPLException
from .utils import fmtargs, fmtkwargs, stderr, strify

UNWORKING = object()

class Row(dict):
    pass


class Column:
    def __init__(self, key, name=''):
        self.name = name or key
        self.key = key

    @property
    def hidden(self) -> bool:
        return self.name.startswith('_')

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

    def __repr__(self):
        return f"<Column {self.name} {self.key}>"

    def deepname(self, table):
        if table.rows:
            r = self.get_value(table.rows[0])
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

            obj = obj.parent_row

            if obj is None:
                raise KeyError(k)

    @property
    def value(self):
        return self._table.columns[-1].get_value(self._row)

    def items(self):
        return self._asdict().items()

    def _asdict(self, named_only=False):
        'if named_only=False, add current_col as "input" if it is hidden.  otherwise ignore it too'
        d = {}

        for c in self._table.columns:
            if c.hidden:
                if named_only or c is not self._table.current_col:
                    continue

                k = 'input'
            else:
                k = c.name

            v = c.get_value(self._row)

            if v is None:
                continue
            elif isinstance(v, Table):
                v = [r._asdict() for r in v]
            elif not isinstance(v, (int, float, str)):
                v = str(v)

            if k in d:
                del d[k]
            d[k] = v

        return d

    @property
    def parent_row(self) -> 'LazyRow':
        return self._row.get('__parent', None)

    def __repr__(self):
        return f"<LazyRow row={self._asdict()} parent={self.parent_row!r}>"


class Table:
    def __init__(self, rows:List[Mapping|LazyRow]=[], parent:'Table|None'=None):
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

    def __len__(self):
        return len(self.rows)

    def __bool__(self):
        return len(self.rows) > 0

    def __copy__(self) -> 'Table':
        'Returns structural copy of table with all columns and no rows.'
        ret = Table()

        for c in self.columns:
            ret.add_column(copy(c))

        ret.rows = []
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
    def shape(self) -> List[int]:
        if not self.rows:
            return [0]
        dims = [len(self.rows)]
        if self.columns:
            firstrowval = self.current_col.get_value(self.rows[0])
            if isinstance(firstrowval, Table):
                dims += firstrowval.shape
        return dims

    @property
    def rank(self) -> int:
        return len(self.shape)

    @property
    def colnames(self):
        return [c.name for c in self.columns]

    @property
    def colkeys(self):
        return [c.key for c in self.columns]

    @property
    def current_col(self) -> Column:
        return self.columns[-1]

    @property
    def deepcolnames(self) -> str:
        return ','.join(f'{c.deepname(self)}' for c in self.columns if not c.hidden or c is self.current_col) or "no cols"

    def __getitem__(self, k:int) -> LazyRow:
        if k >= len(self.rows):
            raise IndexError('table index out of range')
        return LazyRow(self, self.rows[k])

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
                self.add_column(Column(k))

    def add_column(self, col:Column):
        if self.rows:
            assert col.get_value(self.rows[0]) is not UNWORKING
        if col.key in self.colkeys or col.name in self.colnames:
            return
        self.columns.append(col)

    def get_column(self, name:str) -> Column:
        if name == 'input':
            return self.columns[-1]

        for c in self.columns:
            if c.name == name:
                return c

        return None
