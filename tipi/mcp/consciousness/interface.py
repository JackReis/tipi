"""Consciousness interface — the integration seam between tipi and the three layers.

This module defines the SOURCE of truth for the shared consciousness contract.
The JSON Schema shipped in `tipi/contract/consciousness-interface.json` (future
plan Task 9.2) is generated from these definitions.

See the vault ADR at `~/Documents/=notes/docs/architecture/three-layer-consciousness.md`
for the architecture rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Spirit layer — beliefs from the future OB1 belief-ledger
#
# Beliefs are derived (never raw captures) and load-bearing by design. The
# dialectic-vocabulary subtypes below give a belief enough specificity to be
# *measured* — verifier/falsifier turn empirical claims into runnable checks;
# the disputation block carries scholastic-form contestation for normative
# claims. Synthesis: an unexamined claim does not exist (it's superposition
# the observer can't collapse). See:
#   ~/Documents/=notes/docs/conventions/dialectic-vocabulary.md
#   ~/Documents/=notes/docs/conventions/agent-observer-principle.md
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Check:
    """A runnable verifier or falsifier command for a Belief.

    Mirrors peer-grill claims.schema.json: cmd is a shell command,
    expect is a comparator string (literal | >N | matches:/RE/ | contains: |
    sha256:HEX | lines:OP). Deterministic, sandbox-friendly, retryable.
    """

    cmd: str
    expect: str
    timeout_seconds: int = 10
    note: str = ""


@dataclass(frozen=True)
class Obiectio:
    """A numbered objection raised against a Belief's quaestio.

    Latin disputation form per scholastic tradition (Aquinas Summa I-I).
    Each obiectio cites a source the asker can verify.
    """

    n: int
    argument: str
    source: str = ""
    raised_by: str = ""  # agent slug


@dataclass(frozen=True)
class SedContra:
    """The single strongest counter to the obiectiones.

    Aquinas reserves this for the most authoritative source. Only one
    sed contra per disputation, by convention.
    """

    argument: str
    source: str = ""
    raised_by: str = ""


@dataclass(frozen=True)
class Responsio:
    """A reply to a specific obiectio number, completing the disputation."""

    to: int  # obiectio number this reply addresses
    reply: str


@dataclass(frozen=True)
class Disputation:
    """Scholastic quaestio-form structured disputation for high-stakes beliefs.

    Use only when a belief's stakes earn the structural overhead. Everyday
    beliefs ratify with verifier + ALETHEIA stamp; contested ones get the
    full quaestio / obiectiones / sed contra / respondeo / responsiones
    treatment, with a sha256 attestation when both peers ratify the merged
    statement.
    """

    quaestio: str
    obiectiones: tuple[Obiectio, ...] = ()
    sed_contra: SedContra | None = None
    respondeo: str = ""
    responsiones: tuple[Responsio, ...] = ()
    aletheia_sha256: str = ""  # ALETHEIA stamp once both peers RATIFY


@dataclass(frozen=True)
class Belief:
    """A durable, subjectively-weighted claim in the belief ledger.

    Beliefs are derived — never raw captures. A write to spirit implies a
    reflection pass over mind. Per the synthesis at the top of this section:
    an unexamined claim does not exist; a Belief is brought into existence
    by the act of grounding it.

    Optional dialectic fields (verifier, falsifier, disputation, confidence,
    aletheia_sha256) carry the producer-side discipline. They are optional
    for backwards-compat with existing belief data but should be populated
    for any belief that participates in cross-agent reconciliation.
    """

    id: str
    claim: str
    subjective_weight: float  # 0.0 - 1.0
    derived_from: tuple[str, ...] = ()  # mind-layer record IDs
    timestamp: str = ""  # ISO 8601
    confidence: str = ""  # high | medium | low (mirrors peer-grill enum)
    verifier: Check | None = None
    falsifier: Check | None = None
    disputation: Disputation | None = None
    aletheia_sha256: str = ""  # sha256(canonical statement) once ratified


@runtime_checkable
class BeliefLedger(Protocol):
    """Read surface over the spirit layer."""

    def list_beliefs(self, limit: int = 20) -> list[Belief]: ...
    def search_beliefs(self, query: str, limit: int = 5) -> list[Belief]: ...


# ---------------------------------------------------------------------------
# Mind layer — knowledge records from OBn / Khoj / knowledge-graph
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MindRecord:
    """A retrieval hit from the mind layer (backend-agnostic).

    `backend` discriminates the source: obn | khoj | knowledge-graph | ...
    """

    id: str
    content: str
    score: float
    backend: str = "obn"
    metadata: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class MindIndex(Protocol):
    """Read surface over the mind layer. Implementation may back to OBn or Khoj."""

    def search(self, query: str, limit: int = 10) -> list[MindRecord]: ...


# ---------------------------------------------------------------------------
# Body layer — the neural-garden vault + sibling repos + OS
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BodyState:
    """Snapshot of the body substrate."""

    repos: tuple[str, ...] = ()
    recent_changes: tuple[dict[str, str], ...] = ()


@runtime_checkable
class BodyReader(Protocol):
    """Read surface over the body layer."""

    def list_repos(self) -> list[str]: ...
    def recent_changes(self, repo: str, limit: int = 5) -> list[dict[str, str]]: ...
