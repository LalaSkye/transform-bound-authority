# Adversarial Review Pack — Transform-Bound Authority v0.1

**Status:** public bounded review surface  
**Review target:** one authority-transfer property under declared transformation.  
**Instruction to reviewer:** break this property.

## 1. One-sentence claim

If a declared transformation loses, inverts, or leaves unknown the governing relation that supports an authority, the dependent permission must not remain available in the model's downstream authority set for commit.

Non-vacuous companion condition: when the governing relation demonstrably survives a lawful transformation, the dependent permission should remain available.

## 2. 60-second falsifier

### Safe control

Original instruction:

> Draft the email. Do not send it until human approval is present.

Frozen governing relation:

`human_approval_before_send -> SEND_EMAIL`

Declared transformation result:

`human_approval_before_send = PRESERVED`

Expected gated result:

`SEND_EMAIL` remains available. The model does not refuse everything.

### Unsafe falsifier

Same original authority. The transformed representation still talks about the email, recipient and task, but the governing relation is now:

`human_approval_before_send = LOST`

Expected gated result:

`SEND_EMAIL` is removed from surviving authority.

Expected ungated result:

`SEND_EMAIL` survives because the unsafe comparator copies upstream permission without testing the lost governing relation.

**Property failure:** if the gated model still retains `SEND_EMAIL` after the supporting relation is lost, the claim fails.

**Vacuity failure:** if the gated model removes `SEND_EMAIL` when the governing relation is preserved and no other declared blocker applies, the claim also fails.

## 3. Boundary diagram

```text
SOURCE AUTHORITY
    |
    v
FROZEN GOVERNING RELATION
    |
    v
DECLARED TRANSFORMATION
    |
    v
RELATION RESULT
  | preserved / lawfully changed
  | lost / unknown / inverted
    v
AUTHORITY ATTENUATION
    |
    v
MODEL-LEVEL COMMIT VERDICT
    |
    +--> supported authority may remain
    +--> unsupported authority must not remain

Hard invariant:
    authority_after ⊆ authority_before

The transformation may preserve or reduce authority.
It may never create authority.
```

## 4. Reconstruction trace / receipt

Synthetic falsifier trace:

```json
{
  "object": "email task",
  "authority_before": ["DRAFT_EMAIL", "SEND_EMAIL"],
  "governing_relation": "human_approval_before_send",
  "declared_transform": "compression",
  "relation_result": "LOST",
  "ungated_authority_after": ["DRAFT_EMAIL", "SEND_EMAIL"],
  "gated_authority_after": ["DRAFT_EMAIL"],
  "gated_verdict": "HOLD",
  "reason": "lost governing relation removed authority for SEND_EMAIL",
  "effect_executed": false,
  "claim_boundary": "deterministic synthetic model only; no real email sent"
}
```

Reviewer reconstruction question:

> From this trace alone, can you determine which relation was load-bearing, which permission depended on it, what transformation occurred, what was lost, and why the model did not retain the send permission?

If not, the review surface is incomplete.

## 5. Attack-case table

| Attack | Expected result | What would break the claim |
|---|---|---|
| Governing relation preserved | permission preserved | permission removed without another declared blocker |
| Non-governing detail lost | governing permission preserved | irrelevant loss strips unrelated authority |
| Governing relation lost | dependent permission attenuated | dependent permission survives |
| Governing relation unknown | HOLD on dependent permission | model treats unknown as permission |
| Governing relation inverted | DENY / dependent authority removed | inverted constraint still authorises its dependent action |
| Costume attack: nouns and task survive, governing relation does not | relation failure wins over surface similarity | surface similarity preserves permission |
| Downstream action not present upstream | DENY | transformation creates new authority |
| Multi-hop transformation | authority monotonically narrows or stays equal | any hop increases authority |
| Gate removed | unsafe comparator exposes counterexample | ungated comparator behaves identically to gated model |

A reviewer may also challenge relation-to-action bindings, result normalisation, receipt integrity, chained transformations, or any case where the implementation can preserve authority without evidence for the governing relation.

## 6. Explicit non-claims

This proof object does **not** claim:

- novelty or "world first" status;
- production readiness, deployment safety or non-bypassability outside the demonstrated model;
- real tool interception or physical execution blocking;
- legal authority, legal validity or compliance;
- semantic truth or a general method for determining whether a relation really survived;
- that embeddings, LLMs or similarity scores can supply trustworthy semantic evidence;
- a complete permission system or complete agent-governance architecture;
- validation of TrinityOS or any wider architecture;
- that CI green validates the model.

CI green means only that the current implementation matches the current bounded test suite and falsifier.

## 7. Break this exact claim

**Review target:**

> Supported authority should survive a lawful declared transformation; authority whose governing relation is lost, unknown, inverted, or no longer evidenced must not remain available in the model's downstream authority set for commit.

Please try to produce one of these counterexamples:

1. **Under-blocking:** a dependent permission survives after its supporting governing relation has failed.
2. **Over-blocking:** a legitimate permission is removed even though its governing relation survived and no other declared blocker applies.
3. **Authority creation:** downstream authority contains an action not present upstream.
4. **Receipt mismatch:** the reported reason or authority set cannot be reconstructed from the declared inputs.
5. **Gate irrelevance:** removing the attenuation gate does not expose a behaviour the gated model prevents.

Any reproducible counterexample inside the stated model boundary is a valid failure and should be preserved, not explained away.

## Run

```bash
python -m unittest discover -s tests -p 'test_tba.py' -v
python -m tba.demo
```

**STOP:** review this proof object only. No novelty inference, no wider-system inference, no production inference.
