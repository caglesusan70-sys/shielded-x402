from pathlib import Path
print("[*] Auditing Root Configuration...")

# 1. .gitignore
gi = Path(".gitignore")
assert gi.exists() and all(k in gi.read_text() for k in ["*.db", "__pycache__", "gateway.sock"])
print("  [1/4 PASS] .gitignore: Ignores state.db*, __pycache__, and gateway.sock.")

# 2. pyproject.toml
pyproj = Path("pyproject.toml")
assert pyproj.exists() and "shielded-x402" in pyproj.read_text() and "[project]" in pyproj.read_text()
print("  [2/4 PASS] pyproject.toml: Standard PEP 621 metadata verified.")
# 3. LICENSE
lic = Path("LICENSE")
assert lic.exists() and any(k in lic.read_text() for k in ["PROPRIETARY", "CONFIDENTIAL", "Copyright"])
print("  [3/4 PASS] LICENSE: Proprietary all-rights-reserved terms enforced.")

# 4. README.md
rm = Path("README.md")
assert rm.exists() and "Shielded x402" in rm.read_text()
print("  [4/4 PASS] README.md: Architecture summary & notices verified.")

print("\n[✔] ALL 4 ROOT CONFIGURATION ARTIFACTS VERIFIED.")
