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
