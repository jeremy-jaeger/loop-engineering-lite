from money import dollars_to_cents

import pytest


@pytest.mark.parametrize(
    "value, expected",
    [
        ("$12.34", 1234),
        ("12.34", 1234),
        ("10", 1000),
        ("-12.34", ValueError),
        ("", ValueError),
        ("abc", ValueError),
    ],
)
def test_dollars_to_cents(value, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            dollars_to_cents(value)
    else:
        assert dollars_to_cents(value) == expected
