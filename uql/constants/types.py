import typing

Pk: typing.TypeAlias = int | str

IntentResult: typing.TypeAlias = (
    typing.Mapping[str, typing.Any] | typing.Sequence[typing.Any] | None
)
