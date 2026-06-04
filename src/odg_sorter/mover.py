import shutil
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

WIP_GUARD_SECONDS = 7 * 86400
PROTECTED_DIRS_KEY = "_protected_dirs"  # exposed for tests/inspection


@dataclass(frozen=True)
class MoveResult:
    destination: Path
    quarantined: Path | None


@dataclass(frozen=True)
class SkipResult:
    reason: str


def move_into_canonical_home(
    source: Path,
    destination: Path,
    *,
    quarantine_root: Path,
    repos_root: Path,
) -> MoveResult | SkipResult:
    source = Path(source)
    destination = Path(destination)

    # Engine-level safety: files inside repos/ are never moved.
    if _is_under(source, repos_root):
        return SkipResult(reason="source-inside-repos")

    # Identical destination = no-op.
    if destination.exists() and _files_identical(source, destination):
        return SkipResult(reason="identical-destination")

    # WIP guard: skip recent files in repo destinations.
    if (
        _is_under(destination, repos_root)
        and destination.exists()
        and (time.time() - destination.stat().st_mtime) < WIP_GUARD_SECONDS
    ):
        return SkipResult(reason="wip-protected")

    quarantined: Path | None = None
    if destination.exists():
        quarantined = _quarantine(destination, quarantine_root)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return MoveResult(destination=destination, quarantined=quarantined)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _files_identical(a: Path, b: Path) -> bool:
    if a.stat().st_size != b.stat().st_size:
        return False
    with a.open("rb") as fa, b.open("rb") as fb:
        while True:
            ca = fa.read(65536)
            cb = fb.read(65536)
            if ca != cb:
                return False
            if not ca:
                return True


def _quarantine(existing: Path, quarantine_root: Path) -> Path:
    today = date.today().isoformat()
    bucket = quarantine_root / today
    bucket.mkdir(parents=True, exist_ok=True)
    target = bucket / existing.name
    n = 1
    while target.exists():
        target = bucket / f"{existing.stem}.{n}{existing.suffix}"
        n += 1
    shutil.move(str(existing), str(target))
    return target
