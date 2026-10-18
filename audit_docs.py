import os, stat
from pathlib import Path

docs_dir = Path("docs")
print("[*] Auditing Documentation & Legal Suite (docs/)...")

required = {
    "protocol-spec.md": ["ZIP-302", "BLAKE2b", "RFC 9421", "Clearance"],
    "sequence-diagram.md": ["mermaid", "sequenceDiagram", "Gateway", "Daemon"],
    "architecture-overview.md": ["Tier 1", "Tier 2", "Tier 3", "WAL"],
    "MNDA_TEMPLATE.md": ["MUTUAL NON-DISCLOSURE", "Confidential Information", "Purpose"],
}
passed = 0
for filename, keywords in required.items():
    fp = docs_dir / filename
    if not fp.exists():
        print(f"  [✘ MISSING] {fp}")
        continue
    text = fp.read_text(encoding="utf-8")
    missing_kw = [kw for kw in keywords if kw not in text]
    if missing_kw:
        print(f"  [✘ INCOMPLETE] {fp} (Missing: {missing_kw})")
        continue
    mode = oct(fp.stat().st_mode & 0o777)
    print(f"  [✔ PASS] {fp} (Perms: {mode})")
    passed += 1

if passed == 4:
    print("\n[✔] ALL 4 DOCUMENTATION & LEGAL ARTIFACTS VERIFIED.")
else:
    print(f"\n[!] {4 - passed} file(s) failed inspection.")
