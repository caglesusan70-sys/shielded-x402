import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from client_sdk.memo import pack_x402_memo, unpack_x402_memo, MEMO_TOTAL_SIZE
from client_sdk.signer import EphemeralSigner
from client_sdk.agent import ShieldedAgent

print("[*] Auditing Client Agent SDK (client_sdk/)...")

# 1. Memo Wire Encoding Test
pk_test = b"\x07" * 32
packed = pack_x402_memo("inv_test123", pk_test)
assert len(packed) == MEMO_TOTAL_SIZE
unpacked = unpack_x402_memo(packed)
assert unpacked.invoice_id == "inv_test123" and unpacked.pk_agent == pk_test
assert unpack_x402_memo(b"Z402" + b"\x00" * 508) is None
print("  [1/3 PASS] client_sdk/memo.py: ZIP-302 512-byte wire encoding verified.")

# 2. Ephemeral Signer Test
signer = EphemeralSigner()
assert len(signer.public_key_bytes) == 32 and len(signer.public_key_hex) == 64
sig_hex = signer.sign_challenge("feed"*16, "beef"*16)
assert len(sig_hex) == 128
pubkey = Ed25519PublicKey.from_public_bytes(signer.public_key_bytes)
pubkey.verify(bytes.fromhex(sig_hex), f"{'feed'*16}:{'beef'*16}".encode("ascii"))
print("  [2/3 PASS] client_sdk/signer.py: RFC 9421 Ed25519 signing verified.")
# 3. Agent Autonomous 402 Handshake Loop
inv, rec, ch = "inv_mock01", "u1mockaddress", "a" * 64

def mock_transport_handler(request: httpx.Request):
    if "Authorization" not in request.headers:
        h = f'x402 invoice_id="{inv}", recipient="{rec}", amount_zat="50000", challenge="{ch}"'
        return httpx.Response(402, headers={"WWW-Authenticate": h})
    
    auth = request.headers["Authorization"]
    assert f'invoice_id="{inv}"' in auth and "signature=" in auth
    return httpx.Response(200, json={"status": "cleared", "data": "autonomous_verified"})

agent = ShieldedAgent(settlement_broadcaster=lambda r, a, m: "dead"*16)
agent.client = httpx.Client(transport=httpx.MockTransport(mock_transport_handler))
resp = agent.get("http://agent.local/v1/infer")
assert resp.status_code == 200 and resp.json()["status"] == "cleared"
print("  [3/3 PASS] client_sdk/agent.py: Autonomous 402 negotiation loop operational.")

print("\n[✔] ALL 3 CLIENT SDK MODULES VERIFIED & OPERATIONAL.")
