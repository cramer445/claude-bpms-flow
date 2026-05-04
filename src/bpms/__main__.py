"""BPMS Process Engine entry point."""

from bpms import __version__
from bpms.cli import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()
