"""Dashboard payload conformance test.

The infra-context-dashboard (sibling Astro+Prefab app) produces a JSON
payload that must validate against tipi/contract/consciousness-interface.json.
This test holds a representative fixture and asserts conformance.

If the dashboard's wire format drifts, this test fails BEFORE the dashboard's
snapshot test does — catching the break at the contract boundary.

If the schema tightens (e.g. new required field), update the fixture
deliberately. Don't loosen the fixture to silence this test.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tipi.scripts.generate_schema import SCHEMA_PATH

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "dashboard_payload.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def test_dashboard_payload_validates_as_health_snapshot(schema, fixture):
    """A realistic dashboard payload must validate against HealthSnapshot."""
    sub = {**schema["$defs"]["HealthSnapshot"], "$defs": schema["$defs"]}
    jsonschema.validate(instance=fixture, schema=sub)


def test_dashboard_payload_has_all_expected_top_level_fields(fixture):
    """Early-warning smoke check: fixture keys match the wire contract."""
    expected = {
        "handoff_freshness",
        "ob1_sync_status",
        "session_lock_state",
        "project_memory_entries",
    }
    assert set(fixture.keys()) == expected


def test_dashboard_payload_backend_is_known(fixture):
    """Backend enum must be one of obn/khoj/ob1/stub — flag sooner if dashboard invents a new one."""
    assert fixture["ob1_sync_status"]["backend"] in {"obn", "khoj", "ob1", "stub"}
