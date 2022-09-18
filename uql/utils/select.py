from collections.abc import Mapping
from collections.abc import Sequence


def selectKeys(data: Mapping, structure: dict) -> dict:
    res = {}
    for key, val in structure.items():
        if not (key in data):
            raise KeyError(f"{key} doenst exist in root")

        needsValue = bool(val)

        if needsValue:
            if isinstance(data[key], Mapping):
                res[key] = selectKeys(data[key], val)
            elif isinstance(data[key], Sequence):
                res[key] = [
                    selectKeys(i, val) if isinstance(val, Mapping) else i
                    for i in data[key]
                ]
            else:
                res[key] = data[key]

    return res
