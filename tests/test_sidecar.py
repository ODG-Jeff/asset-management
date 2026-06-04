from datetime import datetime
from pathlib import Path

import pytest
import yaml

from odg_sorter.sidecar import write_sidecar, SidecarContext


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    return v


def _ctx(**over) -> SidecarContext:
    base = dict(
        template="dhtw-sled.md.j2",
        sidecar_path=Path("vault/Opal Dragonfly Games/Projects/DHTW/Assets/hull_pirate_v7_05.md"),
        data=dict(
            asset="hull_pirate_v7_05.png",
            theme="pirate",
            source_tool="comfyui",
            workflow="dhtw-sled-v7-locked",
            model="juggernautXL_v9",
            seed="1234567890",
            prompt="pirate sled hull",
            hash="abc",
            size="[1024, 1024]",
            mime="image/png",
            ingested=datetime(2026, 6, 4, 14, 23, 11).isoformat(),
            rule="dhtw-sled-themed-v7",
            canonical_path=r"C:\ODG\repos\dhtw\assets\sleds\themes\pirate\hull_pirate_v7_05.png",
            ingested_from=r"C:\ODG\_intake\hull_pirate_v7_05.png",
        ),
    )
    base.update(over)
    return SidecarContext(**base)


def test_sidecar_written_with_expected_frontmatter(vault):
    ctx = _ctx(sidecar_path=vault / "test.md")
    write_sidecar(ctx)
    text = (vault / "test.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    front, _ = text.split("\n---\n", 1)
    meta = yaml.safe_load(front[4:])  # strip leading "---\n"
    assert meta["asset"] == "hull_pirate_v7_05.png"
    assert meta["theme"] == "pirate"
    assert meta["sorter-rule"] == "dhtw-sled-themed-v7"
    assert "project/dhtw" in meta["tags"]


def test_sidecar_preserves_body_below_embed_on_rewrite(vault):
    ctx = _ctx(sidecar_path=vault / "test.md")
    write_sidecar(ctx)
    # Simulate a human edit below the embed.
    text = (vault / "test.md").read_text(encoding="utf-8")
    text += "\n## My notes\n\nThis is the matte black pirate sled with extra flair.\n"
    (vault / "test.md").write_text(text, encoding="utf-8")
    # Re-route → re-render. Body must survive.
    write_sidecar(ctx)
    after = (vault / "test.md").read_text(encoding="utf-8")
    assert "This is the matte black pirate sled" in after
