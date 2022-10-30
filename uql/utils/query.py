# TODO: properly explain/document this file, cus me sef i dont understand
import typing
from django.db.models import Q
from functools import reduce
from collections.abc import Sequence


ConjunctionTypes: typing.TypeAlias = (
    typing.Literal["_or"] | typing.Literal["_and"] | typing.Literal["_not"]
)
RelationTypes: typing.TypeAlias = (
    typing.Literal["_eq"]
    | typing.Literal["_neq"]
    | typing.Literal["_gt"]
    | typing.Literal["_gte"]
    | typing.Literal["_lt"]
    | typing.Literal["_lte"]
    | typing.Literal["_in"]
    | typing.Literal["_nin"]
    | typing.Literal["_contains"]
    | typing.Literal["_icontains"]
    | typing.Literal["_regex"]
)


class Relation:
    def __init__(self, name: RelationTypes, djtype: str, negate=False) -> None:
        """Direct relation between a key and it's value"""
        self.name = name
        self.djtype = djtype
        self.negate = negate

    def resolve(self, key: str, value: typing.Any) -> Q:
        res = Q(**{f"{key}{self.djtype}": value})
        return ~res if self.negate else res


class Conjunction:
    def __init__(
        self, name: ConjunctionTypes, resolve: typing.Callable[[list[Q]], Q]
    ) -> None:
        """Relationship between many values"""
        self.name = name
        self.resolve = resolve


# create relationships
relationships: dict[RelationTypes, Relation] = {
    "_eq": Relation("_eq", ""),
    "_neq": Relation("_neq", "", negate=True),
    "_gt": Relation("_gt", "__gt"),
    "_gte": Relation("_gte", "__gte"),
    "_lt": Relation("_lt", "__lt"),
    "_lte": Relation("_lte", "__lte"),
    "_in": Relation("_in", "__in"),
    "_nin": Relation("_nin", "__in", negate=True),
    "_contains": Relation("_contains", "__contains"),
    "_icontains": Relation("_icontains", "__icontains"),
    "_regex": Relation("_regex", "__regex"),
}

# create conjunctions
conjunctions: dict[ConjunctionTypes, Conjunction] = {
    "_or": Conjunction("_or", lambda items: reduce(lambda a, b: a | b, items)),
    "_and": Conjunction("_and", lambda items: reduce(lambda a, b: a & b, items)),
    "_not": Conjunction("_not", lambda items: ~reduce(lambda a, b: a & b, items)),
}

allKeywords: dict[str, Conjunction | Relation] = {
    **relationships,
    **conjunctions,
}

# make query func
# TODO: implement cache
def makeQuery(query: dict[str, typing.Any], **kwargs: str):
    parent: str = kwargs.get("parent", "")
    res: list[Q] = []

    for item, value in query.items():
        if modifier := allKeywords.get(item):

            if type(modifier) == Relation:
                modifier = typing.cast(Relation, modifier)
                res.append(modifier.resolve(parent, value))

            elif type(modifier) == Conjunction:
                modifier = typing.cast(Conjunction, modifier)
                assert isinstance(value, Sequence)
                res.append(
                    modifier.resolve([makeQuery(i, parent=parent) for i in value])
                )
        else:
            res.append(makeQuery(value, parent=f"{parent}__{item}" if parent else item))

    return reduce(lambda a, b: a & b, res)
