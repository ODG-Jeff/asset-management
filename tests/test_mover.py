import os
import time
from pathlib import Path

import pytest

from odg_sorter.mover import (
    MoveResult,
    SkipResult,
    move_into_canonical_home,
    PROTECTED_DIRS_KEY,
)


@pytest.fixture
def fakedirs(tmp_path):
    intake = tmp_path / "intake"
    intake.mkdir()
    dest_root = tmp_path / "repos" / "dhtw" / "assets"
    dest_root.mkdir(parents=True)
    quarantine = tmp_path / "_quarantine"
    quarantine.mkdir()
    return {
        "intake": intake,
        "repos_root": tmp_path / "repos",
        "dest_root": dest_root,
        "quarantine": quarantine,
    }


def test_clean_move_relocates_file(fakedirs):
    src = fakedirs["intake"] / "foo.png"
    src.write_bytes(b"hello")
    dest = fakedirs["dest_root"] / "foo.png"
    result = move_into_canonical_home(
        src,
        dest,
        quarantine_root=fakedirs["quarantine"],
        repos_root=fakedirs["repos_root"],
    )
    assert isinstance(result, MoveResult)
    assert not src.exists()
    assert dest.read_bytes() == b"hello"
    assert result.quarantined is None


def test_displaced_file_goes_to_quarantine(fakedirs, tmp_path):
    src = fakedirs["intake"] / "foo.png"
    src.write_bytes(b"new")
    # dest is outside repos so the WIP guard does not interfere
    dest_dir = tmp_path / "vault" / "art"
    dest_dir.mkdir(parents=True)
    dest = dest_dir / "foo.png"
    dest.write_bytes(b"old")
    result = move_into_canonical_home(
        src,
        dest,
        quarantine_root=fakedirs["quarantine"],
        repos_root=fakedirs["repos_root"],
    )
    assert dest.read_bytes() == b"new"
    assert result.quarantined is not None
    assert result.quarantined.read_bytes() == b"old"


def test_identical_destination_is_no_op(fakedirs):
    src = fakedirs["intake"] / "foo.png"
    src.write_bytes(b"same")
    dest = fakedirs["dest_root"] / "foo.png"
    dest.write_bytes(b"same")
    result = move_into_canonical_home(
        src,
        dest,
        quarantine_root=fakedirs["quarantine"],
        repos_root=fakedirs["repos_root"],
    )
    assert isinstance(result, SkipResult)
    assert result.reason == "identical-destination"
    assert src.exists()


def test_file_inside_repos_is_never_moved(fakedirs):
    src = fakedirs["repos_root"] / "dhtw" / "assets" / "foo.png"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(b"x")
    dest = fakedirs["dest_root"] / "elsewhere" / "foo.png"
    result = move_into_canonical_home(
        src,
        dest,
        quarantine_root=fakedirs["quarantine"],
        repos_root=fakedirs["repos_root"],
    )
    assert isinstance(result, SkipResult)
    assert result.reason == "source-inside-repos"
    assert src.exists()


def test_wip_guard_skips_recent_repo_destination(fakedirs):
    src = fakedirs["intake"] / "foo.png"
    src.write_bytes(b"new")
    dest = fakedirs["dest_root"] / "foo.png"
    dest.write_bytes(b"wip")
    now = time.time()
    os.utime(dest, (now, now))  # mtime = now (definitely <7d old)
    result = move_into_canonical_home(
        src,
        dest,
        quarantine_root=fakedirs["quarantine"],
        repos_root=fakedirs["repos_root"],
    )
    assert isinstance(result, SkipResult)
    assert result.reason == "wip-protected"
    assert src.exists()
    assert dest.read_bytes() == b"wip"


def test_wip_guard_does_not_skip_old_destination(fakedirs):
    src = fakedirs["intake"] / "foo.png"
    src.write_bytes(b"new")
    dest = fakedirs["dest_root"] / "foo.png"
    dest.write_bytes(b"old-wip")
    # 30 days ago
    ancient = time.time() - (30 * 86400)
    os.utime(dest, (ancient, ancient))
    result = move_into_canonical_home(
        src,
        dest,
        quarantine_root=fakedirs["quarantine"],
        repos_root=fakedirs["repos_root"],
    )
    assert isinstance(result, MoveResult)
    assert dest.read_bytes() == b"new"
