import sys


def run_main_if_referenced(__name__, main):
    if __name__ == "__main__":
        sys.exit(main())
