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
