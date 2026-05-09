"""
Example Tool: Fibonacci Calculator
Demonstrates a simple mathematical tool
"""


def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number

    Args:
        n: Position in Fibonacci sequence (0-indexed)

    Returns:
        The nth Fibonacci number
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    if n <= 1:
        return n

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b

    return b


# Example usage:
if __name__ == "__main__":
    for i in range(10):
        print(f"F({i}) = {calculate_fibonacci(i)}")
