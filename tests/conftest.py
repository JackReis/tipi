"""Test fixtures shared across the suite."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _tipi_vault_root_set(monkeypatch):
    """Set TIPI_VAULT_ROOT to a harmless value for every test.

    run_intent() now requires TIPI_VAULT_ROOT — tests that hit dispatch
    need the var set. Individual tests that need to verify the "missing
    env var" error can monkeypatch.delenv() inside the test body.
    """
    monkeypatch.setenv("TIPI_VAULT_ROOT", "/tmp/test-vault")
    yield
