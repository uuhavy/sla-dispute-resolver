# SLADisputeResolver

Standalone GenLayer primitive for bilateral SLA incident adjudication. A claimant
opens a case with frozen SLA clauses and incident records. A distinct respondent
explicitly accepts those clauses and supplies their response records before
GenLayer can resolve the case. No frontend, tokens or payment transfers.

This contribution extends beyond single-submitter assessment: both parties have
separate write authority, the respondent explicitly accepts the policy snapshot,
and every definitive clause ruling must cite submitted evidence records.
