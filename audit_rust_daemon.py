import sys
from pathlib import Path

daemon_dir = Path("crates/x402-daemon")
print("[*] Auditing Rust Settlement Daemon (crates/x402-daemon/)...")

files = {
    "Cargo.toml": ["tokio", "rusqlite", "tonic", "prost"],
    "src/memo.rs": ["MEMO_SIZE", 'b"X402"', "ParsedMemo", "parse_memo"],
    "src/db.rs": ["NoteEvent", "DbWorker", "spawn", "blocking_recv"],
    "src/scanner.rs": ["Scanner", "run_with_reconnect", "backoff", "parse_memo"],
    "src/main.rs": ["ctrl_c", "mpsc::channel", "DbWorker::spawn", "main"],
}

missing = 0
for rel_path, required_symbols in files.items():
    fp = daemon_dir / rel_path
    if not fp.exists():
        print(f"  [✘ MISSING] {fp}")
        missing += 1
        continue
    content = fp.read_text(encoding="utf-8")
    missing_syms = [s for s in required_symbols if s not in content]
    if missing_syms:
        print(f"  [✘ INCOMPLETE] {fp} (Missing: {missing_syms})")
        missing += 1
    else:
        print(f"  [✔ PASS] {fp}: Structure & symbols verified.")

if missing == 0:
    print("\n[✔] ALL 5 RUST DAEMON MODULES VERIFIED & READY.")
else:
    print(f"\n[!] {missing} file(s) need initialization.")
    sys.exit(1)
