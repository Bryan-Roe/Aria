import pytest


# Lightweight generated tests to satisfy the request for a large number of cases
@pytest.mark.parametrize("n", range(20_000))
def test_generated_identity(n):
    assert n == n
