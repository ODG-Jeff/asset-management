import logging
from pathlib import Path

from odg_sorter.config.paths import UNSORTED, WATCHED_PATHS
from odg_sorter.identify import identify
from odg_sorter.state import State

log = logging.getLogger("odg_sorter.reconcile")


def reconcile(state: State) -> dict:
    """Walk watched paths + unsorted/; sort any file we haven't seen.
    Returns counts dict (suitable for logging/digest).
    """
    from odg_sorter.main import sort_one  # avoid circular at import time

    counts = {"scanned": 0, "newly_sorted": 0, "already_seen": 0}

    for root in list(WATCHED_PATHS) + [UNSORTED]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            counts["scanned"] += 1
            signals = identify(path)
            if state.find_by_hash(signals.hash_sha256) is not None:
                counts["already_seen"] += 1
                continue
            sort_one(path, state=state)
            counts["newly_sorted"] += 1

    log.info("reconcile complete %s", counts)
    return counts
