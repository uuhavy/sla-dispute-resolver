# Corrected validation - 2026-10-03

- Reproduced E105 on the previous source with official genvm-linter 0.11.0.
- Changed only the deployable class name from Contract to SLADisputeResolver.
- Official `genvm-lint check` now exits 0, lint ok, validation ok, 6 methods.
  Full output and exact source SHA-256 are in schema-validation.json.
- Deployment verification also checks that the official linter's source hash
  matches the on-chain source bytes. Linter code was not patched or bypassed.

- Contract is pure ASCII, with the pinned three-line GenLayer header.
- Public schema loads all six methods.
- `gltest tests/ -q -p no:cacheprovider --tb=short`: 43 passed in 3.13s.
- Deployment is FINALIZED / SUCCESS; source matches public RPC byte-for-byte.
- Real two-wallet open/response/resolve: all FINALIZED / SUCCESS. Actual result
  BREACH_FOUND with citations [0, 1]. The incident input is explicitly fictional.
- Explorer independently displays the correct contract and successful calls.
- Counter uses bigint; storage uses string-keyed TreeMap and a storage dataclass.
- All nondeterministic calls are inside the inner assessment function, with
  frozen local inputs and no storage access.
- Validator independently reassesses each clause and supporting evidence set.
- Tests reject same aggregate/different clauses, same ruling/different citations,
  invalid citation IDs, duplicate/empty citations for definitive decisions,
  malformed LLM output, unauthorized writes and invalid lifecycle transitions.
- Provider/parse exceptions fail closed and preserve the READY state for retry.
- Test-network private keys use ignored `.env.*` files and are never published.

The semantic prompt is not proof of model accuracy or immunity to injection.
The direct suite mocks model outputs. Public execution is separately recorded
in live-example.json. Two wallets demonstrate distinct write authority, not
independent real-world identities. A silent respondent can block resolution;
no deadline or default judgment is claimed. This scope avoids a fabricated
time oracle and keeps the protocol explicit.
