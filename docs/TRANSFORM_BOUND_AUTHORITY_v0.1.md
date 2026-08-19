# Transform-Bound Authority v0.1

**Status:** public bounded deterministic prototype / synthetic fixtures only

## Core rule

> A transformation may preserve or reduce authority. It may never create authority.

Formally:

```text
authority_after ⊆ authority_before
```

The prototype treats compression, translation, summarisation, replanning and other carrier changes as explicit transformations. An upstream authority envelope binds actions to frozen governing relations. A downstream transformation result states which frozen relations were:

- `PRESERVED`
- `LAWFULLY_CHANGED`
- `LOST`
- `INVERTED`
- `UNKNOWN`

The deterministic kernel then derives the downstream authority set.

## Why this seam exists

Identity, provenance and chain continuity are not enough when an instruction changes representation. A summary can keep the right nouns while dropping a prohibition, approval requirement, scope condition or timing constraint.

This prototype separates two questions:

1. **Did the representation still look related?**
2. **Did the governing relation needed for authority survive?**

Only the second can preserve the authority bound to that relation.

## Deterministic decision rules

1. Start with the upstream `permitted_actions`.
2. Remove every explicitly prohibited action.
3. For each frozen relation:
   - `PRESERVED` or `LAWFULLY_CHANGED`: keep authority bound to it.
   - `LOST`: remove authority bound to it.
   - `UNKNOWN`: remove bound authority and return `HOLD` when load-bearing.
   - `INVERTED`: remove bound authority and return `DENY` when load-bearing.
4. If the downstream proposal asks for an action absent from the upstream authority set, return `DENY`.
5. If it asks for an action that existed upstream but no longer survives relation checks, return `HOLD` unless a stronger denial condition exists.
6. Every receipt enforces `authority_after ⊆ authority_before`.
7. Receipt digests and previous-receipt hashes make local tampering and chain rewrites visible within the demonstrated format.

## Critical separation

The kernel **does not decide semantic truth**.

It consumes a `TransformationResult` supplied by an external assessor, test harness or future verifier. The current prototype therefore demonstrates only the attenuation logic:

> given declared relation-survival evidence, downstream authority is derived monotonically and fail-closed.

It does **not** prove that an LLM, embedding model or similarity metric can correctly determine whether a relation survived.

It also does not prove that a real tool call is physically prevented. Its effect is the model-level `authority_after` set and verdict.

## Falsifier

`tba.ungated.naive_copy_authority()` deliberately copies upstream authority without checking relation survival.

The adversarial suite demonstrates a counterexample: when `human_approval_before_send` is lost, the ungated model still carries `SEND_EMAIL`; the gated model removes it.

That is the load-bearing test.

## Test vectors

- T0 identity transform
- T1 lawful change
- T2 non-governing detail loss
- T3 governing constraint loss
- T4 governing constraint inversion
- T5 surface-costume attack
- T6 attempted authority gain
- T7 chained transformations with monotonic authority
- T8 later dependency revocation while preserving issuance history
- missing-relation fail-closed test
- prohibited-action test
- receipt-digest tamper test
- ungated falsifier

## Run

```bash
python -m unittest discover -s tests -p 'test_tba.py' -v
python -m tba.demo
```

No third-party runtime dependencies are required.

## Scope

This v0.1 object is deliberately narrow. It does not claim to subsume:

- permission continuity;
- interpretation admissibility;
- semantic ambiguity gating;
- invariant locking;
- tamper-evident receipt systems;
- trust dependency revocation;
- capability systems;
- production execution gates.

The seam being tested is:

> **Can model-level downstream authority be attenuated according to which frozen governing relations survive a declared transformation?**
