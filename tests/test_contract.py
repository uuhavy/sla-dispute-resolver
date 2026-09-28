import json
import pytest

CLAUSES = json.dumps(["Acknowledge incidents within 30 minutes.", "Publish an incident report."])
RECORDS = json.dumps(["Incident opened 10:00 UTC; acknowledged 10:45 UTC."])

def address(raw):
    from genlayer import Address
    return raw.as_hex if hasattr(raw, "as_hex") else Address(raw).as_hex

def answer(decisions=("BREACHED", "UNKNOWN"), refs=None, reason="Recorded incident evidence."):
    refs = [[0, 1], []] if refs is None else refs
    return json.dumps({"clauses": [{"index": i, "decision": d,
        "evidence_ids": refs[i], "reason": reason} for i, d in enumerate(decisions)]})

def mock(vm, raw=None):
    vm.clear_mocks()
    vm.mock_llm(r".*", answer() if raw is None else raw)

@pytest.fixture
def contract(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    return direct_deploy("contracts/sla_dispute_resolver.py", sdk_version="v0.2.16")

@pytest.fixture
def ready(contract, direct_vm, direct_bob):
    assert contract.open_case(CLAUSES, RECORDS, address(direct_bob)) == "0"
    direct_vm.sender = direct_bob
    contract.accept_and_respond("0", json.dumps(["We confirm acknowledgement at 10:45 UTC."]))
    return contract

@pytest.mark.parametrize("decisions,outcome", [
    (("BREACHED", "COMPLIED"), "BREACH_FOUND"),
    (("BREACHED", "UNKNOWN"), "BREACH_FOUND"),
    (("COMPLIED", "COMPLIED"), "NO_BREACH"),
    (("COMPLIED", "UNKNOWN"), "INCONCLUSIVE"),
    (("UNKNOWN", "UNKNOWN"), "INCONCLUSIVE")])
def test_aggregate_and_storage(ready, direct_vm, decisions, outcome):
    mock(direct_vm, answer(decisions, [[0], [1]]))
    result = json.loads(ready.resolve("0"))
    assert result["outcome"] == outcome
    row = json.loads(ready.get_case("0"))
    assert row["state"] == "FINALIZED" and row["ruling"] == result
    assert row["clauses"] == json.loads(CLAUSES)
    assert direct_vm.run_validator() is True
    assert ready.get_count() == 1

@pytest.mark.parametrize("decisions,refs,agree", [
    (("BREACHED", "UNKNOWN"), [[1,0], []], True),
    (("BREACHED", "UNKNOWN"), [[0], []], False),
    (("UNKNOWN", "BREACHED"), [[], [0,1]], False),
    (("COMPLIED", "UNKNOWN"), [[0,1], []], False)])
def test_meaning_and_citations(ready, direct_vm, decisions, refs, agree):
    mock(direct_vm)
    ready.resolve("0")
    mock(direct_vm, answer(decisions, refs, "Independent wording."))
    assert direct_vm.run_validator() is agree

@pytest.mark.parametrize("raw", ["{}", "null", "broken", "[]",
    answer(refs=[[], []]), answer(refs=[[2], []]), answer(refs=[[True], []]),
    answer(refs=[[0,0], []]), answer(refs=[[-1], []]),
    answer(decisions=("INVALID", "UNKNOWN")), answer(reason=""),
    answer(reason="x"*401), '{"clauses":[]}',
    '{"clauses":[{"index":true},{"index":1}]}'])
def test_invalid_model_does_not_finalize(ready, direct_vm, raw):
    mock(direct_vm, raw)
    with direct_vm.expect_revert("assessment unavailable or invalid"):
        ready.resolve("0")
    assert json.loads(ready.get_case("0"))["state"] == "READY"
    mock(direct_vm)
    ready.resolve("0")

def test_validator_errors(ready, direct_vm):
    mock(direct_vm)
    ready.resolve("0")
    assert direct_vm.run_validator(leader_result="{}") is False
    assert direct_vm.run_validator(leader_error=ValueError("provider failed")) is False
    mock(direct_vm, "broken")
    assert direct_vm.run_validator() is False

@pytest.mark.parametrize("raw", ["", "{}", "[]", "[1]", '[" "]', '["A","a"]',
    json.dumps([str(i) for i in range(9)]), json.dumps(["x"*701]), "x"*20001])
def test_bad_clauses(contract, direct_vm, direct_bob, raw):
    with direct_vm.expect_revert():
        contract.open_case(raw, RECORDS, address(direct_bob))
    assert contract.get_count() == 0

@pytest.mark.parametrize("raw", ["[]", "{}", '[" "]', json.dumps(["x"*1501])])
def test_bad_evidence(contract, direct_vm, direct_bob, raw):
    with direct_vm.expect_revert():
        contract.open_case(CLAUSES, raw, address(direct_bob))
    contract.open_case(CLAUSES, RECORDS, address(direct_bob))
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert():
        contract.accept_and_respond("0", raw)
    assert json.loads(contract.get_case("0"))["state"] == "AWAITING_RESPONSE"

@pytest.mark.parametrize("who", ["invalid", "0x"+"0"*40, "self"])
def test_bad_party(contract, direct_vm, direct_alice, who):
    with direct_vm.expect_revert():
        contract.open_case(CLAUSES, RECORDS, address(direct_alice) if who == "self" else who)

def test_authority_and_cancel(contract, direct_vm, direct_alice, direct_bob):
    contract.open_case(CLAUSES, RECORDS, address(direct_bob))
    with direct_vm.expect_revert("only respondent"):
        contract.accept_and_respond("0", RECORDS)
    with direct_vm.expect_revert("not ready"):
        contract.resolve("0")
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only claimant"):
        contract.cancel_case("0")
    direct_vm.sender = direct_alice
    contract.cancel_case("0")
    assert json.loads(contract.get_case("0"))["state"] == "CANCELLED"
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("not awaiting"):
        contract.accept_and_respond("0", RECORDS)

def test_frozen_ready_and_finalized(ready, direct_vm, direct_alice):
    with direct_vm.expect_revert("not awaiting"):
        ready.accept_and_respond("0", RECORDS)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("not awaiting"):
        ready.cancel_case("0")
    mock(direct_vm)
    ready.resolve("0")
    before = ready.get_case("0")
    with direct_vm.expect_revert("not ready"):
        ready.resolve("0")
    assert ready.get_case("0") == before

def test_missing_case(contract, direct_vm):
    for method, args in [(contract.get_case,["9"]), (contract.resolve,["9"]),
        (contract.cancel_case,["9"]), (contract.accept_and_respond,["9",RECORDS])]:
        with direct_vm.expect_revert("case not found"):
            method(*args)
