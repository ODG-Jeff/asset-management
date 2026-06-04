import shutil
import threading
import time
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"


def test_daemon_routes_a_new_file(tmp_studio):
    from odg_sorter.config.paths import WATCHED_PATHS
    from odg_sorter.main import sort_one
    from odg_sorter.state import State
    from odg_sorter.watcher import Watcher

    state = State(tmp_studio["repos"].parent / "state.sqlite")
    routed = threading.Event()

    def on_landed(path: Path) -> None:
        sort_one(path, state=state)
        routed.set()

    watcher = Watcher(watched_paths=WATCHED_PATHS, on_landed=on_landed, debounce_seconds=0.3)
    watcher.start()
    try:
        target = tmp_studio["intake"] / "hull_pirate_v7_99.png"
        shutil.copy(FIX / "comfyui_dhtw_sled.png", target)
        assert routed.wait(timeout=10.0), "daemon did not route the new file within 10s"
        canonical = tmp_studio["repos"] / "dhtw" / "assets" / "sleds" / "themes" / "pirate" / "hull_pirate_v7_99.png"
        assert canonical.exists()
    finally:
        watcher.stop()
