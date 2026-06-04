import shutil
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"


def _sort(path: Path, *, tmp_studio):
    from odg_sorter.main import sort_one, STATE_PATH
    from odg_sorter.state import State
    # Use tmp state file inside the studio root.
    state = State(tmp_studio["repos"].parent / "state.sqlite")
    return sort_one(path, state=state), state


def test_dhtw_sled_themed_v7_end_to_end(tmp_studio):
    src = tmp_studio["intake"] / "hull_pirate_v7_05.png"
    shutil.copy(FIX / "comfyui_dhtw_sled.png", src)
    outcome, _ = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "routed"
    expected = tmp_studio["repos"] / "dhtw" / "assets" / "sleds" / "themes" / "pirate" / "hull_pirate_v7_05.png"
    assert expected.exists()
    sidecar = tmp_studio["vault"] / "Opal Dragonfly Games" / "Projects" / "DHTW" / "Assets" / "hull_pirate_v7_05.md"
    assert sidecar.exists()


def test_dhtw_card_front_end_to_end(tmp_studio):
    src = tmp_studio["intake"] / "card_007_assist_recover.png"
    shutil.copy(FIX / "wip_file.png", src)  # plain PNG; filename pattern triggers the rule
    outcome, _ = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "routed"
    assert (tmp_studio["repos"] / "dhtw-tabletop" / "components" / "cards" / "fronts" / "card_007_assist_recover.png").exists()


def test_tgc_component_svg_end_to_end(tmp_studio):
    src = tmp_studio["intake"] / "card_back_master.svg"
    shutil.copy(FIX / "dhtw_card_001_test.svg", src)
    outcome, _ = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "routed"
    assert (tmp_studio["repos"] / "dhtw-tabletop" / "components" / "cards" / "card_back_master.svg").exists()


def test_tll_glb_export_by_directory_signal(tmp_studio):
    sub = tmp_studio["repos"].parent / "generated" / "tll" / "hub"
    sub.mkdir(parents=True, exist_ok=True)
    src = sub / "console_smoke_v2.glb"
    shutil.copy(FIX / "tll_probe_console.glb", src)
    outcome, _ = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "routed"
    assert (tmp_studio["repos"] / "tll" / "client" / "assets" / "3d" / "console" / "console_smoke_v2.glb").exists()


def test_dhtw_glb_export_by_filename_signal(tmp_studio):
    src = tmp_studio["intake"] / "sled_pirate_proto.glb"
    shutil.copy(FIX / "tll_probe_console.glb", src)
    outcome, _ = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "routed"
    assert (tmp_studio["repos"] / "dhtw" / "client" / "assets" / "3d" / "sled" / "sled_pirate_proto.glb").exists()


def test_arlo_voice_routes_by_filename(tmp_studio):
    src = tmp_studio["intake"] / "taunt_017_rude.wav"
    src.write_bytes(b"RIFF" + b"\x00" * 40)
    outcome, _ = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "routed"
    assert (tmp_studio["repos"] / "dhtw" / "client" / "assets" / "audio" / "arlo" / "taunt_017_rude.wav").exists()


def test_fallback_park_for_unknown_file(tmp_studio):
    src = tmp_studio["intake"] / "mystery.bin"
    src.write_bytes(b"\x00" * 16)
    outcome, state = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "parked"


def test_idempotent_repeat_sort(tmp_studio):
    src = tmp_studio["intake"] / "hull_pirate_v7_06.png"
    shutil.copy(FIX / "comfyui_dhtw_sled.png", src)
    first, state = _sort(src, tmp_studio=tmp_studio)
    assert first == "routed"
    # File is already at canonical home now. Re-route should be no-op via "already-seen".
    canonical = tmp_studio["repos"] / "dhtw" / "assets" / "sleds" / "themes" / "pirate" / "hull_pirate_v7_06.png"
    assert canonical.exists()
    from odg_sorter.main import sort_one
    again = sort_one(canonical, state=state)
    assert again == "already-seen"


def test_dedup_quarantines_second_copy(tmp_studio):
    a = tmp_studio["intake"] / "hull_pirate_v7_07.png"
    shutil.copy(FIX / "comfyui_dhtw_sled.png", a)
    _sort(a, tmp_studio=tmp_studio)
    b = tmp_studio["intake"] / "hull_pirate_v7_07_copy.png"
    shutil.copy(FIX / "comfyui_dhtw_sled.png", b)
    outcome, _ = _sort(b, tmp_studio=tmp_studio)
    assert outcome == "already-seen"


def test_wip_guard_protects_recent_repo_file(tmp_studio):
    canonical = tmp_studio["repos"] / "dhtw" / "assets" / "sleds" / "themes" / "pirate" / "hull_pirate_v7_05.png"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(b"wip")
    src = tmp_studio["intake"] / "hull_pirate_v7_05.png"
    shutil.copy(FIX / "comfyui_dhtw_sled.png", src)
    outcome, _ = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "wip-protected"
    assert canonical.read_bytes() == b"wip"


def test_parked_file_is_actually_moved_to_unsorted(tmp_studio):
    src = tmp_studio["intake"] / "mystery.bin"
    src.write_bytes(b"\x00" * 16)
    outcome, _ = _sort(src, tmp_studio=tmp_studio)
    assert outcome == "parked"
    assert not src.exists(), "park branch left the file in the intake dir"
    # Find it in unsorted/<date>/
    matches = list(tmp_studio["unsorted"].rglob("mystery.bin"))
    assert len(matches) == 1, f"expected file at unsorted/<date>/mystery.bin, found {matches}"


def test_file_already_at_canonical_home_gets_sidecar(tmp_studio):
    # Simulates a Blender script writing directly to repos/<project>/...
    # Sort_one should detect this and still write the vault sidecar.
    # Filename matches THEME_RE so the router lands on the same canonical path.
    canonical = tmp_studio["repos"] / "dhtw" / "assets" / "sleds" / "themes" / "pirate" / "hull_pirate_v8_01.png"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / "comfyui_dhtw_sled.png", canonical)
    # Backdate so WIP guard doesn't fire.
    import os
    ancient = __import__("time").time() - (30 * 86400)
    os.utime(canonical, (ancient, ancient))
    outcome, _ = _sort(canonical, tmp_studio=tmp_studio)
    assert outcome == "routed", f"expected in-place routing, got {outcome}"
    sidecar = tmp_studio["vault"] / "Opal Dragonfly Games" / "Projects" / "DHTW" / "Assets" / "hull_pirate_v8_01.md"
    assert sidecar.exists(), "in-place file did not get a vault sidecar"
    # File must remain at canonical home.
    assert canonical.exists()
