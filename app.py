"""
Aria Headless Entrypoint
Replaces UI mode with a minimal bootstrap runner.
"""

from core.runner import AriaRunner


def main():
    runner = AriaRunner()
    runner.run()


if __name__ == "__main__":
    main()
