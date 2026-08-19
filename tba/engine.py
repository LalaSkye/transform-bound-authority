from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import (
    AuthorityEnvelope,
    AuthorityReceipt,
    DependencyState,
    RelationStatus,
    TransformationContract,
    TransformationResult,
    Verdict,
)


_SAFE = {RelationStatus.PRESERVED, RelationStatus.LAWFULLY_CHANGED}


def attenuate_authority(
    envelope: AuthorityEnvelope,
    contract: TransformationContract,
    result: TransformationResult,
    *,
    previous_receipt_hash: str | None = None,
) -> AuthorityReceipt:
    """Derive downstream executable authority from relation-survival evidence.

    The kernel does not decide semantic truth. It consumes a declared
    TransformationResult and applies fail-closed authority rules.
    """
    status_map = result.status_map()
    relation_ids = set(contract.frozen_relations)

    missing_load_bearing = sorted(
        binding.relation_id
        for binding in envelope.relation_bindings
        if binding.load_bearing and binding.relation_id not in relation_ids
    )
    if missing_load_bearing:
        raise ValueError(
            "load-bearing relation bindings missing from frozen_relations: "
            f"{missing_load_bearing}"
        )

    unknown_extra = set(status_map) - relation_ids
    if unknown_extra:
        raise ValueError(f"result contains undeclared relations: {sorted(unknown_extra)}")

    normalized_results: list[tuple[str, RelationStatus]] = []
    for relation_id in contract.frozen_relations:
        normalized_results.append(
            (relation_id, status_map.get(relation_id, RelationStatus.UNKNOWN))
        )

    before = set(envelope.permitted_actions)
    after = set(before)
    reasons: list[str] = []

    binding_by_relation = {binding.relation_id: binding for binding in envelope.relation_bindings}

    after.difference_update(envelope.prohibited_actions)

    any_inverted = False
    any_unknown_load_bearing = False
    any_authority_loss = False

    for relation_id, status in normalized_results:
        binding = binding_by_relation.get(relation_id)
        if binding is None:
            if status not in _SAFE:
                reasons.append(f"non-governing relation {relation_id} = {status.value}")
            continue

        affected = set(binding.required_for_actions)
        if status not in _SAFE:
            removed = after & affected
            if removed:
                any_authority_loss = True
                after.difference_update(affected)
                reasons.append(
                    f"{status.value}: {relation_id} removed authority for {sorted(removed)}"
                )
            elif binding.load_bearing:
                reasons.append(f"{status.value}: load-bearing relation {relation_id}")

        if binding.load_bearing and status == RelationStatus.INVERTED:
            any_inverted = True
        if binding.load_bearing and status == RelationStatus.UNKNOWN:
            any_unknown_load_bearing = True

    proposed = set(result.proposed_actions)
    gained = proposed - before
    prohibited_attempts = proposed & set(envelope.prohibited_actions)
    surviving_proposal = proposed - after

    if gained:
        reasons.append(f"authority gain attempt: {sorted(gained)}")
    if prohibited_attempts:
        reasons.append(f"prohibited action attempted: {sorted(prohibited_attempts)}")
    if surviving_proposal:
        reasons.append(f"proposal exceeds surviving authority: {sorted(surviving_proposal)}")

    if gained or prohibited_attempts or any_inverted:
        verdict = Verdict.DENY
    elif any_unknown_load_bearing:
        verdict = Verdict.HOLD
    elif proposed and not proposed.issubset(after):
        verdict = Verdict.HOLD
    elif any_authority_loss:
        verdict = Verdict.ATTENUATE if after else Verdict.HOLD
    else:
        verdict = Verdict.ALLOW

    if not reasons:
        reasons.append("all frozen authority-bearing relations survived")

    return AuthorityReceipt(
        authority_id=envelope.authority_id,
        authority_before=tuple(before),
        authority_after=tuple(after),
        transform_id=contract.transform_id,
        transform_digest=_transform_digest(contract, result),
        relation_results=tuple(normalized_results),
        verdict=verdict,
        reasons=tuple(reasons),
        previous_receipt_hash=previous_receipt_hash,
    )


def propagate_chain(
    envelope: AuthorityEnvelope,
    steps: Iterable[tuple[TransformationContract, TransformationResult]],
) -> tuple[AuthorityReceipt, ...]:
    receipts: list[AuthorityReceipt] = []
    current = envelope
    previous_hash: str | None = None

    for contract, result in steps:
        receipt = attenuate_authority(
            current,
            contract,
            result,
            previous_receipt_hash=previous_hash,
        )
        receipts.append(receipt)
        previous_hash = receipt.digest()

        current = AuthorityEnvelope(
            authority_id=current.authority_id,
            source_object_hash=current.source_object_hash,
            permitted_actions=receipt.authority_after,
            prohibited_actions=current.prohibited_actions,
            relation_bindings=current.relation_bindings,
            consequence_class=current.consequence_class,
            expiry=current.expiry,
            provenance=current.provenance,
        )

    return tuple(receipts)


def reassess_reliance(
    receipt: AuthorityReceipt,
    dependency_state: DependencyState,
) -> AuthorityReceipt:
    """Preserve issuance history while changing only current reliance."""
    if dependency_state == DependencyState.TRUSTED:
        new_state = DependencyState.TRUSTED
    elif dependency_state == DependencyState.REVOKED:
        new_state = DependencyState.REVOKED
    else:
        new_state = DependencyState.UNKNOWN
    return replace(receipt, current_reliance=new_state)


def _transform_digest(
    contract: TransformationContract,
    result: TransformationResult,
) -> str:
    import hashlib
    import json

    payload = {
        "contract": contract.canonical_payload(),
        "result": result.canonical_payload(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
