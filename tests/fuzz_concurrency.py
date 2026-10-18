import secrets, concurrent.futures
from client_sdk.memo import pack_x402_memo
from client_sdk.signer import EphemeralSigner
from gateway.challenge import create_challenge
from gateway.state import SQLiteStateStore
from gateway.validator import ClearanceEngine, AuthParameters

def test_concurrent_double_spend():
    store = SQLiteStateStore(":memory:")
    engine = ClearanceEngine(store)
    signer = EphemeralSigner()
    c = create_challenge("/v1/infer", 50000, 300)
    store.save_challenge(c)
    txid, nf = secrets.token_hex(32), secrets.token_hex(32)
    memo = pack_x402_memo(c.invoice_id, signer.public_key_bytes)
    with store._c() as conn:
        conn.execute("INSERT OR REPLACE INTO settlement_notes VALUES (?,?,?,?,1)", (txid, 50000, memo, nf))

    sig = signer.sign_challenge(c.challenge_hex, txid)
    auth = AuthParameters(c.invoice_id, txid, signer.public_key_hex, sig)

    def attempt(_):
        return engine.evaluate_request(auth, "/v1/infer").http_status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(attempt, range(20)))

    assert results.count(200) == 1, f"Expected 1 success, got {results.count(200)}"
    assert results.count(403) == 19, f"Expected 19 rejections, got {results.count(403)}"

if __name__ == "__main__":
    test_concurrent_double_spend()
    print("[PASS] Concurrency fuzz: 1 cleared (200), 19 rejected (403).")
