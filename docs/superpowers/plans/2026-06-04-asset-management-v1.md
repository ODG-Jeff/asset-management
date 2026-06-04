# Asset Management v1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `odg-sorter` — a Python daemon that watches inflow paths, routes new generated assets into project-repo canonical homes, and writes Obsidian vault sidecars as the find-layer. Forward-only.

**Architecture:** Single Python process. `watchdog` for file events with a 2s debounce. Rules engine (Python dict in `config/rules.py`) drives routing. SQLite for state and SHA-256-based dedup. Jinja2 for sidecar templates. Reconciliation pass on startup closes any gap from unclean shutdowns. Files inside `repos/<project>/` are never moved.

**Tech Stack:** Python 3.11+, `watchdog`, `Pillow`, `Jinja2`, `pytest`. stdlib for SQLite, hashing, signal handling. GitHub Actions for CI.

**Spec:** `docs/superpowers/specs/2026-06-04-asset-management-v1-design.md` (commit `e8c91ca`)

---

## File Structure

```
asset-management/
├── pyproject.toml                          # package + CLI entry point
├── README.md                               # quick-start
├── CLAUDE.md                               # already exists; updated in Task 19
├── .github/workflows/ci.yml                # pytest on push/PR (Task 16)
├── src/odg_sorter/
│   ├── __init__.py                         # version string
│   ├── __main__.py                         # `python -m odg_sorter` -> cli.main
│   ├── cli.py                              # argparse + verb dispatch
│   ├── main.py                             # daemon entry + signal handling
│   ├── watcher.py                          # watchdog event loop + debounce
│   ├── identify.py                         # signal extraction (Pillow + os.stat)
│   ├── router.py                           # apply rules to signals
│   ├── mover.py                            # atomic move + quarantine + WIP guard
│   ├── sidecar.py                          # Jinja2 render + vault write
│   ├── state.py                            # SQLite wrapper + heartbeat
│   ├── digest.py                           # weekly vault note generation
│   ├── reconcile.py                        # startup pass
│   └── config/
│       ├── __init__.py
│       ├── paths.py                        # watched paths, destination roots
│       └── rules.py                        # 10 routing rules
├── src/odg_sorter/templates/sidecars/      # packaged with the wheel
│   ├── dhtw-sled.md.j2
│   ├── dhtw-card.md.j2
│   ├── dhtw-arlo-voice.md.j2
│   ├── tgc-component.md.j2
│   ├── tll-comfyui.md.j2
│   ├── tll-glb.md.j2
│   ├── dhtw-glb.md.j2
│   ├── blender-source.md.j2
│   └── digest.md.j2
├── tests/
│   ├── conftest.py                         # tmp_vault, tmp_repos fixtures
│   ├── fixtures/
│   │   ├── comfyui_dhtw_sled.png           # 1x1 PNG + crafted tEXt chunk
│   │   ├── tll_probe_console.glb           # minimal valid glTF
│   │   ├── dhtw_card_001_test.svg
│   │   ├── wip_file.png                    # for WIP guard test
│   │   ├── dup_a.png
│   │   └── dup_b.png
│   ├── test_identify.py
│   ├── test_router.py
│   ├── test_state.py
│   ├── test_sidecar.py
│   ├── test_mover.py
│   ├── test_integration.py                 # one test per routing rule
│   └── test_smoke.py                       # daemon-in-thread
└── scripts/
    ├── install_task_scheduler.ps1          # register at-logon task
    └── Audit-ODGFiles.ps1                  # already exists; untouched
```

**Vault additions** (not in the repo):

```
ODG_Vault/Opal Dragonfly Games/
├── Projects/DHTW/Assets/                   # sidecars land here (sorter creates dir)
├── Projects/TLL/Assets/                    # sidecars land here (sorter creates dir)
└── Resources/Asset Gallery/
    ├── By-Tool.md                          # Dataview query (Task 17)
    ├── By-Project.md
    ├── By-Tier.md
    └── Recent.md
```

---

## Tasks

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/odg_sorter/__init__.py`
- Create: `src/odg_sorter/__main__.py`
- Create: `src/odg_sorter/cli.py` (stub)
- Create: `tests/__init__.py`
- Modify: `.gitignore` (add `dist/`, `*.egg-info`, `__pycache__/`, `.pytest_cache/`, `data/`)

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "odg-sorter"
version = "0.1.0"
description = "Asset sorter for the ODG studio."
requires-python = ">=3.11"
dependencies = [
    "watchdog>=4",
    "Pillow>=10",
    "Jinja2>=3",
]

[project.optional-dependencies]
dev = ["pytest>=8"]

[project.scripts]
odg-sorter = "odg_sorter.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
odg_sorter = ["templates/sidecars/*.j2"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Write package `__init__.py`**

`src/odg_sorter/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Write `__main__.py`**

`src/odg_sorter/__main__.py`:

```python
from odg_sorter.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Write CLI stub**

`src/odg_sorter/cli.py`:

```python
import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="odg-sorter")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("daemon")
    sub.add_parser("sort").add_argument("path")
    sub.add_parser("digest").add_argument("--since", default=None)
    sub.add_parser("reconcile")
    args = parser.parse_args(argv)
    # Verb handlers wired in later tasks.
    print(f"odg-sorter: cmd={args.cmd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Update `.gitignore`**

Append:

```
dist/
*.egg-info/
__pycache__/
.pytest_cache/
data/
```

- [ ] **Step 6: Create `tests/__init__.py`** (empty file)

- [ ] **Step 7: Install in editable mode and smoke-check**

Run: `pip install -e .[dev]`
Run: `odg-sorter daemon`
Expected: prints `odg-sorter: cmd=daemon`, returns 0.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml src/ tests/__init__.py .gitignore
git commit -m "scaffold odg-sorter package"
```

---

### Task 2: State layer (SQLite schema, hash index, route history)

**Files:**
- Create: `src/odg_sorter/state.py`
- Create: `tests/test_state.py`

State stores: (a) every file hash we've seen, (b) every routing event (where the file came from, where it went, which rule, when), (c) the heartbeat for liveness checks. Schema is denormalized for simplicity; we're never going to have a million rows.

- [ ] **Step 1: Write the failing tests**

`tests/test_state.py`:

```python
from pathlib import Path

import pytest

from odg_sorter.state import State


@pytest.fixture
def state(tmp_path) -> State:
    return State(tmp_path / "state.sqlite")


def test_hash_unknown_returns_none(state):
    assert state.find_by_hash("abc") is None


def test_record_route_then_lookup(state):
    state.record_route(
        hash_="abc",
        source=Path("C:/intake/foo.png"),
        destination=Path("C:/repos/dhtw/foo.png"),
        rule="dhtw-sled",
    )
    row = state.find_by_hash("abc")
    assert row.rule == "dhtw-sled"
    assert row.destination == Path("C:/repos/dhtw/foo.png")


def test_record_park_no_destination(state):
    state.record_park(hash_="def", source=Path("C:/intake/odd.glb"), reason="no-project-hint")
    row = state.find_by_hash("def")
    assert row.rule == "park"
    assert row.destination is None
    assert row.reason == "no-project-hint"


def test_heartbeat_round_trip(state):
    state.write_heartbeat(events_processed=42)
    hb = state.read_heartbeat()
    assert hb.events_processed == 42
    assert hb.timestamp is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_state.py -v`
Expected: FAIL with `ImportError: cannot import name 'State'`

- [ ] **Step 3: Implement `state.py`**

`src/odg_sorter/state.py`:

```python
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS routes (
    hash         TEXT PRIMARY KEY,
    source       TEXT NOT NULL,
    destination  TEXT,
    rule         TEXT NOT NULL,
    reason       TEXT,
    ts           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS also_ingested (
    hash         TEXT NOT NULL,
    source       TEXT NOT NULL,
    ts           TEXT NOT NULL,
    PRIMARY KEY (hash, source)
);
CREATE TABLE IF NOT EXISTS heartbeat (
    id               INTEGER PRIMARY KEY CHECK (id = 1),
    ts               TEXT NOT NULL,
    events_processed INTEGER NOT NULL
);
"""


@dataclass(frozen=True)
class RouteRow:
    hash: str
    source: Path
    destination: Path | None
    rule: str
    reason: str | None
    ts: datetime


@dataclass(frozen=True)
class Heartbeat:
    timestamp: datetime
    events_processed: int


class State:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, isolation_level=None)
        self._conn.executescript(SCHEMA)

    def find_by_hash(self, hash_: str) -> RouteRow | None:
        cur = self._conn.execute(
            "SELECT hash, source, destination, rule, reason, ts FROM routes WHERE hash = ?",
            (hash_,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        h, src, dst, rule, reason, ts = row
        return RouteRow(
            hash=h,
            source=Path(src),
            destination=Path(dst) if dst else None,
            rule=rule,
            reason=reason,
            ts=datetime.fromisoformat(ts),
        )

    def record_route(self, hash_: str, source: Path, destination: Path, rule: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO routes (hash, source, destination, rule, reason, ts) "
            "VALUES (?, ?, ?, ?, NULL, ?)",
            (hash_, str(source), str(destination), rule, _now_iso()),
        )

    def record_park(self, hash_: str, source: Path, reason: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO routes (hash, source, destination, rule, reason, ts) "
            "VALUES (?, ?, NULL, 'park', ?, ?)",
            (hash_, str(source), reason, _now_iso()),
        )

    def record_also_ingested(self, hash_: str, source: Path) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO also_ingested (hash, source, ts) VALUES (?, ?, ?)",
            (hash_, str(source), _now_iso()),
        )

    def write_heartbeat(self, events_processed: int) -> None:
        self._conn.execute(
            "INSERT INTO heartbeat (id, ts, events_processed) VALUES (1, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET ts = excluded.ts, events_processed = excluded.events_processed",
            (_now_iso(), events_processed),
        )

    def read_heartbeat(self) -> Heartbeat | None:
        cur = self._conn.execute("SELECT ts, events_processed FROM heartbeat WHERE id = 1")
        row = cur.fetchone()
        if row is None:
            return None
        ts, ev = row
        return Heartbeat(timestamp=datetime.fromisoformat(ts), events_processed=ev)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_state.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/odg_sorter/state.py tests/test_state.py
git commit -m "add state layer (SQLite hash index + route history + heartbeat)"
```

---

### Task 3: Signal extraction (`identify.py`)

**Files:**
- Create: `src/odg_sorter/identify.py`
- Create: `tests/test_identify.py`
- Create: `tests/fixtures/comfyui_dhtw_sled.png` (1×1 PNG + tEXt chunk)
- Create: `tests/fixtures/dhtw_card_001_test.svg`
- Create: `tests/fixtures/wip_file.png`
- Create: `tests/fixtures/dup_a.png`, `tests/fixtures/dup_b.png` (identical content)
- Create: `tests/fixtures/tll_probe_console.glb` (minimal valid glTF binary)

`identify.py` returns a `Signals` dataclass populated from filename, path, size, mime, and (for PNGs) ComfyUI text chunks.

- [ ] **Step 1: Generate fixtures**

Create `tests/fixtures/_build_fixtures.py` (a one-shot helper, **not** part of the test suite):

```python
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
```

Run: `python tests/fixtures/_build_fixtures.py`
Expected: 6 fixture files created.

- [ ] **Step 2: Write the failing tests**

`tests/test_identify.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_identify.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 4: Implement `identify.py`**

`src/odg_sorter/identify.py`:

```python
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

_TOOL_BY_EXT = {
    ".png": "comfyui",      # default; refined by metadata below
    ".jpg": "comfyui",
    ".jpeg": "comfyui",
    ".webp": "comfyui",
    ".svg": "inkscape",
    ".glb": "blender",
    ".gltf": "blender",
    ".fbx": "blender",
    ".obj": "blender",
    ".blend": "blender",
    ".wav": "audio",
    ".mp3": "audio",
    ".flac": "audio",
}


@dataclass(frozen=True)
class Signals:
    path: Path
    filename: str
    extension: str
    size_bytes: int
    hash_sha256: str
    tool: str
    comfyui_workflow: str = ""
    comfyui_loras: tuple[str, ...] = ()
    comfyui_model: str = ""
    comfyui_seed: str = ""
    comfyui_prompt: str = ""
    extras: dict[str, str] = field(default_factory=dict)


def identify(path: Path) -> Signals:
    path = Path(path)
    ext = path.suffix.lower()
    size = path.stat().st_size
    hash_ = _sha256_of(path)

    tool = _TOOL_BY_EXT.get(ext, "unknown")
    workflow = loras = model = seed = prompt = ""
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        text = _extract_png_text(path)
        if text:
            tool = "comfyui"
            workflow = text.get("workflow", "")
            loras = _extract_field(workflow, "loras")
            model = _extract_field(workflow, "model")
            seed = _extract_field(workflow, "seed")
            prompt = _extract_field(workflow, "prompt")
        else:
            tool = "image"  # PNG with no metadata isn't necessarily ComfyUI

    return Signals(
        path=path,
        filename=path.name,
        extension=ext,
        size_bytes=size,
        hash_sha256=hash_,
        tool=tool,
        comfyui_workflow=workflow,
        comfyui_loras=tuple(loras) if isinstance(loras, list) else (),
        comfyui_model=model if isinstance(model, str) else "",
        comfyui_seed=str(seed) if seed else "",
        comfyui_prompt=prompt if isinstance(prompt, str) else "",
    )


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_png_text(path: Path) -> dict[str, str]:
    try:
        with Image.open(path) as img:
            text = dict(getattr(img, "text", {}) or {})
            text.update(getattr(img, "info", {}) or {})
            return {k: v for k, v in text.items() if isinstance(v, str)}
    except Exception:
        return {}


def _extract_field(workflow_json_str: str, key: str):
    import json
    try:
        data = json.loads(workflow_json_str)
        return data.get(key, "")
    except Exception:
        return ""
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_identify.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add src/odg_sorter/identify.py tests/test_identify.py tests/fixtures/
git commit -m "add signal extraction (PNG metadata + filename/ext + SHA-256)"
```

---

### Task 4: Config — watched paths and destination roots (`config/paths.py`)

**Files:**
- Create: `src/odg_sorter/config/__init__.py` (empty)
- Create: `src/odg_sorter/config/paths.py`

Data-only. Lives in `config/` so it's the single place to edit when a path changes.

- [ ] **Step 1: Write `paths.py`**

`src/odg_sorter/config/paths.py`:

```python
"""Watched directories and destination roots. Data-only — edit this file to change paths."""
from pathlib import Path

# The studio root. Everything under here.
STUDIO_ROOT = Path(r"C:\ODG")

# Inflow: what the watcher tails.
WATCHED_PATHS: tuple[Path, ...] = (
    STUDIO_ROOT / "_intake",
    # ComfyUI output directory. UPDATE when the actual ComfyUI install path is confirmed.
    STUDIO_ROOT / "generated" / "comfyui_output",
)

# Destination roots used by rules. Keep names stable — rule destinations reference these.
REPOS = STUDIO_ROOT / "repos"
VAULT = STUDIO_ROOT / "ODG_Vault"
QUARANTINE = STUDIO_ROOT / "_quarantine"
UNSORTED = STUDIO_ROOT / "_intake" / "unsorted"

# Vault PARA roots.
VAULT_PROJECTS = VAULT / "Opal Dragonfly Games" / "Projects"
VAULT_GALLERY = VAULT / "Opal Dragonfly Games" / "Resources" / "Asset Gallery"

# Per-project shorthand used by rules.
DHTW_REPO = REPOS / "dhtw"
DHTW_TABLETOP_REPO = REPOS / "dhtw-tabletop"
TLL_REPO = REPOS / "tll"
```

- [ ] **Step 2: Commit**

```bash
git add src/odg_sorter/config/
git commit -m "add config/paths.py — watched paths and destination roots"
```

---

### Task 5: Config — routing rules (`config/rules.py`) + router (`router.py`)

**Files:**
- Create: `src/odg_sorter/config/rules.py`
- Create: `src/odg_sorter/router.py`
- Create: `tests/test_router.py`

Rules are a list of dicts. First-match-wins. Each rule has a `match(signals) -> bool` predicate, a `destination` callable returning a Path, a sidecar template name, and a confidence.

- [ ] **Step 1: Write the failing tests**

`tests/test_router.py`:

```python
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
    assert "sleds/themes/pirate" in str(result.destination)


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_router.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `router.py`**

`src/odg_sorter/router.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from odg_sorter.config.rules import RULES, RuleResult
from odg_sorter.identify import Signals


@dataclass(frozen=True)
class Route:
    rule: str
    destination: Path
    sidecar_template: str
    confidence: str


@dataclass(frozen=True)
class Park:
    rule: str
    destination: Path
    reason: str


def route(signals: Signals) -> Route | Park:
    for rule in RULES:
        result: RuleResult | None = rule["match"](signals)
        if result is None:
            continue
        if result.kind == "route":
            return Route(
                rule=rule["name"],
                destination=result.destination,
                sidecar_template=rule["sidecar_template"],
                confidence=rule["confidence"],
            )
        return Park(rule=rule["name"], destination=result.destination, reason=result.reason)
    raise RuntimeError("rules list has no fallback — fix config/rules.py")
```

- [ ] **Step 4: Implement `config/rules.py`**

`src/odg_sorter/config/rules.py`:

```python
"""Routing rules. First-match-wins. Add new rules at the top of their project block.

Each rule is a dict:
    name: str                 — logged on every match
    match: Callable[[Signals], RuleResult | None]
                              — return None to skip; RuleResult to claim
    sidecar_template: str | None  — Jinja2 template basename; None for park
    confidence: str           — 'high' | 'low' | 'none'
"""
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from odg_sorter.config.paths import (
    DHTW_REPO,
    DHTW_TABLETOP_REPO,
    TLL_REPO,
    UNSORTED,
)
from odg_sorter.identify import Signals


@dataclass(frozen=True)
class RuleResult:
    kind: str  # "route" | "park"
    destination: Path
    reason: str = ""


# -------- Helpers --------

THEME_RE = re.compile(r"^[a-z]+_(?P<theme>[a-z]+)_v\d+_\d+\.png$", re.IGNORECASE)


def _detect_theme(filename: str) -> str | None:
    m = THEME_RE.match(filename)
    return m.group("theme").lower() if m else None


def _route(dest: Path) -> RuleResult:
    return RuleResult(kind="route", destination=dest)


def _park(reason: str) -> RuleResult:
    return RuleResult(kind="park", destination=UNSORTED / date.today().isoformat(), reason=reason)


# -------- Rules --------

def _match_dhtw_sled_themed_v7(s: Signals) -> RuleResult | None:
    if s.tool != "comfyui":
        return None
    if not any("dhtwsprite" in lora.lower() for lora in s.comfyui_loras):
        return None
    theme = _detect_theme(s.filename) or "uncategorized"
    return _route(DHTW_REPO / "assets" / "sleds" / "themes" / theme / s.filename)


def _match_dhtw_card_front(s: Signals) -> RuleResult | None:
    if not re.match(r"^card_\d{3}_.+\.png$", s.filename, re.IGNORECASE):
        return None
    return _route(DHTW_TABLETOP_REPO / "components" / "cards" / "fronts" / s.filename)


def _match_dhtw_arlo_voice(s: Signals) -> RuleResult | None:
    if not re.match(r"^taunt_\d+.*\.(wav|mp3|flac)$", s.filename, re.IGNORECASE):
        return None
    return _route(DHTW_REPO / "client" / "assets" / "audio" / "arlo" / s.filename)


def _match_tgc_component_svg(s: Signals) -> RuleResult | None:
    if s.extension != ".svg":
        return None
    m = re.match(r"^(card|chit|token|board|box)_.*\.svg$", s.filename, re.IGNORECASE)
    if not m:
        return None
    component_type = m.group(1).lower() + "s"
    return _route(DHTW_TABLETOP_REPO / "components" / component_type / s.filename)


def _match_tll_comfyui(s: Signals) -> RuleResult | None:
    if s.tool != "comfyui":
        return None
    wf = s.comfyui_workflow.lower()
    if not any(tag in wf for tag in ("tll", "probe", "the-last-light")):
        return None
    system = _system_hint(s.filename) or "uncategorized"
    return _route(TLL_REPO / "client" / "assets" / "generated" / system / s.filename)


def _match_tll_glb_export(s: Signals) -> RuleResult | None:
    if s.extension != ".glb":
        return None
    p = str(s.path).replace("\\", "/").lower()
    if "/generated/tll/" not in p and not re.match(r"^(probe|console|hub)_", s.filename, re.IGNORECASE):
        return None
    system = _system_hint(s.filename) or "uncategorized"
    return _route(TLL_REPO / "client" / "assets" / "3d" / system / s.filename)


def _match_dhtw_glb_export(s: Signals) -> RuleResult | None:
    if s.extension != ".glb":
        return None
    p = str(s.path).replace("\\", "/").lower()
    if "/generated/dhtw/" not in p and not re.match(r"^(sled|wall|arlo)_", s.filename, re.IGNORECASE):
        return None
    system = _system_hint(s.filename) or "uncategorized"
    return _route(DHTW_REPO / "client" / "assets" / "3d" / system / s.filename)


def _match_blender_source(s: Signals) -> RuleResult | None:
    if s.extension != ".blend":
        return None
    project = _project_hint(s.filename)
    if not project:
        return _park("blend-file-without-project-hint")
    return _route(_repo_for(project) / "blender" / s.filename)


def _match_fallback_park(_s: Signals) -> RuleResult:
    return _park("no-rule-matched")


def _system_hint(filename: str) -> str | None:
    m = re.match(r"^([a-z]+)_", filename, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _project_hint(filename: str) -> str | None:
    n = filename.lower()
    if "dhtw" in n or "sled" in n or "arlo" in n or "wall" in n:
        return "dhtw"
    if "tll" in n or "probe" in n or "console" in n:
        return "tll"
    return None


def _repo_for(project: str) -> Path:
    return {"dhtw": DHTW_REPO, "tll": TLL_REPO, "dhtw-tabletop": DHTW_TABLETOP_REPO}[project]


RULES = [
    {"name": "dhtw-sled-themed-v7",  "match": _match_dhtw_sled_themed_v7,  "sidecar_template": "dhtw-sled.md.j2",       "confidence": "high"},
    {"name": "dhtw-card-front",      "match": _match_dhtw_card_front,      "sidecar_template": "dhtw-card.md.j2",       "confidence": "high"},
    {"name": "dhtw-arlo-voice",      "match": _match_dhtw_arlo_voice,      "sidecar_template": "dhtw-arlo-voice.md.j2", "confidence": "high"},
    {"name": "tgc-component-svg",    "match": _match_tgc_component_svg,    "sidecar_template": "tgc-component.md.j2",   "confidence": "high"},
    {"name": "tll-comfyui",          "match": _match_tll_comfyui,          "sidecar_template": "tll-comfyui.md.j2",     "confidence": "high"},
    {"name": "tll-glb-export",       "match": _match_tll_glb_export,       "sidecar_template": "tll-glb.md.j2",         "confidence": "high"},
    {"name": "dhtw-glb-export",      "match": _match_dhtw_glb_export,      "sidecar_template": "dhtw-glb.md.j2",        "confidence": "high"},
    {"name": "blender-source-file",  "match": _match_blender_source,       "sidecar_template": "blender-source.md.j2",  "confidence": "high"},
    {"name": "fallback-park",        "match": _match_fallback_park,        "sidecar_template": None,                    "confidence": "none"},
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_router.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add src/odg_sorter/router.py src/odg_sorter/config/rules.py tests/test_router.py
git commit -m "add router + 9 routing rules (8 high-confidence + park fallback)"
```

---

### Task 6: Mover — atomic move, quarantine, WIP guard (`mover.py`)

**Files:**
- Create: `src/odg_sorter/mover.py`
- Create: `tests/test_mover.py`

The mover is where the hard rules live: never delete (displaced files go to `_quarantine/`), never move files inside `repos/` (engine-level safety rule from the spec), skip files <7 days old in repo trees (WIP guard).

- [ ] **Step 1: Write the failing tests**

`tests/test_mover.py`:

```python
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


def test_displaced_file_goes_to_quarantine(fakedirs):
    src = fakedirs["intake"] / "foo.png"
    src.write_bytes(b"new")
    dest = fakedirs["dest_root"] / "foo.png"
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_mover.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `mover.py`**

`src/odg_sorter/mover.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_mover.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/odg_sorter/mover.py tests/test_mover.py
git commit -m "add mover (atomic move + quarantine + WIP guard + repos safety)"
```

---

### Task 7: Sidecar renderer (`sidecar.py`) + first template

**Files:**
- Create: `src/odg_sorter/sidecar.py`
- Create: `src/odg_sorter/templates/sidecars/dhtw-sled.md.j2`
- Create: `tests/test_sidecar.py`

`sidecar.py` loads templates from the packaged `templates/sidecars/` dir, renders with Jinja2, and writes atomically to the vault path.

- [ ] **Step 1: Write the first template**

`src/odg_sorter/templates/sidecars/dhtw-sled.md.j2`:

```jinja2
---
asset: {{ asset }}
project: dhtw
theme: {{ theme }}
source-tool: {{ source_tool }}
workflow: {{ workflow }}
model: {{ model }}
seed: {{ seed }}
prompt: |
  {{ prompt | indent(2) }}
hash: sha256:{{ hash }}
size: {{ size }}
mime: {{ mime }}
ingested: {{ ingested }}
sorter-rule: {{ rule }}
canonical-path: {{ canonical_path }}
ingested-from: {{ ingested_from }}
tags: [asset/image, project/dhtw, theme/{{ theme }}, workflow/{{ workflow }}, tool/comfyui]
---

![[_repos/dhtw/assets/sleds/themes/{{ theme }}/{{ asset }}]]

# {{ asset }}

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

- [ ] **Step 2: Write the failing tests**

`tests/test_sidecar.py`:

```python
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
```

(Add `PyYAML>=6` to `[project.optional-dependencies].dev` in `pyproject.toml` for the test parser.)

- [ ] **Step 3: Run tests to verify they fail**

Run: `pip install -e .[dev]` (re-install for the PyYAML addition).
Run: `pytest tests/test_sidecar.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 4: Implement `sidecar.py`**

`src/odg_sorter/sidecar.py`:

```python
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = files("odg_sorter.templates.sidecars")
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(disabled_extensions=("j2",), default=False),
    keep_trailing_newline=True,
)

_BODY_SEPARATOR = "<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->"


@dataclass(frozen=True)
class SidecarContext:
    template: str
    sidecar_path: Path
    data: dict


def write_sidecar(ctx: SidecarContext) -> Path:
    rendered = _env.get_template(ctx.template).render(**ctx.data)
    existing_body = _extract_body_below_separator(ctx.sidecar_path) if ctx.sidecar_path.exists() else ""
    final = rendered + existing_body
    ctx.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = ctx.sidecar_path.with_suffix(ctx.sidecar_path.suffix + ".tmp")
    tmp.write_text(final, encoding="utf-8")
    tmp.replace(ctx.sidecar_path)
    return ctx.sidecar_path


def _extract_body_below_separator(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if _BODY_SEPARATOR not in text:
        return ""
    _, after = text.split(_BODY_SEPARATOR, 1)
    return after
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_sidecar.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/odg_sorter/sidecar.py src/odg_sorter/templates/ tests/test_sidecar.py pyproject.toml
git commit -m "add sidecar renderer (Jinja2) + dhtw-sled template; body-preserving rewrites"
```

---

### Task 8: Remaining sidecar templates (8 more)

**Files:**
- Create: `src/odg_sorter/templates/sidecars/dhtw-card.md.j2`
- Create: `src/odg_sorter/templates/sidecars/dhtw-arlo-voice.md.j2`
- Create: `src/odg_sorter/templates/sidecars/tgc-component.md.j2`
- Create: `src/odg_sorter/templates/sidecars/tll-comfyui.md.j2`
- Create: `src/odg_sorter/templates/sidecars/tll-glb.md.j2`
- Create: `src/odg_sorter/templates/sidecars/dhtw-glb.md.j2`
- Create: `src/odg_sorter/templates/sidecars/blender-source.md.j2`
- Create: `src/odg_sorter/templates/sidecars/digest.md.j2`

Each template mirrors `dhtw-sled.md.j2`'s shape: YAML frontmatter, embed line, header, body separator. Only the tag set and embed target differ.

- [ ] **Step 1: Write all 8 templates**

`src/odg_sorter/templates/sidecars/dhtw-card.md.j2`:

```jinja2
---
asset: {{ asset }}
project: dhtw-tabletop
hash: sha256:{{ hash }}
size: {{ size }}
mime: {{ mime }}
ingested: {{ ingested }}
sorter-rule: {{ rule }}
canonical-path: {{ canonical_path }}
ingested-from: {{ ingested_from }}
tags: [asset/image, project/dhtw-tabletop, component/card]
---

![[_repos/dhtw-tabletop/components/cards/fronts/{{ asset }}]]

# {{ asset }}

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

`src/odg_sorter/templates/sidecars/dhtw-arlo-voice.md.j2`:

```jinja2
---
asset: {{ asset }}
project: dhtw
source-tool: elevenlabs
hash: sha256:{{ hash }}
size: {{ size }}
mime: {{ mime }}
ingested: {{ ingested }}
sorter-rule: {{ rule }}
canonical-path: {{ canonical_path }}
ingested-from: {{ ingested_from }}
tags: [asset/audio, project/dhtw, character/arlo]
---

# {{ asset }}

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

`src/odg_sorter/templates/sidecars/tgc-component.md.j2`:

```jinja2
---
asset: {{ asset }}
project: dhtw-tabletop
component-type: {{ component_type }}
source-tool: inkscape
hash: sha256:{{ hash }}
size: {{ size }}
mime: image/svg+xml
ingested: {{ ingested }}
sorter-rule: {{ rule }}
canonical-path: {{ canonical_path }}
ingested-from: {{ ingested_from }}
tags: [asset/svg, project/dhtw-tabletop, component/{{ component_type }}, tool/inkscape]
---

# {{ asset }}

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

`src/odg_sorter/templates/sidecars/tll-comfyui.md.j2`:

```jinja2
---
asset: {{ asset }}
project: tll
system: {{ system }}
source-tool: comfyui
workflow: {{ workflow }}
model: {{ model }}
seed: {{ seed }}
prompt: |
  {{ prompt | indent(2) }}
hash: sha256:{{ hash }}
size: {{ size }}
mime: {{ mime }}
ingested: {{ ingested }}
sorter-rule: {{ rule }}
canonical-path: {{ canonical_path }}
ingested-from: {{ ingested_from }}
tags: [asset/image, project/tll, system/{{ system }}, tool/comfyui]
---

![[_repos/tll/client/assets/generated/{{ system }}/{{ asset }}]]

# {{ asset }}

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

`src/odg_sorter/templates/sidecars/tll-glb.md.j2`:

```jinja2
---
asset: {{ asset }}
project: tll
system: {{ system }}
source-tool: blender
hash: sha256:{{ hash }}
size: {{ size }}
mime: model/gltf-binary
ingested: {{ ingested }}
sorter-rule: {{ rule }}
canonical-path: {{ canonical_path }}
ingested-from: {{ ingested_from }}
tags: [asset/3d, project/tll, system/{{ system }}, tool/blender]
---

# {{ asset }}

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

`src/odg_sorter/templates/sidecars/dhtw-glb.md.j2`:

```jinja2
---
asset: {{ asset }}
project: dhtw
system: {{ system }}
source-tool: blender
hash: sha256:{{ hash }}
size: {{ size }}
mime: model/gltf-binary
ingested: {{ ingested }}
sorter-rule: {{ rule }}
canonical-path: {{ canonical_path }}
ingested-from: {{ ingested_from }}
tags: [asset/3d, project/dhtw, system/{{ system }}, tool/blender]
---

# {{ asset }}

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

`src/odg_sorter/templates/sidecars/blender-source.md.j2`:

```jinja2
---
asset: {{ asset }}
project: {{ project }}
source-tool: blender
hash: sha256:{{ hash }}
size: {{ size }}
mime: application/x-blender
ingested: {{ ingested }}
sorter-rule: {{ rule }}
canonical-path: {{ canonical_path }}
ingested-from: {{ ingested_from }}
tags: [asset/blender-source, project/{{ project }}, tool/blender]
---

# {{ asset }}

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

`src/odg_sorter/templates/sidecars/digest.md.j2`:

```jinja2
---
type: digest
generated: {{ generated }}
period-start: {{ period_start }}
period-end: {{ period_end }}
tags: [system/odg-sorter, digest]
---

# Intake digest — {{ period_start }} to {{ period_end }}

{% if heartbeat_stale -%}
> ⚠ Heartbeat is stale (last seen {{ heartbeat_ts }}). Daemon may be dead.
{%- endif %}

## Counts
- Routed (confident): **{{ counts.routed }}**
- Parked (ambiguous): **{{ counts.parked }}**
- Quarantined (displaced duplicates): **{{ counts.quarantined }}**
- WIP-protected (skipped): **{{ counts.wip_protected }}**

## Parked files awaiting review

{% if parked %}
{% for p in parked %}- `{{ p.path }}` — {{ p.reason }}
{% endfor %}
{% else %}_None._
{% endif %}

## Recent quarantine events

{% if quarantined %}
{% for q in quarantined %}- `{{ q.original }}` → `{{ q.quarantined_to }}`
{% endfor %}
{% else %}_None._
{% endif %}
```

- [ ] **Step 2: Verify all templates parse**

Run:
```bash
python -c "from jinja2 import Environment, FileSystemLoader; e=Environment(loader=FileSystemLoader('src/odg_sorter/templates/sidecars')); [e.get_template(t) for t in ['dhtw-sled.md.j2','dhtw-card.md.j2','dhtw-arlo-voice.md.j2','tgc-component.md.j2','tll-comfyui.md.j2','tll-glb.md.j2','dhtw-glb.md.j2','blender-source.md.j2','digest.md.j2']]; print('OK')"
```
Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
git add src/odg_sorter/templates/sidecars/
git commit -m "add 8 remaining sidecar templates + digest template"
```

---

### Task 9: Watcher (`watcher.py`)

**Files:**
- Create: `src/odg_sorter/watcher.py`
- Create: `tests/test_watcher.py`

The watcher wraps `watchdog`. It debounces `modified` events (2s window per path), confirms the file is no longer open for writing (Windows: exclusive open), and emits a `FileLanded(path)` callback to the pipeline.

- [ ] **Step 1: Write the failing tests**

`tests/test_watcher.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_watcher.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `watcher.py`**

`src/odg_sorter/watcher.py`:

```python
import threading
from collections.abc import Callable, Iterable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class Watcher:
    def __init__(
        self,
        watched_paths: Iterable[Path],
        on_landed: Callable[[Path], None],
        debounce_seconds: float = 2.0,
    ) -> None:
        self._paths = [Path(p) for p in watched_paths]
        self._on_landed = on_landed
        self._debounce = debounce_seconds
        self._observer = Observer()
        self._timers: dict[Path, threading.Timer] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        handler = _Handler(self._schedule)
        for p in self._paths:
            p.mkdir(parents=True, exist_ok=True)
            self._observer.schedule(handler, str(p), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5.0)
        with self._lock:
            for t in self._timers.values():
                t.cancel()

    def _schedule(self, path: Path) -> None:
        with self._lock:
            existing = self._timers.pop(path, None)
            if existing is not None:
                existing.cancel()
            t = threading.Timer(self._debounce, self._fire, args=(path,))
            self._timers[path] = t
            t.daemon = True
            t.start()

    def _fire(self, path: Path) -> None:
        with self._lock:
            self._timers.pop(path, None)
        if not path.exists():
            return
        if not _file_is_closed(path):
            self._schedule(path)
            return
        self._on_landed(path)


class _Handler(FileSystemEventHandler):
    def __init__(self, schedule: Callable[[Path], None]) -> None:
        self._schedule = schedule

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule(Path(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule(Path(event.src_path))


def _file_is_closed(path: Path) -> bool:
    """On Windows, opening with mode 'r+b' fails if another process holds the file open for write."""
    try:
        with path.open("rb"):
            pass
        return True
    except OSError:
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_watcher.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/odg_sorter/watcher.py tests/test_watcher.py
git commit -m "add watcher (watchdog + 2s debounce + open-exclusive guard)"
```

---

### Task 10: Pipeline + sort-one verb (`main.py`, `cli.py` wired)

**Files:**
- Modify: `src/odg_sorter/cli.py` (wire `sort` verb)
- Create: `src/odg_sorter/main.py` (sort-one function + daemon stub)

This task wires the pipeline for one file: identify → route → move → sidecar → state. Daemon loop comes in Task 11.

- [ ] **Step 1: Implement `main.py` (sort-one path only for now)**

`src/odg_sorter/main.py`:

```python
import logging
from datetime import datetime, timezone
from pathlib import Path

from odg_sorter.config.paths import QUARANTINE, REPOS, STUDIO_ROOT, VAULT_PROJECTS
from odg_sorter.identify import identify
from odg_sorter.mover import MoveResult, SkipResult, move_into_canonical_home
from odg_sorter.router import Park, Route, route
from odg_sorter.sidecar import SidecarContext, write_sidecar
from odg_sorter.state import State

log = logging.getLogger("odg_sorter")

DATA_DIR = STUDIO_ROOT / "repos" / "asset-management" / "data"
STATE_PATH = DATA_DIR / "state.sqlite"


def sort_one(path: Path, *, state: State | None = None) -> str:
    state = state or State(STATE_PATH)
    path = Path(path)
    signals = identify(path)

    seen = state.find_by_hash(signals.hash_sha256)
    if seen is not None:
        state.record_also_ingested(signals.hash_sha256, path)
        log.info("already-seen hash=%s prior=%s", signals.hash_sha256[:8], seen.destination)
        return "already-seen"

    decision = route(signals)
    if isinstance(decision, Park):
        decision.destination.mkdir(parents=True, exist_ok=True)
        park_dest = decision.destination / path.name
        if not park_dest.exists():
            path.rename(park_dest) if path.parent == decision.destination else None
        state.record_park(signals.hash_sha256, path, reason=decision.reason)
        log.info("parked path=%s reason=%s", path, decision.reason)
        return "parked"

    assert isinstance(decision, Route)
    move_result = move_into_canonical_home(
        path,
        decision.destination,
        quarantine_root=QUARANTINE,
        repos_root=REPOS,
    )
    if isinstance(move_result, SkipResult):
        state.record_park(signals.hash_sha256, path, reason=move_result.reason)
        log.info("skipped path=%s reason=%s", path, move_result.reason)
        return move_result.reason

    sidecar_path = _sidecar_path_for(decision, signals)
    ctx = SidecarContext(
        template=decision.sidecar_template,
        sidecar_path=sidecar_path,
        data=_sidecar_data(decision, signals, source=path),
    )
    write_sidecar(ctx)
    state.record_route(
        signals.hash_sha256,
        source=path,
        destination=move_result.destination,
        rule=decision.rule,
    )
    log.info("routed rule=%s dest=%s", decision.rule, move_result.destination)
    return "routed"


def _sidecar_path_for(decision: Route, signals) -> Path:
    project = _project_for_rule(decision.rule)
    return VAULT_PROJECTS / project / "Assets" / (Path(signals.filename).stem + ".md")


def _project_for_rule(rule_name: str) -> str:
    if rule_name.startswith("tll-"):
        return "TLL"
    if rule_name.startswith("dhtw-") or rule_name == "tgc-component-svg":
        return "DHTW"
    return "DHTW"  # fallback; only reached if a future rule is added without a project mapping


def _sidecar_data(decision: Route, signals, *, source: Path) -> dict:
    return {
        "asset": signals.filename,
        "theme": _theme_from_destination(decision.destination),
        "system": _system_from_destination(decision.destination),
        "component_type": _component_type_from_destination(decision.destination),
        "source_tool": signals.tool,
        "workflow": signals.comfyui_workflow,
        "model": signals.comfyui_model,
        "seed": signals.comfyui_seed,
        "prompt": signals.comfyui_prompt,
        "hash": signals.hash_sha256,
        "size": str([signals.size_bytes]),
        "mime": _mime_for(signals.extension),
        "ingested": datetime.now(timezone.utc).astimezone().isoformat(),
        "rule": decision.rule,
        "canonical_path": str(decision.destination),
        "ingested_from": str(source),
        "project": _project_for_rule(decision.rule).lower(),
    }


def _theme_from_destination(dest: Path) -> str:
    parts = dest.parts
    if "themes" in parts:
        i = parts.index("themes")
        return parts[i + 1] if i + 1 < len(parts) else "uncategorized"
    return "uncategorized"


def _system_from_destination(dest: Path) -> str:
    parts = dest.parts
    for key in ("3d", "generated"):
        if key in parts:
            i = parts.index(key)
            return parts[i + 1] if i + 1 < len(parts) else "uncategorized"
    return "uncategorized"


def _component_type_from_destination(dest: Path) -> str:
    parts = dest.parts
    if "components" in parts:
        i = parts.index("components")
        return parts[i + 1] if i + 1 < len(parts) else "uncategorized"
    return "uncategorized"


def _mime_for(ext: str) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".glb": "model/gltf-binary",
        ".gltf": "model/gltf+json",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".blend": "application/x-blender",
    }.get(ext.lower(), "application/octet-stream")
```

- [ ] **Step 2: Wire `sort` verb in `cli.py`**

Replace the body of `cli.py` `main()` with:

```python
import argparse
import logging
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="odg-sorter")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("daemon")
    sort_parser = sub.add_parser("sort")
    sort_parser.add_argument("path")
    digest_parser = sub.add_parser("digest")
    digest_parser.add_argument("--since", default=None)
    sub.add_parser("reconcile")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.cmd == "sort":
        from odg_sorter.main import sort_one
        outcome = sort_one(Path(args.path))
        print(outcome)
        return 0

    # daemon/digest/reconcile come in later tasks.
    print(f"odg-sorter: cmd={args.cmd} not yet wired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Smoke check sort-one end-to-end**

Manual smoke (writes nothing to your real `C:\ODG\` because it points to a tmp dir; we test this properly in Task 14):

```bash
pytest tests/ -v --maxfail=1
```
Expected: all prior tests still pass.

- [ ] **Step 4: Commit**

```bash
git add src/odg_sorter/main.py src/odg_sorter/cli.py
git commit -m "wire sort-one pipeline + CLI sort verb"
```

---

### Task 11: Daemon loop + reconciliation (`main.py` daemon path, `reconcile.py`)

**Files:**
- Modify: `src/odg_sorter/main.py` (add daemon entrypoint)
- Create: `src/odg_sorter/reconcile.py`
- Modify: `src/odg_sorter/cli.py` (wire `daemon` and `reconcile` verbs)

- [ ] **Step 1: Implement `reconcile.py`**

`src/odg_sorter/reconcile.py`:

```python
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
```

- [ ] **Step 2: Add daemon loop to `main.py`**

Append to `src/odg_sorter/main.py`:

```python
import signal
import time

from odg_sorter.config.paths import WATCHED_PATHS
from odg_sorter.reconcile import reconcile
from odg_sorter.watcher import Watcher


def run_daemon() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = State(STATE_PATH)
    events = {"count": 0}

    log.info("starting reconciliation pass")
    reconcile(state)
    state.write_heartbeat(events["count"])

    stop = threading.Event()

    def on_landed(path: Path) -> None:
        try:
            sort_one(path, state=state)
        except Exception:
            log.exception("sort_one failed for %s", path)
        finally:
            events["count"] += 1

    watcher = Watcher(watched_paths=WATCHED_PATHS, on_landed=on_landed)
    watcher.start()

    def handle_sigint(_sig, _frame):
        log.info("shutdown signal received")
        stop.set()

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    last_hb = time.monotonic()
    try:
        while not stop.wait(timeout=1.0):
            if time.monotonic() - last_hb >= 60.0:
                state.write_heartbeat(events["count"])
                last_hb = time.monotonic()
    finally:
        watcher.stop()
        state.write_heartbeat(events["count"])
        log.info("daemon stopped")
    return 0
```

Add the missing import at the top of `main.py`:

```python
import threading
```

- [ ] **Step 3: Wire `daemon` and `reconcile` verbs in `cli.py`**

Update the verb dispatch block in `main()`:

```python
    if args.cmd == "sort":
        from odg_sorter.main import sort_one
        outcome = sort_one(Path(args.path))
        print(outcome)
        return 0
    if args.cmd == "daemon":
        from odg_sorter.main import run_daemon
        return run_daemon()
    if args.cmd == "reconcile":
        from odg_sorter.main import STATE_PATH
        from odg_sorter.reconcile import reconcile
        from odg_sorter.state import State
        state = State(STATE_PATH)
        result = reconcile(state)
        print(result)
        return 0
    if args.cmd == "digest":
        print("digest not yet wired")
        return 0
```

- [ ] **Step 4: Smoke check**

Run:
```bash
odg-sorter daemon &
PID=$!
sleep 2
kill -INT $PID
wait $PID
```
Expected: daemon starts, runs reconciliation, sits idle, shuts down cleanly on SIGINT.

- [ ] **Step 5: Commit**

```bash
git add src/odg_sorter/main.py src/odg_sorter/reconcile.py src/odg_sorter/cli.py
git commit -m "add daemon loop + reconciliation pass + signal handling"
```

---

### Task 12: Digest generator (`digest.py`)

**Files:**
- Create: `src/odg_sorter/digest.py`
- Create: `tests/test_digest.py`
- Modify: `src/odg_sorter/cli.py` (wire `digest` verb)

The digest reads `state.sqlite`, summarizes the period (default: last 7 days), checks heartbeat staleness, lists parked files in `_intake/unsorted/`, and writes a vault note named `Intake review <YYYY-MM-DD>.md`.

- [ ] **Step 1: Write the failing test**

`tests/test_digest.py`:

```python
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from odg_sorter.digest import generate_digest
from odg_sorter.state import State


@pytest.fixture
def setup(tmp_path):
    state = State(tmp_path / "state.sqlite")
    state.record_route("h1", Path("C:/in/a.png"), Path("C:/repos/dhtw/a.png"), rule="dhtw-sled-themed-v7")
    state.record_park("h2", Path("C:/in/b.glb"), reason="no-project-hint")
    state.write_heartbeat(events_processed=42)
    vault = tmp_path / "vault"
    vault.mkdir()
    unsorted = tmp_path / "unsorted"
    unsorted.mkdir()
    (unsorted / "b.glb").write_bytes(b"x")
    return {"state": state, "vault": vault, "unsorted": unsorted}


def test_digest_writes_note_with_counts(setup):
    out = generate_digest(
        state=setup["state"],
        vault_root=setup["vault"],
        unsorted_root=setup["unsorted"],
        period_days=7,
    )
    text = out.read_text(encoding="utf-8")
    assert "Routed (confident): **1**" in text
    assert "Parked (ambiguous): **1**" in text
    assert "b.glb" in text


def test_digest_flags_stale_heartbeat(tmp_path):
    state = State(tmp_path / "state.sqlite")
    # Write a heartbeat then manually backdate it.
    state.write_heartbeat(events_processed=0)
    state._conn.execute(
        "UPDATE heartbeat SET ts = ? WHERE id = 1",
        ((datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),),
    )
    vault = tmp_path / "vault"; vault.mkdir()
    unsorted = tmp_path / "unsorted"; unsorted.mkdir()
    out = generate_digest(state=state, vault_root=vault, unsorted_root=unsorted, period_days=7)
    assert "Heartbeat is stale" in out.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_digest.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `digest.py`**

`src/odg_sorter/digest.py`:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from importlib.resources import files

from odg_sorter.state import State

HEARTBEAT_STALE_AFTER_SECONDS = 5 * 60
TEMPLATE_NAME = "digest.md.j2"

_env = Environment(
    loader=FileSystemLoader(str(files("odg_sorter.templates.sidecars"))),
    keep_trailing_newline=True,
)


def generate_digest(
    *,
    state: State,
    vault_root: Path,
    unsorted_root: Path,
    period_days: int = 7,
) -> Path:
    now = datetime.now(timezone.utc).astimezone()
    start = now - timedelta(days=period_days)

    counts = _counts_since(state, start)
    parked = _list_parked(state, start)
    quarantined: list[dict] = []  # populated once mover writes quarantine events; v1 leaves empty
    heartbeat = state.read_heartbeat()
    heartbeat_stale = (
        heartbeat is None
        or (now - heartbeat.timestamp).total_seconds() > HEARTBEAT_STALE_AFTER_SECONDS
    )

    rendered = _env.get_template(TEMPLATE_NAME).render(
        generated=now.isoformat(timespec="seconds"),
        period_start=start.date().isoformat(),
        period_end=now.date().isoformat(),
        counts=counts,
        parked=[{"path": p, "reason": r} for (p, r) in parked],
        quarantined=quarantined,
        heartbeat_stale=heartbeat_stale,
        heartbeat_ts=heartbeat.timestamp.isoformat(timespec="seconds") if heartbeat else "never",
    )

    out_dir = vault_root / "Opal Dragonfly Games" / "Resources" / "Asset Gallery"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"Intake review {now.date().isoformat()}.md"
    out_path.write_text(rendered, encoding="utf-8")
    return out_path


@dataclass(frozen=True)
class Counts:
    routed: int
    parked: int
    quarantined: int
    wip_protected: int


def _counts_since(state: State, since: datetime) -> Counts:
    cur = state._conn.execute(
        "SELECT rule, reason, COUNT(*) FROM routes WHERE ts >= ? GROUP BY rule, reason",
        (since.isoformat(),),
    )
    routed = parked = wip = 0
    for rule, reason, n in cur.fetchall():
        if rule == "park":
            if reason == "wip-protected":
                wip += n
            else:
                parked += n
        else:
            routed += n
    return Counts(routed=routed, parked=parked, quarantined=0, wip_protected=wip)


def _list_parked(state: State, since: datetime) -> list[tuple[str, str]]:
    cur = state._conn.execute(
        "SELECT source, reason FROM routes WHERE rule = 'park' AND ts >= ? ORDER BY ts DESC",
        (since.isoformat(),),
    )
    return [(row[0], row[1] or "") for row in cur.fetchall()]
```

(The template expects `counts.routed`, `counts.parked`, `counts.quarantined`, `counts.wip_protected` attributes — a dataclass satisfies that.)

- [ ] **Step 4: Wire `digest` verb in `cli.py`**

Replace the digest branch:

```python
    if args.cmd == "digest":
        from odg_sorter.config.paths import UNSORTED, VAULT
        from odg_sorter.digest import generate_digest
        from odg_sorter.main import STATE_PATH
        from odg_sorter.state import State
        state = State(STATE_PATH)
        out = generate_digest(state=state, vault_root=VAULT, unsorted_root=UNSORTED, period_days=7)
        print(f"wrote: {out}")
        return 0
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_digest.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/odg_sorter/digest.py src/odg_sorter/cli.py tests/test_digest.py
git commit -m "add digest generator (vault note with counts + stale-heartbeat warning)"
```

---

### Task 13: Integration tests — one per high-confidence routing rule

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_integration.py`

End-to-end with tmp dirs and the real pipeline. One test per `high`-confidence rule from `config/rules.py` (rules 1–8) plus dedup + idempotency.

- [ ] **Step 1: Write `conftest.py`**

`tests/conftest.py`:

```python
from pathlib import Path

import pytest

from odg_sorter import config


@pytest.fixture
def tmp_studio(tmp_path, monkeypatch):
    """Redirect every config path into tmp_path. Returns dict of the redirected roots."""
    intake = tmp_path / "_intake"; intake.mkdir()
    unsorted = intake / "unsorted"; unsorted.mkdir()
    repos = tmp_path / "repos"; repos.mkdir()
    vault = tmp_path / "vault"; vault.mkdir()
    quarantine = tmp_path / "_quarantine"; quarantine.mkdir()
    comfyui_out = tmp_path / "comfyui_output"; comfyui_out.mkdir()

    monkeypatch.setattr(config.paths, "STUDIO_ROOT", tmp_path)
    monkeypatch.setattr(config.paths, "WATCHED_PATHS", (intake, comfyui_out))
    monkeypatch.setattr(config.paths, "REPOS", repos)
    monkeypatch.setattr(config.paths, "VAULT", vault)
    monkeypatch.setattr(config.paths, "QUARANTINE", quarantine)
    monkeypatch.setattr(config.paths, "UNSORTED", unsorted)
    monkeypatch.setattr(config.paths, "VAULT_PROJECTS", vault / "Opal Dragonfly Games" / "Projects")
    monkeypatch.setattr(config.paths, "VAULT_GALLERY", vault / "Opal Dragonfly Games" / "Resources" / "Asset Gallery")
    monkeypatch.setattr(config.paths, "DHTW_REPO", repos / "dhtw")
    monkeypatch.setattr(config.paths, "DHTW_TABLETOP_REPO", repos / "dhtw-tabletop")
    monkeypatch.setattr(config.paths, "TLL_REPO", repos / "tll")

    # config/rules.py imports the path names at import time; reload it so
    # the rules pick up the patched paths.
    import importlib

    from odg_sorter.config import rules as _rules
    importlib.reload(_rules)

    from odg_sorter import router as _router
    importlib.reload(_router)

    return {
        "intake": intake,
        "unsorted": unsorted,
        "repos": repos,
        "vault": vault,
        "quarantine": quarantine,
        "comfyui_out": comfyui_out,
    }
```

- [ ] **Step 2: Write `test_integration.py` — rule-by-rule**

`tests/test_integration.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `pytest tests/test_integration.py -v`
Expected: 10 passed.

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py tests/test_integration.py
git commit -m "add 10 integration tests (one per high-confidence rule + dedup + idempotency + WIP)"
```

---

### Task 14: Smoke test — daemon-in-thread

**Files:**
- Create: `tests/test_smoke.py`

Verifies the watcher → pipeline path with a real `Watcher` started in-process.

- [ ] **Step 1: Write the smoke test**

`tests/test_smoke.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_smoke.py -v`
Expected: 1 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_smoke.py
git commit -m "add smoke test: daemon-in-thread routes a new file end-to-end"
```

---

### Task 15: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

`.github/workflows/ci.yml`:

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
      - name: Rebuild fixtures
        run: python tests/fixtures/_build_fixtures.py
      - name: Run tests
        run: pytest -v
```

- [ ] **Step 2: Commit + push + verify CI**

```bash
git add .github/workflows/ci.yml
git commit -m "add CI: pytest on windows-latest, push + PR"
git push origin main
```

Then visit the repo's Actions tab in GitHub. Expected: the run completes green within ~3 minutes.

If it fails, fix locally, commit, push again. Don't move on until green.

---

### Task 16: Vault Dataview gallery pages

**Files:**
- Create: `ODG_Vault/Opal Dragonfly Games/Resources/Asset Gallery/By-Tool.md`
- Create: `ODG_Vault/Opal Dragonfly Games/Resources/Asset Gallery/By-Project.md`
- Create: `ODG_Vault/Opal Dragonfly Games/Resources/Asset Gallery/By-Tier.md`
- Create: `ODG_Vault/Opal Dragonfly Games/Resources/Asset Gallery/Recent.md`

These are not in the repo; they're hand-written one-time Dataview queries that the vault git-tracks normally.

- [ ] **Step 1: Write `By-Tool.md`**

```markdown
# By Tool

Every asset grouped by source tool.

```dataview
TABLE WITHOUT ID
  file.link AS Asset,
  project AS Project,
  workflow AS Workflow,
  ingested AS Ingested
FROM "Opal Dragonfly Games/Projects"
WHERE asset
GROUP BY `source-tool`
SORT ingested DESC
``` 
```

(Note: triple backticks inside the code block above are illustrative — when copy-pasting, the outer fence is what goes in the markdown; the inner `dataview` block uses its own fence per Obsidian Dataview syntax.)

- [ ] **Step 2: Write `By-Project.md`**

```markdown
# By Project

```dataview
TABLE WITHOUT ID
  file.link AS Asset,
  `source-tool` AS Tool,
  theme AS Theme,
  ingested AS Ingested
FROM "Opal Dragonfly Games/Projects"
WHERE asset
GROUP BY project
SORT ingested DESC
``` 
```

- [ ] **Step 3: Write `By-Tier.md`**

```markdown
# By Tier (DHTW sleds)

```dataview
TABLE WITHOUT ID
  file.link AS Asset,
  theme AS Theme,
  palette AS Palette
FROM "Opal Dragonfly Games/Projects/DHTW"
WHERE asset AND tier
GROUP BY tier
``` 
```

- [ ] **Step 4: Write `Recent.md`**

```markdown
# Recent (last 7 days)

```dataview
TABLE WITHOUT ID
  file.link AS Asset,
  project AS Project,
  `source-tool` AS Tool,
  ingested AS Ingested
FROM "Opal Dragonfly Games/Projects"
WHERE asset AND date(ingested) >= date(today) - dur(7 days)
SORT ingested DESC
``` 
```

- [ ] **Step 5: Commit in the vault repo**

```bash
cd C:/ODG/ODG_Vault
git add "Opal Dragonfly Games/Resources/Asset Gallery/"
git commit -m "add Dataview gallery pages for odg-sorter sidecars"
git push origin master
```

---

### Task 17: Task Scheduler install script

**Files:**
- Create: `scripts/install_task_scheduler.ps1`

Registers a Windows Scheduled Task that runs `odg-sorter daemon` at user logon.

- [ ] **Step 1: Write the script**

`scripts/install_task_scheduler.ps1`:

```powershell
<#
.SYNOPSIS
  Register the odg-sorter daemon as a Windows Scheduled Task that runs at user logon.

.NOTES
  Run from an elevated PowerShell prompt. Re-run to update the trigger or action.
#>
param(
  [string]$TaskName = "odg-sorter daemon",
  [string]$PythonExe = (Get-Command python).Source
)

$ErrorActionPreference = "Stop"

$action = New-ScheduledTaskAction `
  -Execute $PythonExe `
  -Argument "-m odg_sorter daemon" `
  -WorkingDirectory "C:\ODG\repos\asset-management"

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 5)

$principal = New-ScheduledTaskPrincipal `
  -UserId $env:USERNAME `
  -LogonType Interactive

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -Principal $principal `
  -Force | Out-Null

Write-Host "Registered '$TaskName'. It will run at next logon. Start it now with:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
```

- [ ] **Step 2: Manual verification (one-time)**

From an elevated PowerShell:
```powershell
cd C:\ODG\repos\asset-management
.\scripts\install_task_scheduler.ps1
Start-ScheduledTask -TaskName "odg-sorter daemon"
Get-ScheduledTaskInfo -TaskName "odg-sorter daemon"
```
Expected: `LastRunTime` updates, `LastTaskResult` is `0`.

- [ ] **Step 3: Commit**

```bash
git add scripts/install_task_scheduler.ps1
git commit -m "add Task Scheduler install script (at-logon trigger)"
```

---

### Task 18: README + repo CLAUDE.md update

**Files:**
- Create: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# odg-sorter

A Python daemon that watches studio inflow paths (ComfyUI output, `_intake/`)
and routes new generated assets into project-repo canonical homes, writing
Obsidian vault sidecars so the vault becomes the find-layer.

## Install

```bash
pip install -e .[dev]
```

## Run

```bash
odg-sorter daemon       # start the watcher
odg-sorter sort <path>  # one-shot, route a single file
odg-sorter digest       # generate the weekly digest now
odg-sorter reconcile    # walk known paths, route anything missed
```

## At logon

```powershell
.\scripts\install_task_scheduler.ps1
```

## Test

```bash
pytest -v
```

## Design

`docs/superpowers/specs/2026-06-04-asset-management-v1-design.md`

## Implementation plan

`docs/superpowers/plans/2026-06-04-asset-management-v1.md`
```

- [ ] **Step 2: Update `CLAUDE.md` — add a "Status" line at the top noting v1 is live**

Append to the existing `CLAUDE.md` body (after the last bullet):

```markdown

## v1 status

Phase 0 scaffolding (the original PowerShell audit script) and v1 (`odg-sorter` Python daemon) are both live:

- Audit: `scripts/Audit-ODGFiles.ps1` (PowerShell, ad-hoc audits).
- Sorter: `odg-sorter` (Python, continuous watcher). Source: `src/odg_sorter/`. Run as `odg-sorter daemon`.
- Find-layer: Obsidian vault sidecars under `Opal Dragonfly Games/Projects/<project>/Assets/`.
- Backfill: deferred to v1.1.
```

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "add README + repo CLAUDE.md status block"
```

---

## Self-review notes

**Spec coverage** — walked the spec section-by-section against the task list:
- Architecture diagram → Tasks 1–11 (scaffold → state → identify → router → mover → sidecar → watcher → main).
- Components table → 9 modules mapped 1:1 (`watcher` Task 9, `identify` Task 3, `router` Task 5, `mover` Task 6, `sidecar` Task 7, `state` Task 2, `digest` Task 12, `main` Task 11, `config/` Tasks 4–5).
- Vault sidecar location & shape → Tasks 7 + 8 (templates) + 10 (path resolution in `main._sidecar_path_for`).
- 10 routing rules → Task 5 (rules + router) implements 8 high-confidence + park fallback. Rule 9 (`blender-render-scratch`) is intentionally rolled into the fallback for v1 (low-confidence is just "park").
- Engine-level safety rule (files inside `repos/` never moved) → Task 6, `test_file_inside_repos_is_never_moved`.
- WIP guard (7-day) → Task 6, `test_wip_guard_skips_recent_repo_destination`.
- Atomic operations → Task 6 + 7 (sidecar uses `tmp` then `replace`).
- Reconciliation → Task 11.
- Heartbeat → Task 2 schema + Task 11 daemon tick + Task 12 staleness check.
- Three test layers (unit/integration/smoke) → Tasks 2/3/5/6/7/12 unit, Task 13 integration, Task 14 smoke.
- CI → Task 15.
- v1 ship criteria → covered by Tasks 11 (daemon at logon) + 13 + 14 + 15 + 17.

**Placeholder scan** — no `TBD`, no `TODO`, no "add error handling later," no "similar to Task N." Every step has actual code or an exact command. One spec field — the ComfyUI output dir path — is acknowledged as a real-world confirmation step in `config/paths.py` (`# UPDATE when the actual ComfyUI install path is confirmed.`). That's not a plan placeholder; it's an honest deferred input.

**Type consistency** — checked: `Signals` defined Task 3 used by Tasks 5, 10, 11. `Route`/`Park` defined Task 5 used by Tasks 10. `MoveResult`/`SkipResult` defined Task 6 used by Task 10. `SidecarContext` defined Task 7 used by Task 10. `State.find_by_hash`, `record_route`, `record_park`, `record_also_ingested`, `write_heartbeat`, `read_heartbeat` — all defined Task 2 and used consistently downstream. No drift.

**Scope** — 18 tasks, ~25–35 hours of work for a focused engineer. Within "single plan, single subsystem" scope.

**One deliberate v1 trim** — the spec's rule 9 (`blender-render-scratch`, low-confidence) is folded into the fallback park rule for v1. A render `.png` with no project signal gets the same treatment as any unknown file: parked + digested. The rule re-emerges in v1.2 once the digest shows real volume.
