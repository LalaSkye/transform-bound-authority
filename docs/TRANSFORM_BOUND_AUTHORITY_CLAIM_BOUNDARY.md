# Transform-Bound Authority — Claim Boundary

## What is demonstrated

This repository contains a small deterministic reference prototype showing that:

- authority can be represented as an explicit upstream action set plus relation bindings;
- a declared transformation result can narrow that authority when governing relations are lost, inverted or unknown;
- the resulting authority set is mechanically constrained to be a subset of the upstream authority set;
- attempted authority gain is denied;
- unknown load-bearing relation state can hold the model-level commit decision;
- inverted load-bearing relation state can deny the model-level commit decision;
- chained receipts can preserve prior receipt hashes;
- historical issuance can remain unchanged while current reliance is later marked revoked or unknown;
- an ungated authority-copy model can be made to fail on a counterexample that the attenuation gate catches.

## Input-contract validity

For the demonstrated model, a valid input contract requires:
- unique relation-binding identifiers; and
- every load-bearing relation binding to appear exactly once in the frozen relation set.

Malformed contracts are rejected before attenuation is evaluated.

## What is not demonstrated

This prototype does **not** demonstrate:

- production readiness;
- enterprise deployment;
- real tool interception or physical enforcement;
- legal, regulatory or compliance correctness;
- complete authorization for any real agent stack;
- path-universal non-bypassability;
- external adoption;
- novelty or "first ever" status;
- semantic understanding;
- that an LLM can reliably score relation survival;
- that embeddings prove preserved meaning;
- that translation, compression or summarisation can be verified generally;
- cryptographic attestation of real-world events;
- secure key management;
- trusted execution;
- a complete threat model;
- TrinityOS or any wider architecture.

## Semantic-assessor boundary

The enforcement kernel accepts an explicit `TransformationResult`.

That object is evidence **input**, not automatically established truth.

A real deployment would need a separately validated relation-survival assessor with its own uncertainty, provenance and adversarial controls. This repository deliberately does not pretend that problem is solved.

## Hash boundary

SHA-256 digests in the receipt format make changes to the local serialized receipt visible when rechecked.

They do not prove:

- external truth;
- completeness;
- physical enforcement;
- who authored a real-world statement;
- that an omitted event never happened.

## Novelty boundary

No novelty claim is made here.

Any future novelty statement should compare the exact conjunction against current primary literature, standards and public implementations.

## Safety rule

Do not connect this v0.1 prototype to live credentials, live agents, live communication surfaces or consequential tools.

Synthetic fixtures only until a separate deployment review explicitly changes that status.
