from pathlib import Path

from odg_sorter.identify import Signals
from odg_sorter.router import route, Park, Route


def _sig(**overrides) -> Signals:
    base = dict(
        path=Path("C:/_intake/foo.png"),
        filename="foo.png",
        extension=".png",
        size_bytes=1234,
        hash_sha256="0" * 64,
        tool="comfyui",
    )
    base.update(overrides)
    return Signals(**base)


def test_dhtw_sled_themed_v7_matches_comfyui_with_dhtwsprite():
    s = _sig(
        comfyui_loras=("dhtwsprite_v1-000010",),
        comfyui_workflow='{"workflow":"dhtw-sled-v7-locked"}',
        filename="hull_pirate_v7_05.png",
    )
    result = route(s)
    assert isinstance(result, Route)
    assert result.rule == "dhtw-sled-themed-v7"
    assert "sleds/themes/pirate" in str(result.destination).replace("\\", "/")


def test_dhtw_card_front_matches_numbered_card_png():
    s = _sig(filename="card_007_assist_recover.png", path=Path("C:/_intake/card_007_assist_recover.png"))
    result = route(s)
    assert isinstance(result, Route)
    assert result.rule == "dhtw-card-front"


def test_unknown_file_parks_fallback():
    s = _sig(filename="random.bin", extension=".bin", tool="unknown")
    result = route(s)
    assert isinstance(result, Park)
    assert result.rule == "fallback-park"


def test_glb_in_tll_generated_routes_to_tll_3d():
    s = _sig(
        path=Path(r"C:\ODG\generated\tll\hub\console_smoke_v1.glb"),
        filename="console_smoke_v1.glb",
        extension=".glb",
        tool="blender",
    )
    result = route(s)
    assert isinstance(result, Route)
    assert result.rule == "tll-glb-export"
    assert "tll/client/assets/3d" in str(result.destination).replace("\\", "/")
