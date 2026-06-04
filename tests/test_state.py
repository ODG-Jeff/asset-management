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
