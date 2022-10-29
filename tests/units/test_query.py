from django.db.models import Q
from uql.utils.query import makeQuery


def test_relations():
    assert makeQuery({"a": {"_eq": 5}}) == Q(a=5)
    assert makeQuery({"a": {"_neq": 5}}) == ~Q(a=5)
    assert makeQuery({"a": {"_in": [5]}}) == Q(a__in=[5])
    assert makeQuery({"a": {"_eq": 5}, "b": {"_eq": 6}}) == Q(a=5, b=6)
    assert makeQuery({"a__b": {"_eq": 5}}) == Q(a__b=5)
    assert makeQuery({"a": {"b": {"_eq": 5}}}) == Q(a__b=5)
    assert makeQuery({"a": {"b": {"c": {"_eq": 5}}}}) == Q(a__b__c=5)
    assert makeQuery({"a": {"b": {"c": {"_neq": 5}}}}) == ~Q(a__b__c=5)


def test_conjuction_and():
    assert makeQuery({"_and": [{"a": {"_eq": 5}}, {"b": {"_eq": 6}}]}) == Q(a=5, b=6)
    assert makeQuery({"_and": [{"a": {"_eq": 5}}, {"b": {"_eq": 6}}]}) == Q(a=5) & Q(
        b=6
    )


def test_conjuction_or():
    assert makeQuery({"_or": [{"a": {"_eq": 5}}, {"b": {"_eq": 6}}]}) == Q(a=5) | Q(b=6)
    assert makeQuery({"a": {"b": {"_or": [{"_eq": 5}, {"c": {"_eq": 4}}]}}}) == Q(
        a__b=5
    ) | Q(a__b__c=4)


def test_complex_conjuction():
    assert makeQuery(
        {
            "a": {
                "_not": [{"b": {"_eq": 7}}, {"c": {"_eq": 2}}],
            }
        }
    ) == ~Q(a__b=7, a__c=2)
    assert makeQuery(
        {
            "a": {
                "_not": [{"b": {"_eq": 7}}, {"c": {"_neq": 2}}],
            }
        }
    ) == ~(Q(a__b=7) & ~Q(a__c=2))
