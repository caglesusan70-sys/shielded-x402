import time, os, subprocess, sys, httpx

print("[1] Spawning Guarded UDS Gateway...")
proc = subprocess.Popen([sys.executable, "-m", "gateway.secure_listener"])

for _ in range(40):
    if os.path.exists("gateway.sock"):
        break
    time.sleep(0.1)

try:
    print("[2] Client connecting via gateway.sock...")
    transport = httpx.HTTPTransport(uds="gateway.sock")
    with httpx.Client(transport=transport) as client:
        resp = client.get("http://localhost/health")
        print(f"[3] Response Code: {resp.status_code}")
        print(f"[4] Response JSON: {resp.json()}")
finally:
    proc.terminate()
    print("[5] Gateway shut down cleanly.")
