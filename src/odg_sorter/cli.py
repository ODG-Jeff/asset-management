import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="odg-sorter")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("daemon")
    sub.add_parser("sort").add_argument("path")
    sub.add_parser("digest").add_argument("--since", default=None)
    sub.add_parser("reconcile")
    args = parser.parse_args(argv)
    # Verb handlers wired in later tasks.
    print(f"odg-sorter: cmd={args.cmd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
