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
