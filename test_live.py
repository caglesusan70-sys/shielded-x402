import secrets, time, subprocess, sys, sqlite3
from gateway.state import SQLiteStateStore
from client_sdk.agent import ShieldedAgent

store = SQLiteStateStore("state.db")

def mock_daemon_broadcaster(recipient, amount_zat, raw_memo):
    txid, nf = secrets.token_hex(32), secrets.token_hex(32)
    with sqlite3.connect(store.p) as c:
        c.execute("INSERT OR REPLACE INTO settlement_notes VALUES (?,?,?,?,1)", (txid, amount_zat, raw_memo, nf))
    return txid
print("[1] Launching Gateway server...")
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "gateway.main:app", "--port", "8000", "--log-level", "warning"])
time.sleep(2.0)

try:
    print("[2] Agent querying /v1/infer...")
    agent = ShieldedAgent(settlement_broadcaster=mock_daemon_broadcaster)
    resp = agent.get("http://127.0.0.1:8000/v1/infer")
    print(f"[3] Response Code: {resp.status_code}")
    print(f"[4] Response Data: {resp.json()}")
finally:
    proc.terminate()
    print("[5] Gateway stopped.")
