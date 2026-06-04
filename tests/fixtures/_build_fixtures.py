"""Run once with `python tests/fixtures/_build_fixtures.py` to (re)generate binary fixtures."""
import json
import struct
import zlib
from pathlib import Path

from PIL import Image, PngImagePlugin

FIX = Path(__file__).parent


def _png_1x1(out: Path, text_chunks: dict[str, str] | None = None) -> None:
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    info = PngImagePlugin.PngInfo()
    for k, v in (text_chunks or {}).items():
        info.add_text(k, v)
    img.save(out, format="PNG", pnginfo=info)


def _minimal_glb(out: Path) -> None:
    # Empty-scene glTF.
    gltf = {"asset": {"version": "2.0"}, "scenes": [{"nodes": []}], "scene": 0}
    json_bytes = json.dumps(gltf).encode("utf-8")
    while len(json_bytes) % 4:
        json_bytes += b" "
    json_chunk = struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes  # JSON tag
    total = 12 + len(json_chunk)
    header = struct.pack("<III", 0x46546C67, 2, total)  # magic glTF, version 2
    out.write_bytes(header + json_chunk)


def main() -> None:
    workflow = json.dumps({
        "workflow": "dhtw-sled-v7-locked",
        "loras": ["dhtwsprite_v1-000010"],
        "model": "juggernautXL_v9",
        "seed": 1234567890,
        "prompt": "pirate sled hull, matte black with gold leaf trim",
    })
    _png_1x1(FIX / "comfyui_dhtw_sled.png", {"workflow": workflow})
    _png_1x1(FIX / "wip_file.png")
    _png_1x1(FIX / "dup_a.png", {"marker": "dup"})
    _png_1x1(FIX / "dup_b.png", {"marker": "dup"})  # same content -> same hash
    (FIX / "dhtw_card_001_test.svg").write_text(
        '<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>\n'
    )
    _minimal_glb(FIX / "tll_probe_console.glb")


if __name__ == "__main__":
    main()
