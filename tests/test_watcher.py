import threading
import time
from pathlib import Path

import pytest

from odg_sorter.watcher import Watcher


def test_watcher_emits_callback_for_new_file(tmp_path):
    seen: list[Path] = []
    done = threading.Event()

    def on_landed(p: Path) -> None:
        seen.append(p)
        done.set()

    w = Watcher(watched_paths=[tmp_path], on_landed=on_landed, debounce_seconds=0.3)
    w.start()
    try:
        (tmp_path / "foo.png").write_bytes(b"hello")
        assert done.wait(timeout=5.0), "callback was not invoked within 5s"
        assert seen == [tmp_path / "foo.png"]
    finally:
        w.stop()


def test_watcher_debounces_rapid_writes(tmp_path):
    seen: list[Path] = []
    done = threading.Event()

    def on_landed(p: Path) -> None:
        seen.append(p)
        done.set()

    w = Watcher(watched_paths=[tmp_path], on_landed=on_landed, debounce_seconds=0.5)
    w.start()
    try:
        f = tmp_path / "stream.png"
        for chunk in (b"a", b"b", b"c"):
            with f.open("ab") as fh:
                fh.write(chunk)
            time.sleep(0.05)
        assert done.wait(timeout=5.0)
        # Exactly one emission for the burst.
        time.sleep(0.6)
        assert len(seen) == 1
    finally:
        w.stop()
