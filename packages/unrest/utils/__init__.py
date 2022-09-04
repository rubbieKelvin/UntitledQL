def fromDotNotation(container: dict, path: str, parent=None):
    parent = parent or "$root"

    key = path.split(".")[0]
    dots = path.split(".")[1:]

    if type(container) != dict:
        raise TypeError(f'"{key}" is not a subroot')

    if not (key in container):
        raise KeyError(f'key "{key}" inexistent in {parent}')

    if len(dots) > 0:
        return fromDotNotation(
            container.get(key, {}), ".".join(dots), f"{parent}.{key}"
        )
    return container.get(key)
