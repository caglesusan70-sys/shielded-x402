import os, sys, subprocess

tests = [
    ("tests/test_clearance.py", "Core Clearance Pipeline (12 Outcomes)"),
    ("tests/fuzz_concurrency.py", "Multi-Threaded Double-Spend Fuzz"),
    ("test_live.py", "Live End-to-End HTTP Negotiation (TCP :8000)"),
    ("test_uds_kernel.py", "Kernel UDS Process Isolation (SO_PEERCRED)"),
]

print("================================================================")
print("       SHIELDED x402 — MASTER TEST & VERIFICATION SUITE         ")
print("================================================================\n")
env = os.environ.copy()
env["PYTHONPATH"] = "."

passed = 0
for script, desc in tests:
    print(f"[*] Running: {desc} ({script})...")
    res = subprocess.run([sys.executable, script], capture_output=True, text=True, env=env)
    if res.returncode == 0:
        print(f"    [✔ PASS] {script}\n")
        passed += 1
    else:
        print(f"    [✘ FAIL] {script}")
        print(res.stderr or res.stdout)
        print()

print(f"RESULTS: {passed}/{len(tests)} test runners passed successfully.")
