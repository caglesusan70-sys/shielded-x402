import subprocess, time, sys, secrets, sqlite3
from client_sdk.agent import ShieldedAgent

# 1. Spawn Mock Upstream API on port 9000
up_code = '''
from fastapi import FastAPI
app = FastAPI()
@app.get("/v1/models")
def get_models(): return {"object": "list", "models": ["llama-3-8b", "deepseek-coder"]}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=9000, log_level="error")
'''
with open("mock_upstream.py", "w") as f: f.write(up_code)
up_proc = subprocess.Popen([sys.executable, "mock_upstream.py"])
time.sleep(1.2)

# 2. Spawn Gateway on port 8000 (Targeting Upstream: 9000)
gw_proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "gateway.main:app", "--port", "8000", "--log-level", "error"])
time.sleep(1.5)
def mock_broadcaster(rec, amt, memo):
    txid, nf = secrets.token_hex(32), secrets.token_hex(32)
    with sqlite3.connect("state.db") as c:
        c.execute("INSERT OR REPLACE INTO settlement_notes VALUES (?,?,?,?,1)", (txid, amt, memo, nf))
    return txid

try:
    print("[*] Agent querying Gateway (8000) for upstream (9000) route...")
    agent = ShieldedAgent(settlement_broadcaster=mock_broadcaster)
    resp = agent.get("http://127.0.0.1:8000/v1/models")
    print(f"[✔] Reverse-Proxy Clearance Success! Status: {resp.status_code}")
    print(f"    Upstream Payload Delivered: {resp.json()}")
finally:
    up_proc.terminate()
    gw_proc.terminate()
    import os; os.unlink("mock_upstream.py")
