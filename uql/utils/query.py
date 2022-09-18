# TODO: properly explain/document this file, cus me sef i dont understand
from django.db.models import Q
from typing import Callable, Any, cast
from functools import reduce
from collections.abc import Sequence


class QKeyword:
    _store = {}

    def __init__(self, name: str) -> None:
        self.name = name
        QKeyword._store[name] = self

    @staticmethod
    def get(name: str):
        return QKeyword._store.get(name, None)


class Relation(QKeyword):
    def __init__(self, name: str, djtype: str, negate=False) -> None:
        """Direct relation between a key and it's value"""
        self.name = name
        self.djtype = djtype
        self.negate = negate
        super().__init__(name)

    def resolve(self, key: str, value: Any) -> Q:
        res = Q(**{f"{key}{self.djtype}": value})
        return ~res if self.negate else res


class Conjunction(QKeyword):
    def __init__(self, name: str, resolve: Callable[[list[Q]], Q]) -> None:
        """Relationship between many values"""
        self.name = name
        self.resolve = resolve
        super().__init__(name)


# create relationships
Relation("_eq", "")
Relation("_neq", "", negate=True)
Relation("_gt", "__gt")
Relation("_gte", "__gte")
Relation("_lt", "__lt")
Relation("_lte", "__lte")
Relation("_in", "__in")
Relation("_nin", "__in", negate=True)
Relation("_contains", "__contains")
Relation("_icontains", "__icontains")
Relation("_regex", "__regex")

# create conjunctions
Conjunction("_or", lambda items: reduce(lambda a, b: a | b, items))
Conjunction("_and", lambda items: reduce(lambda a, b: a & b, items))
Conjunction("_not", lambda items: ~reduce(lambda a, b: a & b, items))

# make query func
# TODO: implement cache
def makeQuery(query: dict, **kwargs):
    parent = kwargs.get("parent")
    res = []

    for item, value in query.items():
        if qkw := QKeyword.get(item):
            qkw = cast(Conjunction | Relation, qkw)

            if type(qkw) == Relation:
                res.append(qkw.resolve(parent, value))
            elif type(qkw) == Conjunction:
                assert isinstance(value, Sequence)
                res.append(qkw.resolve([makeQuery(i, parent=parent) for i in value]))
        else:
            res.append(makeQuery(value, parent=f"{parent}__{item}" if parent else item))

    return reduce(lambda a, b: a & b, res)
