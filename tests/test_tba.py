import unittest

from tba import (
    AuthorityEnvelope,
    DependencyState,
    RelationBinding,
    RelationStatus,
    TransformationContract,
    TransformationResult,
    Verdict,
    attenuate_authority,
    propagate_chain,
    reassess_reliance,
)
from tba.ungated import naive_copy_authority


def base_envelope():
    return AuthorityEnvelope(
        authority_id="auth-001",
        source_object_hash="sha256:source",
        permitted_actions=("DRAFT_EMAIL", "ATTACH_REPORT", "SEND_EMAIL"),
        prohibited_actions=("DELETE_ARCHIVE",),
        relation_bindings=(
            RelationBinding(
                "human_approval_before_send",
                ("SEND_EMAIL",),
            ),
            RelationBinding(
                "ask_before_attach",
                ("ATTACH_REPORT",),
            ),
        ),
        provenance="synthetic",
    )


def contract(transform_id="t-001", relations=("human_approval_before_send", "ask_before_attach")):
    return TransformationContract(
        transform_id=transform_id,
        transform_kind="compression",
        source_carrier="instruction",
        target_carrier="summary",
        frozen_relations=relations,
    )


class TransformBoundAuthorityTests(unittest.TestCase):
    def test_t0_identity_preserves_authority(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.PRESERVED,
            "ask_before_attach": RelationStatus.PRESERVED,
        })
        receipt = attenuate_authority(base_envelope(), contract(), result)
        self.assertEqual(receipt.verdict, Verdict.ALLOW)
        self.assertEqual(set(receipt.authority_after), set(base_envelope().permitted_actions))

    def test_t1_lawful_change_preserves_authority(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.LAWFULLY_CHANGED,
            "ask_before_attach": RelationStatus.PRESERVED,
        })
        receipt = attenuate_authority(base_envelope(), contract(), result)
        self.assertEqual(receipt.verdict, Verdict.ALLOW)
        self.assertIn("SEND_EMAIL", receipt.authority_after)

    def test_t2_non_governing_detail_loss_does_not_reduce_authority(self):
        e = AuthorityEnvelope(
            authority_id="auth-non-governing",
            source_object_hash="sha256:source",
            permitted_actions=("DRAFT_EMAIL", "SEND_EMAIL"),
            relation_bindings=(
                RelationBinding("scene_detail", (), load_bearing=False),
            ),
            provenance="synthetic",
        )
        c = contract(relations=("scene_detail",))
        result = TransformationResult.from_mapping({"scene_detail": RelationStatus.LOST})
        receipt = attenuate_authority(e, c, result)
        self.assertEqual(receipt.verdict, Verdict.ALLOW)
        self.assertEqual(set(receipt.authority_after), set(e.permitted_actions))

    def test_t3_lost_governing_constraint_attenuates(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.PRESERVED,
            "ask_before_attach": RelationStatus.LOST,
        })
        receipt = attenuate_authority(base_envelope(), contract(), result)
        self.assertEqual(receipt.verdict, Verdict.ATTENUATE)
        self.assertNotIn("ATTACH_REPORT", receipt.authority_after)
        self.assertIn("SEND_EMAIL", receipt.authority_after)

    def test_t4_inverted_governing_constraint_denies(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.INVERTED,
            "ask_before_attach": RelationStatus.PRESERVED,
        }, proposed_actions=("SEND_EMAIL",))
        receipt = attenuate_authority(base_envelope(), contract(), result)
        self.assertEqual(receipt.verdict, Verdict.DENY)
        self.assertNotIn("SEND_EMAIL", receipt.authority_after)

    def test_t5_costume_attack_can_fail_relation_check(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.LOST,
            "ask_before_attach": RelationStatus.PRESERVED,
        }, proposed_actions=("SEND_EMAIL",))
        receipt = attenuate_authority(base_envelope(), contract(), result)
        self.assertEqual(receipt.verdict, Verdict.HOLD)
        self.assertNotIn("SEND_EMAIL", receipt.authority_after)

    def test_t6_authority_gain_is_denied(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.PRESERVED,
            "ask_before_attach": RelationStatus.PRESERVED,
        }, proposed_actions=("PAY_INVOICE",))
        receipt = attenuate_authority(base_envelope(), contract(), result)
        self.assertEqual(receipt.verdict, Verdict.DENY)
        self.assertNotIn("PAY_INVOICE", receipt.authority_after)

    def test_t7_chain_is_monotonic(self):
        e = base_envelope()
        steps = [
            (
                contract("t-a"),
                TransformationResult.from_mapping({
                    "human_approval_before_send": RelationStatus.PRESERVED,
                    "ask_before_attach": RelationStatus.LOST,
                }),
            ),
            (
                contract("t-b"),
                TransformationResult.from_mapping({
                    "human_approval_before_send": RelationStatus.LOST,
                    "ask_before_attach": RelationStatus.UNKNOWN,
                }),
            ),
        ]
        receipts = propagate_chain(e, steps)
        prior = set(e.permitted_actions)
        for receipt in receipts:
            current = set(receipt.authority_after)
            self.assertTrue(current.issubset(prior))
            prior = current
        self.assertNotIn("ATTACH_REPORT", receipts[0].authority_after)
        self.assertNotIn("SEND_EMAIL", receipts[1].authority_after)
        self.assertEqual(receipts[1].previous_receipt_hash, receipts[0].digest())

    def test_t8_reassessment_preserves_issuance(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.PRESERVED,
            "ask_before_attach": RelationStatus.PRESERVED,
        })
        receipt = attenuate_authority(base_envelope(), contract(), result)
        issued_digest = receipt.digest()
        revoked = reassess_reliance(receipt, DependencyState.REVOKED)
        self.assertTrue(revoked.valid_at_issuance)
        self.assertEqual(revoked.current_reliance, DependencyState.REVOKED)
        self.assertEqual(receipt.current_reliance, DependencyState.TRUSTED)
        self.assertNotEqual(revoked.digest(), issued_digest)

    def test_missing_relation_is_hold_and_attenuates_bound_action(self):
        result = TransformationResult.from_mapping({
            "ask_before_attach": RelationStatus.PRESERVED,
        })
        receipt = attenuate_authority(base_envelope(), contract(), result)
        self.assertEqual(receipt.verdict, Verdict.HOLD)
        self.assertNotIn("SEND_EMAIL", receipt.authority_after)

    def test_prohibited_action_never_appears(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.PRESERVED,
            "ask_before_attach": RelationStatus.PRESERVED,
        }, proposed_actions=("DELETE_ARCHIVE",))
        receipt = attenuate_authority(base_envelope(), contract(), result)
        self.assertEqual(receipt.verdict, Verdict.DENY)
        self.assertNotIn("DELETE_ARCHIVE", receipt.authority_after)

    def test_falsifier_proves_gate_is_load_bearing(self):
        e = base_envelope()
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.LOST,
            "ask_before_attach": RelationStatus.PRESERVED,
        })
        receipt = attenuate_authority(e, contract(), result)
        ungated = naive_copy_authority(e)
        self.assertIn("SEND_EMAIL", ungated)
        self.assertNotIn("SEND_EMAIL", receipt.authority_after)

    def test_receipt_tamper_evidence_changes_digest(self):
        result = TransformationResult.from_mapping({
            "human_approval_before_send": RelationStatus.PRESERVED,
            "ask_before_attach": RelationStatus.PRESERVED,
        })
        receipt = attenuate_authority(base_envelope(), contract(), result)
        digest = receipt.digest()
        altered = type(receipt)(
            authority_id=receipt.authority_id,
            authority_before=receipt.authority_before,
            authority_after=("DRAFT_EMAIL",),
            transform_id=receipt.transform_id,
            transform_digest=receipt.transform_digest,
            relation_results=receipt.relation_results,
            verdict=receipt.verdict,
            reasons=receipt.reasons,
            previous_receipt_hash=receipt.previous_receipt_hash,
            valid_at_issuance=receipt.valid_at_issuance,
            current_reliance=receipt.current_reliance,
        )
        self.assertNotEqual(digest, altered.digest())

    def test_duplicate_relation_bindings_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate relation bindings"):
            AuthorityEnvelope(
                authority_id="auth-dup",
                source_object_hash="sha256:source",
                permitted_actions=("DRAFT_EMAIL", "SEND_EMAIL"),
                relation_bindings=(
                    RelationBinding("human_approval_before_send", ("SEND_EMAIL",)),
                    RelationBinding("human_approval_before_send", ("DRAFT_EMAIL",)),
                ),
            )

    def test_unfrozen_load_bearing_binding_is_rejected(self):
        e = base_envelope()
        c = contract(relations=("ask_before_attach",))
        result = TransformationResult.from_mapping({
            "ask_before_attach": RelationStatus.PRESERVED,
        })
        with self.assertRaisesRegex(
            ValueError,
            "load-bearing relation bindings missing from frozen_relations",
        ):
            attenuate_authority(e, c, result)


if __name__ == "__main__":
    unittest.main()
