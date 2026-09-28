# SLADisputeResolver

Standalone GenLayer primitive for bilateral SLA incident adjudication. A claimant
opens a case with frozen SLA clauses and incident records. A distinct respondent
explicitly accepts those clauses and supplies their response records before
GenLayer can resolve the case. No frontend, tokens or payment transfers.

This contribution extends beyond single-submitter assessment: both parties have
separate write authority, the respondent explicitly accepts the policy snapshot,
and every definitive clause ruling must cite submitted evidence records.

## Consensus on meaning and evidence

Inside `gl.vm.run_nondet_unsafe`, the leader assesses each agreed clause against
both parties' records. The custom validator independently repeats the assessment
on the same frozen input and compares each clause's decision AND sorted evidence
IDs. It agrees on the **meaning of the ruling and its evidentiary basis, not JSON
format**. Different reason wording and citation ordering are allowed; different
decisions or citation sets are rejected, even when the overall outcome matches.

The model classifies each clause as BREACHED, COMPLIED, or UNKNOWN. Prompt rules
require UNKNOWN for missing, ambiguous or materially conflicting evidence, and
recognize explicit policy exceptions. Deterministic code validates citation IDs,
requires evidence for definitive decisions, and computes the overall outcome:

- Any BREACHED clause: `BREACH_FOUND`.
- Otherwise any UNKNOWN clause: `INCONCLUSIVE`.
- Otherwise: `NO_BREACH`.

An LLM cannot supply an overriding aggregate outcome. Syntactically valid
citations are not proof of relevance; independent semantic reassessment is the
additional check. Reasons are leader explanations, not consensus on exact prose.

## State and public API

`AWAITING_RESPONSE -> READY -> FINALIZED`, or
`AWAITING_RESPONSE -> CANCELLED`.

| Method | Access and result |
| --- | --- |
| `open_case(clauses_json, incident_records_json, respondent) -> str` | Anyone; fixes clauses and claimant evidence, returns case ID starting at `"0"` |
| `accept_and_respond(case_id, response_records_json)` | Assigned respondent only; explicitly accepts the frozen clauses and locks response |
| `cancel_case(case_id)` | Claimant only, before response |
| `resolve(case_id) -> str` | Anyone, only READY; returns ruling JSON after consensus |
| `get_case(case_id) -> str` | Public complete JSON record |
| `get_count() -> int` | Total created including cancelled cases |

Evidence IDs are stable: claimant records first (0-based), then respondent
records. Clauses also use ordered zero-based indices. Read both arrays from
`get_case` to reconstruct citations.

Both parties must use distinct nonzero wallet addresses. The contract does not
prove that those wallets belong to different people. There are no amendments,
overwrites, appeals or default judgments. A nonresponsive respondent can prevent
resolution; the claimant may cancel before response. A failed model assessment
leaves READY state intact for retry. Once both sides have submitted, cancellation
is forbidden. There is no privileged owner who can choose the outcome.

Storage is `TreeMap[str, Dispute]`, a storage dataclass and a `bigint` counter.
Evidence arrays and rulings are serialized into storage strings. Input limits:
1..8 unique clauses of up to 700 characters, 1..8 unique records per party of up
to 1,500 characters each, each input JSON string at most 20,000 characters.
Empty/oversized input, duplicate entries, invalid parties, unauthorized calls,
missing IDs and invalid transitions raise `UserError`. Invalid LLM outputs or
failed independent reassessment never silently finalize a ruling.

## Deployment

- Network: **studionet**, chain ID **61999**.
- Address: **`0x2a3706e2D8dB38202180eb7ED22886E47423372d`**.
- [Explorer contract](https://explorer-studio.genlayer.com/address/0x2a3706e2D8dB38202180eb7ED22886E47423372d).
- [Deployment transaction](https://explorer-studio.genlayer.com/tx/0x414a2ebb5e6e7d2daaff79e9dd547c33f10736ce88a76fde34f5a39ab7712b3c).
- Deployment **FINALIZED / SUCCESS** on 2026-09-28.
- Exact deployed source SHA-256: `99213fd07ed5806236592eb454bff6f57cea3b4574f5203f2cdadb6682313959`.
- [Public verification record](deployment-verification.json).

Run `python scripts/verify_public.py` to check public receipt, source byte equality,
schema and read behavior without a saved key or logged-in browser. Public RPC:
`https://studio.genlayer.com/api`. Studionet is a test environment; this records
successful verification at a specific time, not a guarantee of permanent retention.

### Worked example: real execution of a fictional incident

On 2026-09-28, two distinct test wallets submitted case `"0"`. The incident is
illustrative, but the transactions, LLM execution, consensus and read result are
real public studionet results, with no mocks and `leader_only=False`.

1. Claimant calls `open_case` with clause
   `The service provider must acknowledge every incident within 30 minutes of the incident being opened.`,
   record `Incident INC-17 was opened on 2026-09-28 at 10:00 UTC. This is the agreed incident opening timestamp.`,
   and respondent `0xB3213A02cb79b34f60125fe43908aF63b75f43A0`.
   Pass clause and record as separate JSON arrays of strings.
2. That respondent calls `accept_and_respond("0", response_records_json)` with
   `Provider incident log INC-17: first acknowledgement was on 2026-09-28 at 10:45 UTC. We confirm this is the correct first acknowledgement timestamp, and we accept the claimant's opening timestamp.`
   in a JSON array.
3. Claimant calls `resolve("0")`. Anyone could trigger this step after READY.
4. Public `get_case("0")` returns FINALIZED with the actual ruling below
   (explanatory reason omitted here; full output in the linked evidence file).

```json
{
  "clauses": [{"index": 0, "decision": "BREACHED", "evidence_ids": [0, 1]}],
  "outcome": "BREACH_FOUND"
}
```

The reason identifies 45 minutes elapsed against the 30-minute limit, citing the
claimant's opening timestamp and the respondent's acknowledgement timestamp.
All three calls are FINALIZED / SUCCESS.

- [Full inputs, transaction hashes and actual read result](live-example.json).
- [Actual resolve transaction](https://explorer-studio.genlayer.com/tx/0x9dae5fcb6b4a6699f9fb23c49a783d2e3c72c27c5b325ffe7babab58bfe9fadd).
- `python scripts/live_example.py` verifies existing receipts and reads the
  finalized case without sending a transaction. `--send` is only for advancing
  an unfinished recorded example; it does not overwrite an existing case.

## Tests

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/prepare_windows_tests.py
gltest tests/ -q -p no:cacheprovider --tb=short
```

**43 passed in 2.68s** on 2026-09-28 (Python 3.12, genlayer-test 0.29.2).
SDK v0.2.16 is pinned in direct deployment fixtures and downloaded from the
official release on first use. The Windows helper only fixes the runner's
temporary-file cleanup; it does not change contract or validator semantics.
No simulator service is required for these direct tests.

Tests cover aggregation, evidence citation order/set agreement, semantic
disagreement, invalid LLM response and retry, role separation, frozen inputs,
duplicate processing, cancellation, missing IDs and bounds. They use mocked LLM
responses and separately invoke the captured validator; they are not an LLM
accuracy benchmark. Public execution evidence is recorded separately.

## Reuse and limits

Suitable for hosting incident review, API-provider support SLA disputes, and
managed-service response-time disputes. Downstream services can consume a frozen,
cited decision through the read API. No frontend, token, payout or escrow.

This judges consistency of submitted records with agreed SLA text; it does not
authenticate telemetry, establish real-world identity, or enforce legal rights.
Both parties can collude or provide false records. Model reasoning and prompt
injection defenses are imperfect. Strict citation agreement can fail to converge
when multiple evidence sets are equally relevant. Unknown is a first-class
outcome; consumers must not treat it as compliance. All submitted records are
public, so use sanitized incident data. No automatic financial action occurs.

## References

- [GenLayer equivalence principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle)
- [GenLayer non-determinism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism)
- [GenLayer testing](https://docs.genlayer.com/developers/intelligent-contracts/testing)
