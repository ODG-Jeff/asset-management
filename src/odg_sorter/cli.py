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
    if args.cmd == "daemon":
        from odg_sorter.main import run_daemon
        return run_daemon()
    if args.cmd == "reconcile":
        from odg_sorter.main import STATE_PATH
        from odg_sorter.reconcile import reconcile
        from odg_sorter.state import State
        state = State(STATE_PATH)
        result = reconcile(state)
        print(result)
        return 0
    if args.cmd == "digest":
        from odg_sorter.config.paths import UNSORTED, VAULT
        from odg_sorter.digest import generate_digest
        from odg_sorter.main import STATE_PATH
        from odg_sorter.state import State
        state = State(STATE_PATH)
        out = generate_digest(state=state, vault_root=VAULT, unsorted_root=UNSORTED, period_days=7)
        print(f"wrote: {out}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
