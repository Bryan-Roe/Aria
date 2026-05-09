"""Generated utility functions for numeric summaries and simple statistics.

This module is intentionally pure (no filesystem/network side effects)
and safe for reuse in API and CLI layers.
"""

from __future__ import annotations

from typing import Iterable

Number = int | float


def to_floats(values: Iterable[Number]) -> list[float]:
    """Convert iterable numeric values to a list of floats.

    Args:
        values: Iterable of numeric values.

    Returns:
        List of float values.

    Raises:
        ValueError: If any value is non-numeric.
    """
    result: list[float] = []
    for value in values:
        if not isinstance(value, (int, float)):
            raise ValueError(f"Non-numeric value encountered: {value!r}")
        result.append(float(value))
    return result


def mean(values: Iterable[Number]) -> float:
    """Return arithmetic mean.

    Raises:
        ValueError: If values is empty.
    """
    nums = to_floats(values)
    if not nums:
        raise ValueError("mean requires at least one value")
    return sum(nums) / len(nums)


def median(values: Iterable[Number]) -> float:
    """Return median of values.

    Raises:
        ValueError: If values is empty.
    """
    nums = sorted(to_floats(values))
    n = len(nums)
    if n == 0:
        raise ValueError("median requires at least one value")

    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    return (nums[mid - 1] + nums[mid]) / 2.0


def percentile(values: Iterable[Number], p: float) -> float:
    """Compute percentile using linear interpolation.

    Args:
        values: Iterable of numeric values.
        p: Percentile in [0, 100].

    Returns:
        Percentile value.

    Raises:
        ValueError: If values empty or p outside [0, 100].
    """
    nums = sorted(to_floats(values))
    if not nums:
        raise ValueError("percentile requires at least one value")
    if p < 0 or p > 100:
        raise ValueError("p must be between 0 and 100")

    if len(nums) == 1:
        return nums[0]

    rank = (p / 100.0) * (len(nums) - 1)
    low = int(rank)
    high = min(low + 1, len(nums) - 1)
    fraction = rank - low
    return nums[low] + (nums[high] - nums[low]) * fraction


def variance(values: Iterable[Number], sample: bool = False) -> float:
    """Return variance (population by default, sample if sample=True).

    Raises:
        ValueError: If not enough values for requested mode.
    """
    nums = to_floats(values)
    n = len(nums)
    if n == 0:
        raise ValueError("variance requires at least one value")
    if sample and n < 2:
        raise ValueError("sample variance requires at least two values")

    mu = sum(nums) / n
    ss = sum((x - mu) ** 2 for x in nums)
    denom = (n - 1) if sample else n
    return ss / denom


def stddev(values: Iterable[Number], sample: bool = False) -> float:
    """Return standard deviation.

    Args:
        values: Iterable of numeric values.
        sample: Use sample variance when True.
    """
    return variance(values, sample=sample) ** 0.5


def five_number_summary(values: Iterable[Number]) -> dict[str, float]:
    """Return min, q1, median, q3, max summary.

    Returns:
        Dict with keys: min, q1, median, q3, max.
    """
    nums = sorted(to_floats(values))
    if not nums:
        raise ValueError("five_number_summary requires at least one value")

    return {
        "min": nums[0],
        "q1": percentile(nums, 25),
        "median": percentile(nums, 50),
        "q3": percentile(nums, 75),
        "max": nums[-1],
    }
