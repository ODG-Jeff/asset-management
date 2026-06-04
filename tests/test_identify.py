from pathlib import Path

from odg_sorter.identify import identify

FIX = Path(__file__).parent / "fixtures"


def test_comfyui_png_extracts_workflow_and_lora():
    sig = identify(FIX / "comfyui_dhtw_sled.png")
    assert sig.tool == "comfyui"
    assert sig.extension == ".png"
    assert "dhtw-sled-v7-locked" in sig.comfyui_workflow
    assert "dhtwsprite_v1-000010" in sig.comfyui_loras
    assert sig.hash_sha256.startswith("")  # any 64-hex string
    assert len(sig.hash_sha256) == 64


def test_plain_svg_is_inkscape():
    sig = identify(FIX / "dhtw_card_001_test.svg")
    assert sig.tool == "inkscape"
    assert sig.extension == ".svg"


def test_glb_is_blender():
    sig = identify(FIX / "tll_probe_console.glb")
    assert sig.tool == "blender"
    assert sig.extension == ".glb"


def test_duplicate_fixtures_share_a_hash():
    a = identify(FIX / "dup_a.png")
    b = identify(FIX / "dup_b.png")
    assert a.hash_sha256 == b.hash_sha256


def test_unknown_extension_marks_tool_unknown(tmp_path):
    p = tmp_path / "mystery.bin"
    p.write_bytes(b"\x00" * 16)
    sig = identify(p)
    assert sig.tool == "unknown"
