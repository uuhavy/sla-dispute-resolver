"""Resume one public example step; without --send this script is read-only."""
import argparse
from datetime import datetime, timezone
import json
from eth_account import Account
from genlayer_py import create_client
from genlayer_py.chains import studionet
from deploy_public import ROOT, RPC, MANIFEST

parser = argparse.ArgumentParser()
parser.add_argument("--send", action="store_true")
opts = parser.parse_args()
manifest = json.loads(MANIFEST.read_text())
address = manifest["contract_address"]
path = ROOT / "live-example.json"
clauses = ["The service provider must acknowledge every incident within 30 minutes of the incident being opened."]
claim = ["Incident INC-17 was opened on 2026-09-28 at 10:00 UTC. This is the agreed incident opening timestamp."]
reply = ["Provider incident log INC-17: first acknowledgement was on 2026-09-28 at 10:45 UTC. We confirm this is the correct first acknowledgement timestamp, and we accept the claimant's opening timestamp."]
reader = create_client(chain=studionet, account=Account.create(), endpoint=RPC)
if path.exists():
    data = json.loads(path.read_text())
else:
    if not opts.send:
        raise SystemExit("No live example yet. Use --send to start.")
    respondent_key = ROOT / ".env.studionet-respondent"
    if not respondent_key.exists():
        respondent_key.write_text(Account.create().key.hex(), encoding="ascii")
    respondent = Account.from_key(respondent_key.read_text().strip())
    data = {"contract_address": address, "network": "studionet", "case_id": "0",
        "claimant": manifest["deployer"], "respondent": respondent.address,
        "clauses": clauses, "claimant_records": claim, "respondent_records": reply,
        "expected_outcome_before_execution": "BREACH_FOUND", "transactions": []}
assert data["contract_address"] == address

def save():
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

for tx in data["transactions"]:
    receipt = reader.get_transaction(tx["hash"])
    tx["status"] = receipt["status_name"]
    save()
    print(tx["method"], tx["status"], flush=True)
    if tx["status"] != "FINALIZED":
        raise SystemExit(2)
    tx["execution_result"] = receipt["consensus_data"]["leader_receipt"][0]["execution_result"]
    save()
    assert tx["execution_result"] == "SUCCESS"
steps = [("open_case", [json.dumps(clauses), json.dumps(claim), data["respondent"]], "deployer"),
         ("accept_and_respond", ["0", json.dumps(reply)], "respondent"),
         ("resolve", ["0"], "deployer")]
index = len(data["transactions"])
if index == 3:
    result = json.loads(reader.read_contract(address=address, function_name="get_case", args=["0"]))
    assert result["state"] == "FINALIZED" and result["clauses"] == clauses
    assert result["claimant_records"] == claim and result["respondent_records"] == reply
    assert result["claimant"] == data["claimant"] and result["respondent"] == data["respondent"]
    data["actual_record"] = result
    data["verified_at_utc"] = datetime.now(timezone.utc).isoformat()
    data["result_kind"] = "REAL studionet execution; no mocks; leader_only=False"
    save()
    print(json.dumps(result, indent=2))
elif opts.send:
    if index == 0:
        assert reader.read_contract(address=address, function_name="get_count", args=[]) == 0
    method, args, role = steps[index]
    account = Account.from_key((ROOT / (".env.studionet-" + role)).read_text().strip())
    assert account.address == (data["respondent"] if role == "respondent" else data["claimant"])
    client = create_client(chain=studionet, account=account, endpoint=RPC)
    tx = client.write_contract(address=address, function_name=method, args=args, leader_only=False)
    data["transactions"].append({"method": method, "hash": str(tx), "status": "submitted"})
    save()
    print("Submitted", method, tx, flush=True)
else:
    print("Next step:", steps[index][0], "(use --send)")
