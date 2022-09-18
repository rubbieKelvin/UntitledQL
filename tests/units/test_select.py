from uql.utils.select import selectKeys

data = {
    "name": {
        "common": "Lesotho",
        "official": "Kingdom of Lesotho",
    }
}


def test_selectkeys():
    assert {"name": data["name"]} == selectKeys(data, {"name": True})
    assert {"name": {"common": data["name"]["common"]}} == selectKeys(
        data, {"name": {"common": True}}
    )
