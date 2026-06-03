"""Generate tipi/contract/consciousness-interface.json from the Python dataclasses.

This is the mechanical transform that produces the JSON Schema both
enclosures (vs-tipi, infra-context-dashboard) validate against. CI
should fail if the schema and the Python source drift.

Usage:
    .venv/bin/python -m tipi.scripts.generate_schema

Writes: tipi/contract/consciousness-interface.json
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from tipi.mcp.consciousness.health import (
    HandoffFreshness,
    HealthSnapshot,
    OB1SyncStatus,
    PerSessionMemoryEntry,
    ProjectMemoryEntries,
    SessionLock,
)
from tipi.mcp.consciousness.interface import (
    Belief,
    BodyState,
    Check,
    Disputation,
    MindRecord,
    Obiectio,
    Responsio,
    SedContra,
)

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contract"
SCHEMA_PATH = SCHEMA_DIR / "consciousness-interface.json"

# The top-level types consumers validate against. Add new types here as
# the contract grows.
ROOTS: dict[str, type] = {
    # Interface (body / mind / spirit reads)
    "Belief": Belief,
    "MindRecord": MindRecord,
    "BodyState": BodyState,
    # Spirit-layer dialectic vocabulary — the producer-side discipline that
    # gives Beliefs enough specificity to be measured. See:
    # ~/Documents/=notes/docs/conventions/dialectic-vocabulary.md
    "Check": Check,
    "Obiectio": Obiectio,
    "SedContra": SedContra,
    "Responsio": Responsio,
    "Disputation": Disputation,
    # Health (shared cross-enclosure fields)
    "HandoffFreshness": HandoffFreshness,
    "OB1SyncStatus": OB1SyncStatus,
    "SessionLock": SessionLock,
    "PerSessionMemoryEntry": PerSessionMemoryEntry,
    "ProjectMemoryEntries": ProjectMemoryEntries,
    "HealthSnapshot": HealthSnapshot,
}


def _ensure_dataclass_description(schema: dict[str, Any], tp: type) -> None:
    """Keep schema descriptions stable across Pydantic minor versions."""
    if "description" not in schema and tp.__doc__:
        schema["description"] = inspect.cleandoc(tp.__doc__)


def build_schema() -> dict[str, Any]:
    """Build the JSON Schema document with all ROOTS as named definitions."""
    definitions: dict[str, Any] = {}
    for name, tp in ROOTS.items():
        schema = TypeAdapter(tp).json_schema(ref_template="#/$defs/{model}")
        # pydantic nests generated refs under $defs inside each root; hoist them.
        inner_defs = schema.pop("$defs", {})
        for k, v in inner_defs.items():
            if isinstance(v, dict):
                inner_type = ROOTS.get(k)
                if inner_type is not None:
                    _ensure_dataclass_description(v, inner_type)
            definitions.setdefault(k, v)
        _ensure_dataclass_description(schema, tp)
        definitions[name] = schema
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "tipi/contract/consciousness-interface.json",
        "title": "tipi consciousness interface",
        "description": (
            "Shared contract between tipi + vs-tipi (IDE enclosure) and the "
            "infra-context-dashboard (browser enclosure). Generated from "
            "tipi/mcp/consciousness/*.py — do not edit by hand."
        ),
        "$defs": definitions,
    }


def write_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    schema = build_schema()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    return schema


def main() -> None:
    schema = write_schema()
    print(f"wrote {SCHEMA_PATH} with {len(schema['$defs'])} definitions")


if __name__ == "__main__":
    main()
