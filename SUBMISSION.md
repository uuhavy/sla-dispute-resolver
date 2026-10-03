# Portal submission

Track: Builder

Type: Intelligent Contracts

Original contribution date: 28/09/2026

Corrected revision completed: 03/10/2026

Use Resubmit on the rejected contribution. Preserve the original contribution
date if the form keeps it; 03/10/2026 is the actual correction/deployment date.

Title:

```text
SLADisputeResolver - Bilateral Incident Adjudication with Evidence Citations
```

Description:

```text
Corrected resubmission: E105 fixed by declaring class SLADisputeResolver(gl.Contract). The official genvm-linter 0.11.0 check now passes: 6 methods, exit 0. Public API and logic are unchanged. This standalone primitive adjudicates SLA incidents against frozen clauses and records from two distinct wallets. GenLayer validators independently agree on the MEANING of each clause decision and its supporting evidence IDs, not JSON format. Reusable for hosting incidents, API support SLAs and managed-service disputes. No frontend or automatic payouts. Includes 43 passing tests, docs, schema-validation.json and matching public deployment evidence. New studionet contract: 0x9E223985B5773714696e7F9C8Bf486b0B15a3dD6. The deployed source hash matches the file validated by the official linter. This replaces the previously submitted deployment.
```

Add TWO separate evidence entries:

1. GitHub Repository: https://github.com/uuhavy/sla-dispute-resolver
2. GenLayer Explorer Contract: https://explorer-studio.genlayer.com/address/0x9E223985B5773714696e7F9C8Bf486b0B15a3dD6

Remove the old Explorer evidence URL ending in 0x2a3706e2D8dB38202180eb7ED22886E47423372d.

Optional supporting URL (official linter result tied to source hash):
https://github.com/uuhavy/sla-dispute-resolver/blob/master/schema-validation.json

Paste the title into Title, and only the description paragraph into Notes /
Description. Review the submission and complete reCAPTCHA yourself at
https://portal.genlayer.foundation before submitting under Builder ->
Intelligent Contracts. No portal submission is performed by the scripts.
