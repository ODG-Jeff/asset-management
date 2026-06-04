# Asset Management v1 — Design

| | |
|---|---|
| **Status** | Design — awaiting plan |
| **Owner** | Jeff Konz |
| **Captured** | 2026-06-04 |
| **Sub-project of** | ODG AI Studio (broader: A of A/B/C/D/E/G) |
| **Implements** | `odg-sorter` daemon + Obsidian sidecar find-layer |

## Summary

A Python daemon (`odg-sorter`) that watches a small set of inflow paths and routes generated assets into their canonical homes in the project repos. For every routed file, it writes a metadata sidecar `.md` into the Obsidian vault — making the vault the single find-layer for everything the studio generates. Files the sorter can't confidently classify wait in `_intake/unsorted/` for a weekly digest review.

Forward-only: v1 sorts new files. Existing scatter in `C:\ODG\generated\`, `Downloads\`, `Desktop\`, etc. stays put until a v1.1 backfill pass once the routing rules are proven.

Replaces the manual triage that lets generated assets accumulate in `_intake/`, `generated/`, and the OS download folder — without taking on the risk of moving files we're not sure about.

## Goals

1. **Fire-and-forget routing.** A confident new file (e.g. ComfyUI sled output) lands → reaches its canonical home in `repos/dhtw/assets/sleds/themes/<theme>/` within seconds, with a sidecar in the vault.
2. **Find anything in seconds.** Vault sidecars carry rich frontmatter (project, theme, tier, tool, prompt, workflow, hash, etc.). Obsidian search + Dataview queries surface assets without folder navigation.
3. **Never lose work.** Hard rule: never delete. Replaced files go to `_quarantine/<date>/`. In-flight files (mtime <7d in a repo tree) are never moved.
4. **Restart-safe.** Daemon can be killed at any moment; reconciliation closes any gap on next start. No data loss, no in-memory queue.
5. **Idempotent.** Re-routing a file that's already in its canonical home is a no-op (other than refreshing the sidecar timestamp).
6. **One-user simple.** No web UI, no rule-editing UI, no notifications beyond a weekly digest. Terminal + Obsidian + heartbeat log is the whole UX.

## Non-goals (v1)

- Backfilling existing scatter (deferred to v1.1).
- LLM-in-the-loop classification of ambiguous files (deferred to v1.2 if digest volume justifies it).
- CLIP / semantic visual search (deferred to v3.0 if tag-based search proves insufficient).
- A web UI, tray icon, toasts, or any out-of-band notification.
- A second tool (Eagle / Bridge / Mylio). The vault is the find-layer.
- Auto-generated thumbnails (Obsidian renders the `![[...]]` embed from the canonical-path file).
- Cross-machine sync of state (laptop is the only generator).
- Format-validity checks (rule-driven, not content-driven).
- Rule learning from manual corrections (you read the digest and edit `config/rules.py` yourself).

## Architecture

```
       Watched inflow paths                Hard rules
       +----------------------------+      +------------------------------+
       | * ComfyUI output dir(s)    |      | * Never delete; replaced     |
       | * C:\ODG\_intake\<date>\   |      |   files -> _quarantine/<date>|
       | * Browser Downloads        |      | * Skip files modified <7d in |
       |   (redirected -> _intake/) |      |   repo trees (probable WIP)  |
       +-------------+--------------+      | * Skip when OneDrive lockfile|
                     | file event          |   markers present            |
                     v                     | * Log every move (CSV+SQLite)|
       +------------------------------+    | * Idempotent: re-run = no-op |
       |  odg-sorter (Python daemon)  |    +------------------------------+
       |  * watchdog event loop       |
       |  * rules engine (config)     |
       |  * SHA-256 dedup (SQLite)    |
       |  * startup reconciliation    |
       +-----+--------------+---------+
       confident         ambiguous
             |              |
             v              v
    +--------------+  +---------------------+
    | Move to      |  | Park in             |
    | canonical    |  | _intake/unsorted/   |
    | home (repo   |  | (no sidecar yet)    |
    |  or vault)   |  +----------+----------+
    +------+-------+             |
           |                     |
           v                     |
    +--------------------------------------+
    | Write Obsidian sidecar .md           |
    | -> vault under PARA tree             |
    +------+-------------------------------+
           |
           v
    +--------------------------------------+        Weekly digest job
    | Append SQLite row + CSV log line     | <----- reads SQLite, summarizes
    +--------------------------------------+        _intake/unsorted/, writes
                                                    vault note "Intake review"
```

**Process shape.**
- Single Python process `odg-sorter`, started at logon via Windows Task Scheduler. Also runnable as `odg-sorter daemon` directly.
- State in `data/state.sqlite` (file index, hashes, route history, heartbeat).
- Logs in `data/logs/sort-<YYYY-MM-DD>.csv` — one row per move.
- Config in `config/rules.py` and `config/paths.py` — both version-controlled Python files, not YAML.
- Crash-safe: events processed one at a time, no in-memory queue, missed events caught by startup reconciliation against `state.sqlite`.

**Two-track output.**
- **Confident routes** → file moves to canonical home + sidecar written + log row.
- **Ambiguous files** → park only (no move, no sidecar — just a log row marking it parked) → processed manually during the weekly digest.

## Components

The daemon is a small Python package, ~9 modules, each with one purpose. Names track the data flow.

### Pipeline modules

| Module | Job | Key dependency |
|---|---|---|
| `watcher.py` | `watchdog` event loop; debounces partial-write events (2s window after last `modified` event) | `watchdog` |
| `identify.py` | Extract signals: filename, path, ComfyUI PNG `iTXt`/`tEXt` chunks (prompt/model/seed/LoRAs), EXIF | `Pillow` |
| `router.py` | Apply `config/rules.py` to signals → `Route(dest, template)` or `Park(reason)` | stdlib |
| `mover.py` | Atomic move via `shutil.move`; displaced files → `_quarantine/<date>`; idempotency check | stdlib |
| `sidecar.py` | Render Jinja2 sidecar template; write `.md` into vault path | `Jinja2` |
| `state.py` | SQLite wrapper: hash index, route history, dedup, reconciliation queries, heartbeat | stdlib |

### Standalone modules

| Module | Job |
|---|---|
| `digest.py` | Separate entry point — reads SQLite, summarizes `_intake/unsorted/`, writes a vault note |
| `main.py` | Wires the pipeline; owns the event loop; handles SIGINT and restart cleanly |
| `config/rules.py` | Routing rules — data-only Python (callables permitted for non-trivial matching) |
| `config/paths.py` | Watched directories and destination canonical homes — data-only Python |

### CLI entry points

```
odg-sorter daemon              # start the watcher (Task Scheduler runs this at logon)
odg-sorter sort <path>         # one-shot route a single file (debugging)
odg-sorter digest [--since D]  # generate the weekly digest now
odg-sorter reconcile           # startup-style pass: walk known paths, route any missed
```

### Design choices

- **`config/rules.py` is Python, not YAML/JSON.** Rules can include callables for non-trivial matching (e.g. "ComfyUI workflow contains `dhtwsprite` LoRA in metadata → DHTW sled"). Flat for now; revisit if non-developers ever need to edit rules.
- **`state.sqlite` is the single source of truth for "have we seen this file."** Hash-based, so a file moved out and back routes the same way.
- **`identify`, `router`, `mover`, `sidecar` are pure-ish** — each takes input and returns a result. `watcher`, `main`, `state` are the I/O edges. Makes unit testing cheap.

## Vault sidecar location & shape

### Location — project-bound under PARA's Projects tree

```
ODG_Vault/
  Opal Dragonfly Games/
    Projects/
      DHTW/
        Assets/
          hull_pirate_v7_05.md       <- sidecar
          ...
      TLL/
        Assets/
          probe_hull_concept_03.md
    Resources/
      Asset Gallery/                 <- Dataview-driven cross-cutting views
        By-Tool.md
        By-Project.md
        By-Tier.md
        Recent.md
```

**Why project-bound (not flat or repo-mirror).** Assets share lifecycle with their project (archived project → archived assets). Matches existing PARA discipline. Cross-cutting views come free via Dataview queries over frontmatter — no folder duplication needed.

### Shape — sorter-owned frontmatter, human-owned body

```markdown
---
asset: hull_pirate_v7_05.png
project: dhtw
theme: pirate
tier: rare
palette: matte-black-gold-trim
source-tool: comfyui
workflow: dhtw-sled-v7-locked
model: juggernautXL_v9
seed: 1234567890
prompt: |
  pirate sled hull, matte black with gold leaf trim, ...
hash: sha256:abc123...
size: [1024, 1024]
mime: image/png
ingested: 2026-06-04T14:23:11-05:00
sorter-rule: dhtw-sled-themed-v7
canonical-path: C:\ODG\repos\dhtw\assets\sleds\themes\pirate\hull_pirate_v7_05.png
ingested-from: C:\ODG\_intake\2026-06-04\hull_pirate_v7_05.png
tags: [asset/image, project/dhtw, theme/pirate, tier/rare, workflow/dhtw-sled-v7, tool/comfyui]
---

![[_repos/dhtw/assets/sleds/themes/pirate/hull_pirate_v7_05.png]]

# hull_pirate_v7_05.png

<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->
```

### Key invariants

1. **Asset files stay in repos, not in vault.** Sidecar references via `![[_repos/...]]` — the existing `_repos/` junction in the vault (gitignored per-machine, recreated by `_scripts/`) makes the embed render inline.
2. **Frontmatter is sorter-owned.** Re-running the sorter rewrites it (idempotent when signals unchanged). Anything written outside the frontmatter is safe.
3. **Tags are hierarchical** (`project/dhtw`, `theme/pirate`, etc.) so Obsidian's tag pane is browsable as a tree.
4. **No image data duplicated** — every asset is a single source of truth in its repo.
5. **Cross-cutting views are Dataview, not folders** — `Resources/Asset Gallery/By-Tool.md` is one `dataview` codeblock pulling from frontmatter. We write a handful of these views once.

## Routing rules

### Rule structure

A rule is a Python dict with three parts:

```python
{
    "name": "dhtw-sled-themed-v7",          # logged on every match
    "match": <predicate over signals>,      # callable; returns True/False
    "destination": "repos/dhtw/assets/sleds/themes/{theme}/{filename}",
    "sidecar_template": "dhtw-sled.md.j2",  # None = park, no sidecar
    "confidence": "high",                   # high -> confident track; low/None -> park
}
```

First-match-wins. Rules live in `config/rules.py`. New rules go at the top of their project block.

### Available signals

Extracted by `identify.py` before routing runs:

| Signal | Source |
|---|---|
| `source_dir` | Watcher event |
| `filename`, `extension`, `size` | `os.stat` |
| `hash_sha256` | Computed once, cached in `state.sqlite` |
| `tool` (`comfyui` / `blender` / `inkscape` / `unknown`) | Source dir heuristic + extension |
| `comfyui.workflow`, `comfyui.model`, `comfyui.loras`, `comfyui.prompt`, `comfyui.seed` | PNG `iTXt` / `tEXt` chunks |
| `exif.*` | `Pillow.ExifTags` for jpeg/tiff |
| `blender.source_blend` | `.blend` references from glTF/PNG metadata when present |

### V1 rule set

| # | Rule name | Confidence | Destination |
|---|---|---|---|
| 1 | `dhtw-sled-themed-v7` (ComfyUI + `dhtwsprite` LoRA + theme keyword) | high | `repos/dhtw/assets/sleds/themes/<theme>/` |
| 2 | `dhtw-card-front` (filename `card_NNN_*.png`) | high | `repos/dhtw-tabletop/components/cards/fronts/` |
| 3 | `dhtw-arlo-voice` (filename `taunt_NNN*.{wav,mp3,flac}`) | high | `repos/dhtw/client/assets/audio/arlo/` |
| 4 | `tgc-component-svg` (Inkscape SVG matching TGC component pattern) | high | `repos/dhtw-tabletop/components/<component_type>/` |
| 5 | `tll-comfyui` (ComfyUI workflow name contains `tll`/`probe`/`the-last-light`) | high | `repos/tll/client/assets/generated/<system>/` |
| 6 | `tll-glb-export` (`.glb` in `generated/tll/**` or filename matches `probe_*`, `console_*`, etc.) | high | `repos/tll/client/assets/3d/<system>/` |
| 7 | `dhtw-glb-export` (`.glb` in `generated/dhtw/**` or filename matches DHTW sled/wall naming) | high | `repos/dhtw/client/assets/3d/<system>/` |
| 8 | `blender-source-file` (`.blend` in `_intake/` with a project hint) | high | `repos/<project>/<near-asset>/` |
| 9 | `blender-render-scratch` (`.png`/`.exr` clearly from Blender render, no project hint) | low | stays in `generated/<project>/` if dir signals; else park |
| 10 | `fallback-park` (catch-all) | none | `_intake/unsorted/<date>/` |

### Engine-level safety rule (not a routing rule)

**Any file already inside `repos/<project>/` is never moved by the sorter.** If a Blender script writes straight to its canonical home, the sorter sees it during reconciliation, writes/updates the sidecar, and that's it. Eliminates the risk of the sorter fighting existing pipelines.

### Adding a rule — three steps in `config/rules.py`

1. Add the dict to `RULES` (above the fallback).
2. Add a corresponding Jinja2 template at `templates/sidecars/<name>.md.j2` if confidence is `high`.
3. Add a unit test at `tests/test_routing.py` with a fixture file in `tests/fixtures/`.

No code changes outside `config/` and `templates/`. The router is data-driven.

### Edge cases handled by the router/mover

- **File at destination already exists, different hash** → displaced file → `_quarantine/<date>/`, new file takes canonical path, sidecar updated.
- **File at destination already exists, same hash** → no-op, log `already-routed`, touch sidecar's `ingested` field.
- **Multiple rules match** → first wins; others logged as `also_matched` (useful for tuning).
- **File hash already in `state.sqlite` from a different source path** → re-route (file probably moved out and back); sidecar tracks both `ingested-from` paths.

## Error handling, dedup, restart safety

### Atomic operations

Order: rename → write sidecar → write SQLite row. Each step is independently recoverable:
- `shutil.move()` is atomic when source and dest are on the same volume (the common case — both under `C:\ODG\`).
- Sidecar write happens **after** the move. If it crashes, the move stands; reconciliation on next startup notices a canonical-path file with no SQLite row and writes the sidecar.
- SQLite row commits in its own transaction at the end, so a crash leaves a recoverable state at every step.

### Race conditions

File still being written when watcher fires — two guards:
1. **Debounce window:** wait 2s after the last `modified` event for the same path before processing.
2. **Open-exclusive check:** before reading hash/metadata, try to open the file with an exclusive lock. On Windows `ERROR_SHARING_VIOLATION`, retry up to 5 times with backoff, then defer to reconciliation.

### Dedup

SHA-256 keyed in `state.sqlite`. Three cases:
- Hash unseen → normal route.
- Hash matches an already-routed file at a different path → log `duplicate`, move incoming to `_quarantine/<date>/`, sidecar of canonical updated with `also-ingested-from: <new path>`.
- Hash matches and incoming path *is* the canonical path → no-op (idempotent re-run).

### Reconciliation pass — runs on every daemon startup

- Walk every watched dir → handle any events missed during downtime.
- Walk every canonical destination → for any file without a `state.sqlite` row, identify and write sidecar.
- Walk `_intake/unsorted/` → log a count for the next digest.
- Runtime budget: minutes, not seconds. Acceptable because it only runs at logon.

### WIP guard — the 7-day rule

For any file matched to a destination inside `repos/`, check `mtime > now - 7 days`. If yes → skip, log as `wip-protected`. File stays where it is. Protects in-flight editing from sorter interference. Files in `_intake/` are NEVER WIP-protected (they're inflow, not work).

### OneDrive coexistence

Vault is no longer in OneDrive (per global `CLAUDE.md`), so the v1 vault-write path is unaffected. Remaining concerns:
- Watched paths inside OneDrive (currently none — but a future watched path could be): skip files named `*.tmp`, `*.partial`, `~$*`.
- `_quarantine/` and `_intake/` MUST live outside OneDrive (they currently do — `C:\ODG\_quarantine\`, `C:\ODG\_intake\`).
- Spec captures this so future-Jeff doesn't accidentally point a watched path into OneDrive.

### Restart-safety summary

The daemon can be killed at any moment and restarted with zero data loss because:
- Source files only delete (via `shutil.move`) after the rename succeeds atomically.
- Sidecar writes are idempotent — regenerating from the canonical-path file always produces the same content.
- SQLite is the only durable state, written in transactions.
- Reconciliation closes any gap left by an unclean shutdown.

### Intentionally not built in v1

- No retry queue. A failed move that isn't a transient lock just logs an error and the file stays put — visible in the digest.
- No alerting beyond the digest. If something misbehaves, it shows up in the digest or the logs.
- No file-content validation (e.g. "is this a valid PNG?"). Routing is metadata-driven, not content-driven.

## Testing & verification

### Three test layers

| Layer | Scope | Speed | Runs |
|---|---|---|---|
| Unit | Pure functions: signal extraction, rule predicates, template rendering | <1s | On every save (watch mode) |
| Integration | End-to-end with tmp dirs, real files, real SQLite | 10-30s | On commit + in CI |
| Smoke | Daemon starts → watches a dir → routes one file → shuts down cleanly | ~5s | In CI only |

### Unit tests cover

- `identify.py` — given a fixture PNG with crafted PNG chunks, returns expected signals.
- `router.py` — given a signal dict, returns the expected rule name and destination template.
- `sidecar.py` — given signals + a template, renders expected markdown.
- `state.py` — hash insert/lookup, dedup detection.

### Integration tests — minimum set

- `test_route_dhtw_sled()` — drop fixture into tmp `_intake/`, call `odg-sorter sort <path>`, assert file at expected destination + sidecar exists + SQLite row written.
- `test_dedup_quarantines()` — drop two files with same hash, assert second goes to `_quarantine/`, first sidecar updated.
- `test_wip_guard_skips()` — touch a file in fake `repos/dhtw/assets/`, set mtime to 1 day ago, run sorter, assert file untouched.
- `test_reconciliation_writes_missing_sidecars()` — pre-place a file in canonical destination without a SQLite row, run reconciliation, assert sidecar appears.
- `test_idempotency()` — sort the same file twice, assert no second move, sidecar timestamp updated.
- **Plus one integration test per routing rule** — minimum 10 for v1.

### Smoke test — exercises the watcher itself

- Start the daemon in a thread pointed at a tmp dir.
- Copy a fixture into the watched dir.
- Wait up to 5s (debounce + processing).
- Assert the file landed at the expected destination.
- Send SIGTERM, assert clean shutdown.

### Fixtures

Version-controlled under `tests/fixtures/`. Tiny crafted files:
- `comfyui_dhtw_sled.png` — 1×1 PNG with `tEXt` chunk containing fake ComfyUI workflow JSON.
- `tll_probe_glb.glb` — minimal valid glTF binary.
- `dhtw_card_001_test.svg` — minimal Inkscape SVG.
- `wip_file.png` — for the WIP guard test.
- `dup_a.png`, `dup_b.png` — same content, different names, for dedup test.

Crafted fixtures keep the suite fast and deterministic — no dependency on actual ComfyUI/Blender outputs.

### CI — GitHub Actions

Mirrors the DHTW server pattern:
- Trigger: push to `main` + any PR.
- Steps: `pip install -e .`, `pytest -v`, fail on red.
- PR status check blocks merge on broken sorter.

### Runtime health monitoring

Tests pass ≠ daemon is alive. Mechanism:
- Heartbeat log: daemon writes to `data/heartbeat` every 60s with timestamp + processed-event-count.
- Stale heartbeat = dead daemon. Weekly digest cross-checks: if `now - heartbeat_mtime > 5min`, surface a warning at the top of the digest note.
- No tray icon, no Windows toast, no email alerts in v1. The digest is the channel.

### Manual verification after v1 lands

- Run the daemon for one week.
- On day 7, glance at the digest. Key numbers:
  - `wip-protected` count — should be low if rules cover normal output.
  - `_intake/unsorted/` count — should be small. If huge, rules are too strict.
  - `_quarantine/` count — should mostly be zero. Anything non-zero deserves a look.
- Tune `config/rules.py` based on what shows up. Repeat.

## v1 ship criteria

The spec is done when:

1. Daemon starts at logon, runs invisibly, doesn't break anything (24h uptime under normal use).
2. A new ComfyUI sled output lands → routes to the right `repos/dhtw/assets/sleds/themes/<theme>/` folder + sidecar appears in the vault within 30 seconds.
3. A new ambiguous file → parks in `_intake/unsorted/`, shows up in the weekly digest.
4. The full pytest suite is green and runs in CI on every PR.
5. After one week of running, the digest is informative and the rule set covers ≥80% of new files without parking.

## Path to v2

| Version | Addition | Trigger |
|---|---|---|
| v1.1 | `--backfill` mode: one-shot pass over an existing dir, proposes routes, you approve in batches | When v1 has been stable for ~2 weeks and you want to clean up old scatter |
| v1.2 | Claude classifier hook for `low`-confidence rules | When the digest shows >5 ambiguous files/week consistently |
| v1.3 | Rule-suggestion in digest: "you re-routed 4 files matching X pattern this week — add a rule?" | After enough manual park corrections that a pattern emerges |
| v2.0 | Sub-project G (Studio Glue): cross-project dashboard surfacing asset counts, recent intake, digest deltas | Once 2+ sub-projects (Notes, Godot pipeline) also produce sidecar data the dashboard can consume |
| v3.0 | CLIP embeddings + semantic visual search | Only if Obsidian tag search proves insufficient for "find that thing" |

## Connections to other studio sub-projects

- **B (Cross-project Art Pipeline)** consumes vault sidecars to know "which DHTW workflow produced what." Easier to build once sidecars exist.
- **C (Note-taking Pipeline)** collapses INTO this one — sidecars ARE the note-taking layer for generated assets. Remaining "Notes" work is daily journals + decision logs.
- **D (Godot Dev Pipeline)** can use the same SQLite + sidecar model for "which sled `.glb` is used in which scene" — natural extension.
- **E (Coding/CI Pipeline)** is independent.

## Open questions

None blocking. Items confirmed during brainstorming:
- Success shape: fire-and-forget routing + Obsidian search find-layer.
- Ambiguity rule: park in `_intake/unsorted/`, weekly digest.
- Find-layer: Obsidian sidecars (collapses Asset Mgmt + Notes sub-projects).
- Backfill: forward-only in v1.
- Trigger: continuous watcher (Task Scheduler at logon).
- Implementation: pure Python daemon (Approach 1).
- 3D pipeline: Blender (local) + ComfyUI 2D (local) — no Tripo/Meshy/Leonardo.
- Hard rule: never move files inside `repos/<project>/`.

Items to revisit at the implementation-plan stage (next step):
- Exact ComfyUI output directory path(s) — needs a confirmation from the actual ComfyUI install.
- Exact filename patterns for rules 1–8 — needs sample files from current generators to pin regexes.
- Whether `_intake/unsorted/` digest cadence should be weekly, twice-weekly, or driven by count (e.g. "digest when unsorted/ hits 20 files").
