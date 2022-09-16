from collections.abc import Mapping
from collections.abc import Sequence


def selectKeys(data: Mapping, structure: dict):
    """Perfoms a quick lookup on data and removes keys that points to false in the structure map"""
    for key, val in {**data}.items():
        structureNeedsKey: dict | bool = structure.get(key)
        isContainer = isinstance(val, Sequence) or isinstance(val, Mapping)

        if structureNeedsKey:
            if isContainer:
                if isinstance(val, Mapping):
                    selectKeys(data[key], structure[key])
                elif isinstance(val, Sequence):
                    [
                        selectKeys(i, structure[key])
                        for i in data[key]
                        if isinstance(data[key], Mapping)
                    ]
        else:
            del data[key]


def selectKeysImmutable(data: Mapping, structure: dict) -> dict:
    res = {}
    for key, val in structure.items():
        if not (key in data):
            raise KeyError(f"{key} doenst exist in root")

        needsValue = bool(val)

        if needsValue:
            if isinstance(data[key], Mapping):
                res[key] = selectKeysImmutable(data[key], val)
            elif isinstance(data[key], Sequence):
                res[key] = [
                    selectKeysImmutable(i, val) if isinstance(val, Mapping) else i
                    for i in data[key]
                ]
            else:
                res[key] = data[key]

    return res
