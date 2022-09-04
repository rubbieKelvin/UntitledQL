from django.db.models import Q
from typing import Callable, TypeVar

T = TypeVar("T", dict, list)

QUERY_UNIONS = dict(AND="_and", OR="_or", NOT="_not")

QUERY_RELATIONSHIPS = dict(
    EQUALS="_eq",
    NOT_EQUALS="_neq",
    IS_NULL="_null",
    GREATER_THAN="_gt",
    GREATER_THAN_OR_EQUALS="_gte",
    LESS_THAN="_lt",
    LESS_THAN_OR_EQUALS="_lte",
    IN="_in",
    NOT_IN="_nin",
    CONTAINS="_contains",
    INSENSITIVE_CONTAINS="_icontains",
    REGEX="_regex",
)

RAW_QUERY_MAPPING = {
    QUERY_RELATIONSHIPS["EQUALS"]: dict(negate=False, ext=""),
    QUERY_RELATIONSHIPS["NOT_EQUALS"]: dict(negate=True, ext=""),
    QUERY_RELATIONSHIPS["IS_NULL"]: dict(negate=False, ext="__isnull"),
    QUERY_RELATIONSHIPS["GREATER_THAN"]: dict(negate=False, ext="__gt"),
    QUERY_RELATIONSHIPS["GREATER_THAN_OR_EQUALS"]: dict(negate=False, ext="__gte"),
    QUERY_RELATIONSHIPS["LESS_THAN"]: dict(negate=False, ext="__lt"),
    QUERY_RELATIONSHIPS["LESS_THAN_OR_EQUALS"]: dict(negate=False, ext="__lte"),
    QUERY_RELATIONSHIPS["IN"]: dict(negate=False, ext="__in"),
    QUERY_RELATIONSHIPS["NOT_IN"]: dict(negate=True, ext="__in"),
    QUERY_RELATIONSHIPS["CONTAINS"]: dict(negate=False, ext="__contains"),
    QUERY_RELATIONSHIPS["INSENSITIVE_CONTAINS"]: dict(negate=False, ext="__icontains"),
    QUERY_RELATIONSHIPS["REGEX"]: dict(negate=False, ext="__regex"),
}


RELATIONSHIP_QUERY_MAPING = {
    QUERY_UNIONS["AND"]: lambda parent, value: _and_rel(
        mapQ(value, parent=parent, join=False)
    ),
    QUERY_UNIONS["OR"]: lambda parent, value: _or_rel(
        mapQ(value, parent=parent, join=False)
    ),
    QUERY_UNIONS["NOT"]: lambda parent, value: ~_and_rel(
        mapQ(value, parent=parent, join=False)
    ),
}


def _relation(queries: list[Q], bonder: Callable[[Q, Q], Q]) -> Q:
    if not queries:
        return None
    res = queries[0]
    for q in queries[1:]:
        res = bonder(res, q)
    return res


def _and_rel(queries: list[Q]) -> Q:
    return _relation(queries, lambda a, b: a & b)


def _or_rel(queries: list[Q]) -> Q:
    return _relation(queries, lambda a, b: a | b)


def mapQ(query: dict, parent: str | None = None, join: bool = True) -> Q | list[Q]:
    """Parses a dictionary into django.db.models.Q class"""
    res = []
    for key, val in query.items():

        if key in QUERY_RELATIONSHIPS.values():
            r_map = RAW_QUERY_MAPPING[key]
            resultant_query = Q(**{f'{parent}{r_map["ext"]}': val})
            res.append((~resultant_query) if r_map["negate"] else resultant_query)
        elif key in QUERY_UNIONS.values():
            rel = RELATIONSHIP_QUERY_MAPING[key]
            res.append(rel(parent, val))
        else:
            root = (
                f"{parent}__{key}" if (parent and not parent.startswith("_")) else key
            )
            res.append(mapQ(val, parent=root, join=True))
    return _and_rel(res) if join else res


def cleanup(data, struct: dict):
    "remove keys from data"
    for key, item in struct.items():
        if not (key in data):
            continue

        if type(item) == bool:
            if item:
                del data[key]
        elif type(item) == dict:
            if type(data[key]) == list:
                [cleanup(item, struct[key]) for item in data[key]]
            else:
                cleanup(data[key], struct[key])
