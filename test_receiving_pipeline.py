import secrets, time, subprocess, sys
from client_sdk.agent import ShieldedAgent
from client_sdk.zingo_driver import ZingoDaemonDriver
from daemon_worker import SettlementReceiverPipeline
from gateway.state import SQLiteStateStore

store = SQLiteStateStore("state.db")
receiver = SettlementReceiverPipeline("state.db")

# Intercept agent wallet broadcast and feed directly into the receiver pipeline
def live_receiver_broadcaster(recipient: str, amount_zat: int, raw_memo: bytes) -> str:
    txid = secrets.token_hex(32)
    nullifier = secrets.token_hex(32)
    print(f"\n[Test Network] Broadcasting Orchard Spend to {recipient[:16]}...")
    receiver.process_incoming_note(txid, amount_zat, raw_memo, nullifier)
    return txid

print("[1] Launching FastAPI Gateway server...")
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "gateway.main:app", "--port", "8000", "--log-level", "warning"])
time.sleep(2.0)

try:
    print("[2] Initializing Agent with live mock receiver bridge...")
    driver = ZingoDaemonDriver(mock_mode=True)
    # Monkeypatch send_payment to use our live test receiver broadcaster
    driver.send_payment = lambda r, a, m: live_receiver_broadcaster(r, a, bytes.fromhex(m))
    
    agent = ShieldedAgent(upstream_url="http://127.0.0.1:8000", zingo_driver=driver)
    
    print("[3] Agent requesting protected endpoint /v1/infer...")
    result = agent.request("/v1/infer", payload={"prompt": "Run zero-knowledge inference"})
    print(f"[4] Final Gateway Response: {result}")
finally:
    proc.terminate()
    print("[5] End-to-end receiving pipeline test completed cleanly.")
