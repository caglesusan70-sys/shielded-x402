import secrets
from client_sdk.memo import pack_x402_memo
from client_sdk.signer import EphemeralSigner
from gateway.challenge import create_challenge
from gateway.validator import ClearanceEngine, ClearanceStatus, AuthParameters, ShieldedNoteRecord

class MockStore:
    def __init__(self):
        self.challenges, self.notes, self.spent = {}, {}, {}
    def get_challenge(self, i): return self.challenges.get(i)
    def mark_invoice_consumed(self, i): self.challenges[i]["consumed"] = True
    def get_settlement_note(self, t): return self.notes.get(t)
    def is_nullifier_spent(self, n): return n in self.spent
    def register_spent_nullifier(self, n, i): self.spent[n] = i

def test_pipeline():
    store = MockStore()
    engine = ClearanceEngine(store)
    signer = EphemeralSigner()
    c = create_challenge("/v1/infer", 50000, 300)
    store.challenges[c.invoice_id] = {"challenge_hex": c.challenge_hex, "amount_zat": c.amount_zat, "valid_until": c.valid_until, "route_path": c.route_path, "consumed": False}
    
    txid, nf = secrets.token_hex(32), secrets.token_hex(32)
    memo = pack_x402_memo(c.invoice_id, signer.public_key_bytes)
    store.notes[txid] = ShieldedNoteRecord(txid, 50000, memo, nf, True)
    
    sig = signer.sign_challenge(c.challenge_hex, txid)
    auth = AuthParameters(c.invoice_id, txid, signer.public_key_hex, sig)
    
    res = engine.evaluate_request(auth, "/v1/infer")
    assert res.is_cleared and res.status == ClearanceStatus.CLEARED
    
    store.challenges[c.invoice_id]["consumed"] = False
    assert engine.evaluate_request(auth, "/v1/infer").status == ClearanceStatus.NULLIFIER_REUSED
    print("[SUCCESS] All 4 Clearance Engine stages verified locally!")

if __name__ == "__main__":
    test_pipeline()
