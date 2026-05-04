"""BPMS Process Engine entry point."""

from bpms import __version__


def main() -> None:
    print(f"BPMS Process Engine v{__version__}")


if __name__ == "__main__":
    main()
