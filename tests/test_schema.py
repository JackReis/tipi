"""Contract tests for consciousness-interface.json.

Two things to guard:

1. The generated JSON Schema matches what's on disk (drift detection).
   CI fails if someone edits interface.py or health.py without rerunning
   the generator.

2. The stub data serializes to something the schema accepts. This is the
   smoke test for the shared contract — if this passes, both enclosures
   (vs-tipi + infra-context-dashboard) can validate their data against
   the same schema.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import jsonschema
import pytest

from tipi.mcp.consciousness.stubs import (
    StubBeliefLedger,
    StubBodyReader,
    StubHealthReader,
    StubMindIndex,
    body_state_snapshot,
)
from tipi.scripts.generate_schema import SCHEMA_PATH, build_schema


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def test_schema_on_disk_matches_generated():
    """Drift guard: regenerate in-memory + compare byte-for-byte with on-disk."""
    generated = build_schema()
    on_disk = json.loads(SCHEMA_PATH.read_text())
    assert generated == on_disk, (
        "consciousness-interface.json is stale. "
        "Run: .venv/bin/python -m tipi.scripts.generate_schema"
    )


def test_schema_defines_all_expected_roots(schema):
    expected = {
        "Belief",
        "MindRecord",
        "BodyState",
        "HandoffFreshness",
        "OB1SyncStatus",
        "SessionLock",
        "PerSessionMemoryEntry",
        "ProjectMemoryEntries",
        "HealthSnapshot",
    }
    assert expected.issubset(schema["$defs"].keys())


def _jsonify(data):
    """Round-trip through JSON to coerce tuples→lists, matching wire format.

    `dataclasses.asdict` preserves tuples; JSON Schema expects arrays. MCP
    serialization encodes tuples as JSON arrays. Round-tripping through json
    makes the test reflect what the MCP server actually puts on the wire.
    """
    return json.loads(json.dumps(data))


def _validate(data, schema: dict, root: str) -> None:
    """Validate `data` against the `$defs.<root>` sub-schema."""
    sub = {**schema["$defs"][root], "$defs": schema["$defs"]}
    jsonschema.validate(instance=_jsonify(data), schema=sub)


def test_stub_belief_matches_schema(schema):
    beliefs = StubBeliefLedger().list_beliefs(limit=5)
    for b in beliefs:
        _validate(asdict(b), schema, "Belief")


def test_stub_mind_record_matches_schema(schema):
    results = StubMindIndex().search(query="tipi")
    for r in results:
        _validate(asdict(r), schema, "MindRecord")


def test_stub_body_state_matches_schema(schema):
    snap = body_state_snapshot()
    _validate(asdict(snap), schema, "BodyState")


def test_stub_health_snapshot_matches_schema(schema):
    snap = StubHealthReader().snapshot()
    payload = {
        "handoff_freshness": asdict(snap.handoff_freshness),
        "ob1_sync_status": asdict(snap.ob1_sync_status),
        "session_lock_state": [asdict(s) for s in snap.session_lock_state],
        "project_memory_entries": asdict(snap.project_memory_entries),
    }
    _validate(payload, schema, "HealthSnapshot")


def test_schema_enforces_backend_enum(schema):
    """ob1_sync_status.backend must be one of the known backends."""
    bad = {
        "backend": "frobnicator",
        "last_sync": "2026-04-21T00:00:00Z",
        "ok": True,
        "record_count": 0,
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(bad, schema, "OB1SyncStatus")
