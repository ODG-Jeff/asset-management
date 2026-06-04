import argparse
import logging
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="odg-sorter")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("daemon")
    sort_parser = sub.add_parser("sort")
    sort_parser.add_argument("path")
    digest_parser = sub.add_parser("digest")
    digest_parser.add_argument("--since", default=None)
    sub.add_parser("reconcile")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.cmd == "sort":
        from odg_sorter.main import sort_one
        outcome = sort_one(Path(args.path))
        print(outcome)
        return 0

    # daemon/digest/reconcile come in later tasks.
    print(f"odg-sorter: cmd={args.cmd} not yet wired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
