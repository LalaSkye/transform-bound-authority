from __future__ import annotations

from .engine import attenuate_authority
from .models import (
    AuthorityEnvelope,
    RelationBinding,
    RelationStatus,
    TransformationContract,
    TransformationResult,
)
from .ungated import naive_copy_authority


def main() -> None:
    envelope = AuthorityEnvelope(
        authority_id="auth-demo-001",
        source_object_hash="sha256:source",
        permitted_actions=("DRAFT_EMAIL", "SEND_EMAIL"),
        prohibited_actions=(),
        relation_bindings=(
            RelationBinding(
                relation_id="human_approval_before_send",
                required_for_actions=("SEND_EMAIL",),
            ),
        ),
        provenance="synthetic-demo",
    )

    contract = TransformationContract(
        transform_id="compress-001",
        transform_kind="compression",
        source_carrier="instruction",
        target_carrier="summary",
        frozen_relations=("human_approval_before_send",),
    )

    corrupted = TransformationResult.from_mapping(
        {"human_approval_before_send": RelationStatus.LOST},
        proposed_actions=("SEND_EMAIL",),
    )

    receipt = attenuate_authority(envelope, contract, corrupted)
    ungated = naive_copy_authority(envelope)

    print("Transform-Bound Authority v0.1")
    print(f"before:  {envelope.permitted_actions}")
    print("status:  LOST human_approval_before_send")
    print(f"after:   {receipt.authority_after}")
    print(f"verdict: {receipt.verdict.value}")
    print(f"ungated SEND_EMAIL survives: {'SEND_EMAIL' in ungated}")
    print(f"gated SEND_EMAIL survives:   {'SEND_EMAIL' in receipt.authority_after}")
    print(f"receipt: {receipt.digest()}")


if __name__ == "__main__":
    main()
