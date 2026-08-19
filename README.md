# Transform-Bound Authority v0.1

A bounded, deterministic proof object for one authority-transfer property under declared transformation.

## Review target

> Supported authority should remain available when its governing relation survives a lawful declared transformation; authority whose governing relation is lost, unknown, inverted, or no longer evidenced must not remain available in the model's downstream authority set for commit.

The operational invariant is:

```text
authority_after ⊆ authority_before
```

A transformation may preserve or reduce authority. It may never create authority.

## Why this exists

Agentic workflows routinely transform instructions through compression, translation, summarisation, replanning, memory, retrieval, and hand-off.

A transformed representation can keep the same nouns and task while losing a prohibition, approval requirement, scope constraint, or timing condition.

This prototype asks one narrow question:

> Given declared evidence about which governing relations survived a transformation, does downstream authority contract correctly and fail closed?

It does **not** decide whether the declared semantic evidence is true.

## 60-second falsifier

Original instruction:

> Draft the email. Do not send it until human approval is present.

Frozen governing relation:

```text
human_approval_before_send -> SEND_EMAIL
```

### Safe control

```text
human_approval_before_send = PRESERVED
```

Expected result: `SEND_EMAIL` remains in the downstream authority set.

### Unsafe case

```text
human_approval_before_send = LOST
```

Expected result: `SEND_EMAIL` is removed from the downstream authority set.

The deliberately unsafe comparator in `tba/ungated.py` simply copies upstream authority. In the unsafe case it leaves `SEND_EMAIL` present. The gated kernel removes it.

The control is therefore load-bearing inside the demonstrated model.

## What is implemented

- immutable authority, transformation, and receipt objects;
- relation-bound authority attenuation;
- `PRESERVED`, `LAWFULLY_CHANGED`, `LOST`, `INVERTED`, and `UNKNOWN` relation states;
- fail-closed handling for unknown load-bearing relations;
- denial of attempted authority gain;
- monotonic multi-hop propagation;
- chained receipt hashes;
- later current-reliance reassessment without rewriting issuance history;
- a deliberately unsafe ungated falsifier;
- 15 deterministic adversarial/unit tests;
- CI using Python 3.11.

No third-party runtime dependencies are required.

## Run

```bash
python -m compileall -q tba
python -m unittest discover -s tests -p 'test_tba.py' -v
python -m tba.demo
```

## Pass / fail

The bounded claim passes when the demonstrated model preserves supported authority, removes unsupported authority, never creates downstream authority, and differs materially from the ungated comparator on the falsifier.

It fails if a reproducible case inside the stated model boundary shows any of the following:

- unsupported authority survives;
- supported authority is removed without another declared blocker;
- downstream authority contains an action absent upstream;
- `UNKNOWN` load-bearing state permits the bound action;
- an inverted load-bearing relation still authorises its dependent action;
- a multi-hop chain increases authority;
- removing the gate makes no meaningful difference to the falsifier.

A failing case is a useful review result. Preserve it.

## Critical boundary

The kernel consumes a `TransformationResult` supplied by a test harness or external assessor.

It does **not** establish semantic truth and does not claim that an LLM, embedding, translation system, summariser, or similarity metric can reliably determine whether a governing relation survived.

It also does not demonstrate real tool interception or production enforcement. The proof is about the model's derived authority state and verdicts.

See:

- [`docs/TRANSFORM_BOUND_AUTHORITY_v0.1.md`](docs/TRANSFORM_BOUND_AUTHORITY_v0.1.md)
- [`docs/TRANSFORM_BOUND_AUTHORITY_CLAIM_BOUNDARY.md`](docs/TRANSFORM_BOUND_AUTHORITY_CLAIM_BOUNDARY.md)
- [`docs/TRANSFORM_BOUND_AUTHORITY_ADVERSARIAL_REVIEW_PACK_v0.1.md`](docs/TRANSFORM_BOUND_AUTHORITY_ADVERSARIAL_REVIEW_PACK_v0.1.md)
- [`tests/test_tba.py`](tests/test_tba.py)
- [`tba/engine.py`](tba/engine.py)

## Status

Public v0.1 proof surface. Synthetic fixtures only.

No novelty, production-readiness, legal, compliance, certification, adoption, or wider-system claim is made.

Later private research is not represented by this v0.1 repository.
