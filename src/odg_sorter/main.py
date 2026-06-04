import logging
import shutil
import signal
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from odg_sorter.config.paths import QUARANTINE, REPOS, STUDIO_ROOT, VAULT_PROJECTS, WATCHED_PATHS
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
        if path.resolve() != park_dest.resolve() and not park_dest.exists():
            shutil.move(str(path), str(park_dest))
        state.record_park(signals.hash_sha256, park_dest, reason=decision.reason)
        log.info("parked path=%s reason=%s", park_dest, decision.reason)
        return "parked"

    assert isinstance(decision, Route)
    move_result = move_into_canonical_home(
        path,
        decision.destination,
        quarantine_root=QUARANTINE,
        repos_root=REPOS,
    )
    if isinstance(move_result, SkipResult):
        # If the source is already at its canonical home, still write the sidecar
        # so the file shows up in the vault find-layer (Blender scripts often
        # write directly to repos/<project>/...).
        if move_result.reason == "source-inside-repos" and path == decision.destination:
            _write_sidecar_for(decision, signals, source=path)
            state.record_route(
                signals.hash_sha256,
                source=path,
                destination=path,
                rule=decision.rule,
            )
            log.info("in-place routed rule=%s dest=%s", decision.rule, path)
            return "routed"
        state.record_park(signals.hash_sha256, path, reason=move_result.reason)
        log.info("skipped path=%s reason=%s", path, move_result.reason)
        return move_result.reason

    _write_sidecar_for(decision, signals, source=path)
    state.record_route(
        signals.hash_sha256,
        source=path,
        destination=move_result.destination,
        rule=decision.rule,
    )
    log.info("routed rule=%s dest=%s", decision.rule, move_result.destination)
    return "routed"


def _write_sidecar_for(decision: "Route", signals, *, source: Path) -> None:
    sidecar_path = _sidecar_path_for(decision, signals)
    ctx = SidecarContext(
        template=decision.sidecar_template,
        sidecar_path=sidecar_path,
        data=_sidecar_data(decision, signals, source=source),
    )
    write_sidecar(ctx)


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


def run_daemon() -> int:
    from odg_sorter.reconcile import reconcile
    from odg_sorter.watcher import Watcher

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
