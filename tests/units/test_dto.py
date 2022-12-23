import pytest
from uql.utils.dto import *


def test_string_validation():
    # Test validating a non-nullable string with no constraints
    rule = String()
    rule.validate("hello")
    rule.validate("world")
    with pytest.raises(ValueError):
        rule.validate(None)

    # Test validating a nullable string with no constraints
    rule = String(nullable=True)
    rule.validate("hello")
    rule.validate("world")
    rule.validate(None)

    # Test validating a string with a minimum length
    rule = String(min_length=5)
    rule.validate("hello")
    with pytest.raises(ValueError):
        rule.validate("hi")

    # Test validating a string with a maximum length
    rule = String(max_length=5)
    rule.validate("hello")
    rule.validate("world")
    with pytest.raises(ValueError):
        rule.validate("this is a longer string")

    # Test validating a string with a custom validator
    def validate_even_length(s: str) -> bool:
        return len(s) % 2 == 0

    rule = String(validators=[validate_even_length])
    rule.validate("hell")
    with pytest.raises(ValueError):
        rule.validate("world")

    # Test validating a string with multiple validators
    def validate_contains_vowel(s: str) -> bool:
        return any((c in "aeiou") for c in s)

    rule = String(validators=[validate_even_length, validate_contains_vowel])
    rule.validate("hell")
    with pytest.raises(ValueError):
        rule.validate("wrld")

    # Test validating a string with disallowed whitespace
    rule = String(allow_whitespace=False)
    rule.validate("hello")
    with pytest.raises(ValueError):
        rule.validate("hello world")

    # Test validating a string with disallowed numeric characters
    rule = String(allow_numeric=False)
    rule.validate("hello")
    with pytest.raises(ValueError):
        rule.validate("hello1")

    # Test validating a string with disallowed special characters
    rule = String(allow_special_characters=False)
    rule.validate("hello")
    with pytest.raises(ValueError):
        rule.validate("h@llo")

    # Test validating a string with disallowed uppercase characters
    rule = String(allow_uppercase=False)
    rule.validate("hello")
    with pytest.raises(ValueError):
        rule.validate("HELLO")

    # Test validating a string with disallowed lowercase characters
    rule = String(allow_lowercase=False)
    rule.validate("HELLO")
    with pytest.raises(ValueError):
        rule.validate("hello")

    # Test validating a string with a pattern
    rule = String(pattern=r"\d{3}-\d{3}-\d{4}")
    rule.validate("123-456-7890")
    with pytest.raises(ValueError):
        rule.validate("123-4567-890")
        rule.validate("1234567890")
        rule.validate("123 456 7890")


def test_number_validation():
    # Test validating a non-nullable number with no constraints
    rule = Number()
    rule.validate(5)
    rule.validate(10.5)
    with pytest.raises(ValueError):
        rule.validate(None)

    # Test validating a nullable number with no constraints
    rule = Number(nullable=True)
    rule.validate(5)
    rule.validate(10.5)
    rule.validate(None)

    # Test validating a number with a minimum value
    rule = Number(minimum=5)
    rule.validate(5)
    rule.validate(10.5)
    with pytest.raises(ValueError):
        rule.validate(4)
        rule.validate(4.9)

    # Test validating a number with a maximum value
    rule = Number(maximum=5)
    rule.validate(5)
    with pytest.raises(ValueError):
        rule.validate(5.1)
        rule.validate(10)

    # Test validating a number with a custom validator
    def validate_even(n: int | float) -> bool:
        return n % 2 == 0

    rule = Number(validators=[validate_even])
    rule.validate(6)
    with pytest.raises(ValueError):
        rule.validate(5)
        rule.validate(5.1)

    # Test validating a number with multiple validators
    def validate_divisible_by_three(n: int | float) -> bool:
        return n % 3 == 0

    rule = Number(validators=[validate_even, validate_divisible_by_three])
    rule.validate(6)
    with pytest.raises(ValueError):
        rule.validate(5)
        rule.validate(5.1)
        rule.validate(9)

    # Test validating an integer-only number
    rule = Number(integer_only=True)
    rule.validate(5)
    with pytest.raises(ValueError):
        rule.validate(5.1)
        rule.validate(10.5)

    # Test validating a number with a minimum and maximum value
    rule = Number(minimum=5, maximum=10)
    rule.validate(5)
    rule.validate(7.5)
    rule.validate(10)
    with pytest.raises(ValueError):
        rule.validate(4)
        rule.validate(10.1)

    # Test validating a number with a minimum, maximum, and validators
    rule = Number(minimum=5, maximum=10, validators=[validate_even])
    rule.validate(6)
    rule.validate(8)
    rule.validate(10)
    with pytest.raises(ValueError):
        rule.validate(5.1)
        rule.validate(11)
        rule.validate(7)


def test_boolean_validation():
    # Test validating a non-nullable boolean with no constraints
    rule = Boolean()
    rule.validate(True)
    rule.validate(False)
    with pytest.raises(ValueError):
        rule.validate(None)

    # Test validating a nullable boolean with no constraints
    rule = Boolean(nullable=True)
    rule.validate(True)
    rule.validate(False)
    rule.validate(None)


def test_dictionary():
    # Test nullable flag
    dictionary = Dictionary(
        {
            "password": String(min_length=6),
            "username": String(
                min_length=3, allow_whitespace=False, allow_special_characters=False
            ),
        },
        nullable=True,
    )
    dictionary.validate(None)
    dictionary.validate({"username": "rubbie", "password": "secretPassword"})

    dictionary = Dictionary(
        {
            "password": String(min_length=6),
            "username": String(
                min_length=3, allow_whitespace=False, allow_special_characters=False
            ),
        },
        nullable=False,
    )
    with pytest.raises(
        ValueError, match=r"value is None but nullable flag is set to False"
    ):
        dictionary.validate(None)
    dictionary.validate({"username": "rubbie", "password": "secretPassword"})

    # Test min_length and max_length flags
    dictionary = Dictionary(
        {
            "password": String(min_length=6),
            "username": String(
                min_length=3, allow_whitespace=False, allow_special_characters=False
            ),
        },
        min_length=2,
        max_length=3,
    )
    dictionary.validate({"username": "rubbie", "password": "secretPassword"})
    with pytest.raises(
        ValueError,
        match=r"value has 1 key-value pairs, which is less than the minimum of 2",
    ):
        dictionary.validate({"username": "rubbie"})
    with pytest.raises(
        ValueError,
        match=r"value has 4 key-value pairs, which is more than the maximum of 3",
    ):
        dictionary.validate(
            {
                "username": "rubbie",
                "password": "secretPassword",
                "email": "rubbie@example.com",
                "age": 25,
            }
        )

    # Test allow_unknown_keys flag
    dictionary = Dictionary(
        {
            "password": String(min_length=6),
            "username": String(
                min_length=3, allow_whitespace=False, allow_special_characters=False
            ),
        },
        allow_unknown_keys=True,
    )
    dictionary.validate(
        {
            "username": "rubbie",
            "password": "secretPassword",
            "email": "rubbie@example.com",
        }
    )


def test_list_validation():
    # Test valid list
    List(
        String(min_length=3),
        min_length=2,
        max_length=3,
    ).validate(["hello", "world"])

    # Test list with too many elements
    with pytest.raises(
        ValueError, match="has 4 elements, which is more than the maximum of 3"
    ):
        List(
            String(min_length=3),
            min_length=2,
            max_length=3,
        ).validate(["hello", "world", "longer", "list"])

    # Test list with too few elements
    with pytest.raises(
        ValueError, match="has 1 elements, which is less than the minimum of 2"
    ):
        List(
            String(min_length=3),
            min_length=2,
            max_length=3,
        ).validate(["hi"])

    # Test nullable list
    List(
        String(min_length=3),
        min_length=2,
        max_length=3,
        nullable=True,
    ).validate(None)

    # Test list with invalid element
    with pytest.raises(
        ValueError,
        match="shorter than the minimum length of 3",
    ):
        List(
            String(min_length=3),
            min_length=2,
            max_length=3,
        ).validate(["hi", "world"])


def test_any_validation():
    # Test valid value
    Any(
        [String(min_length=3), String(max_length=5)],
    ).validate("hello")

    # Test invalid value
    with pytest.raises(ValueError, match="does not meet any of the provided rules"):
        Any(
            [Number(minimum=3), Number(minimum=5)],
        ).validate("hi")

    # Test nullable value
    Any(
        [String(min_length=3), String(max_length=5)],
        nullable=True,
    ).validate(None)

    # Test invalid type
    with pytest.raises(ValueError, match="does not meet any of the provided rules"):
        Any(
            [String(min_length=3), String(max_length=5)],
        ).validate(123)

    # Test value that passes Number rule
    Any(
        [Number(minimum=10), Number(maximum=20)],
    ).validate(15)

    # Test value that passes multiple rules
    Any(
        [Number(minimum=10), Boolean()],
    ).validate(True)


def test_non_null_validation():
    # Test valid value
    NonNull().validate("Hello")

    # Test null value
    with pytest.raises(ValueError, match="should not be None"):
        NonNull().validate(None)
