from .client import UnrestClient

client = UnrestClient()


def test(fn):
    def _():
        print(f"\n{fn.__name__}")
        print(fn(), end="\n\n")

    return _()


@test
def test_model_fetch_query():
    return client.call({"intent": "models.users"})
