from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable


class RelationStatus(str, Enum):
    PRESERVED = "PRESERVED"
    LAWFULLY_CHANGED = "LAWFULLY_CHANGED"
    LOST = "LOST"
    INVERTED = "INVERTED"
    UNKNOWN = "UNKNOWN"


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    ATTENUATE = "ATTENUATE"
    HOLD = "HOLD"
    DENY = "DENY"


class DependencyState(str, Enum):
    TRUSTED = "TRUSTED"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, order=True)
class RelationBinding:
    relation_id: str
    required_for_actions: tuple[str, ...] = ()
    load_bearing: bool = True

    def __post_init__(self) -> None:
        if not self.relation_id.strip():
            raise ValueError("relation_id must be non-empty")
        object.__setattr__(self, "required_for_actions", _canonical_tuple(self.required_for_actions))


@dataclass(frozen=True)
class AuthorityEnvelope:
    authority_id: str
    source_object_hash: str
    permitted_actions: tuple[str, ...]
    prohibited_actions: tuple[str, ...] = ()
    relation_bindings: tuple[RelationBinding, ...] = ()
    consequence_class: str = "LOW"
    expiry: str | None = None
    provenance: str = ""

    def __post_init__(self) -> None:
        if not self.authority_id.strip():
            raise ValueError("authority_id must be non-empty")
        if not self.source_object_hash.strip():
            raise ValueError("source_object_hash must be non-empty")
        permitted = _canonical_tuple(self.permitted_actions)
        prohibited = _canonical_tuple(self.prohibited_actions)
        if set(permitted) & set(prohibited):
            raise ValueError("an action cannot be both permitted and prohibited")
        object.__setattr__(self, "permitted_actions", permitted)
        object.__setattr__(self, "prohibited_actions", prohibited)
        binding_ids = [binding.relation_id for binding in self.relation_bindings]
        duplicates = sorted({rid for rid in binding_ids if binding_ids.count(rid) > 1})
        if duplicates:
            raise ValueError(f"duplicate relation bindings: {duplicates}")
        object.__setattr__(
            self,
            "relation_bindings",
            tuple(sorted(self.relation_bindings, key=lambda b: b.relation_id)),
        )

    def canonical_payload(self) -> dict:
        return {
            "authority_id": self.authority_id,
            "source_object_hash": self.source_object_hash,
            "permitted_actions": list(self.permitted_actions),
            "prohibited_actions": list(self.prohibited_actions),
            "relation_bindings": [
                {
                    "relation_id": b.relation_id,
                    "required_for_actions": list(b.required_for_actions),
                    "load_bearing": b.load_bearing,
                }
                for b in self.relation_bindings
            ],
            "consequence_class": self.consequence_class,
            "expiry": self.expiry,
            "provenance": self.provenance,
        }

    def digest(self) -> str:
        return _digest(self.canonical_payload())


@dataclass(frozen=True)
class TransformationContract:
    transform_id: str
    transform_kind: str
    source_carrier: str
    target_carrier: str
    frozen_relations: tuple[str, ...]
    loss_policy: str = "FAIL_CLOSED"

    def __post_init__(self) -> None:
        if not self.transform_id.strip():
            raise ValueError("transform_id must be non-empty")
        raw_relations = [str(value).strip() for value in self.frozen_relations if str(value).strip()]
        duplicates = sorted({rid for rid in raw_relations if raw_relations.count(rid) > 1})
        if duplicates:
            raise ValueError(f"duplicate frozen relations: {duplicates}")
        object.__setattr__(self, "frozen_relations", tuple(sorted(raw_relations)))

    def canonical_payload(self) -> dict:
        return {
            "transform_id": self.transform_id,
            "transform_kind": self.transform_kind,
            "source_carrier": self.source_carrier,
            "target_carrier": self.target_carrier,
            "frozen_relations": list(self.frozen_relations),
            "loss_policy": self.loss_policy,
        }

    def digest(self) -> str:
        return _digest(self.canonical_payload())


@dataclass(frozen=True)
class TransformationResult:
    statuses: tuple[tuple[str, RelationStatus], ...]
    proposed_actions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        normalized: list[tuple[str, RelationStatus]] = []
        for relation_id, status in self.statuses:
            if relation_id in seen:
                raise ValueError(f"duplicate relation status: {relation_id}")
            seen.add(relation_id)
            normalized.append((relation_id, RelationStatus(status)))
        normalized.sort(key=lambda item: item[0])
        object.__setattr__(self, "statuses", tuple(normalized))
        object.__setattr__(self, "proposed_actions", _canonical_tuple(self.proposed_actions))

    @classmethod
    def from_mapping(
        cls,
        statuses: dict[str, RelationStatus | str],
        proposed_actions: Iterable[str] = (),
    ) -> "TransformationResult":
        return cls(
            tuple((key, RelationStatus(value)) for key, value in statuses.items()),
            tuple(proposed_actions),
        )

    def status_map(self) -> dict[str, RelationStatus]:
        return dict(self.statuses)

    def canonical_payload(self) -> dict:
        return {
            "statuses": [[rid, status.value] for rid, status in self.statuses],
            "proposed_actions": list(self.proposed_actions),
        }

    def digest(self) -> str:
        return _digest(self.canonical_payload())


@dataclass(frozen=True)
class AuthorityReceipt:
    authority_id: str
    authority_before: tuple[str, ...]
    authority_after: tuple[str, ...]
    transform_id: str
    transform_digest: str
    relation_results: tuple[tuple[str, RelationStatus], ...]
    verdict: Verdict
    reasons: tuple[str, ...]
    previous_receipt_hash: str | None = None
    valid_at_issuance: bool = True
    current_reliance: DependencyState = DependencyState.TRUSTED

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_before", _canonical_tuple(self.authority_before))
        object.__setattr__(self, "authority_after", _canonical_tuple(self.authority_after))
        object.__setattr__(self, "reasons", tuple(self.reasons))
        if not set(self.authority_after).issubset(set(self.authority_before)):
            raise ValueError("authority_after must be a subset of authority_before")

    def canonical_payload(self) -> dict:
        return {
            "authority_id": self.authority_id,
            "authority_before": list(self.authority_before),
            "authority_after": list(self.authority_after),
            "transform_id": self.transform_id,
            "transform_digest": self.transform_digest,
            "relation_results": [[rid, status.value] for rid, status in self.relation_results],
            "verdict": self.verdict.value,
            "reasons": list(self.reasons),
            "previous_receipt_hash": self.previous_receipt_hash,
            "valid_at_issuance": self.valid_at_issuance,
            "current_reliance": self.current_reliance.value,
        }

    def digest(self) -> str:
        return _digest(self.canonical_payload())


def _canonical_tuple(values: Iterable[str]) -> tuple[str, ...]:
    result = sorted({str(value).strip() for value in values if str(value).strip()})
    return tuple(result)


def _digest(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()
