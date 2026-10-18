# Shielded x402 Master Makefile

.PHONY: all test lint audit clean

all: lint test

test:
	@echo "[*] Running Shielded x402 Master Test Suite..."
	PYTHONPATH=. python3 run_test_suite.py

lint:
	@echo "[*] Compiling Python source files..."
	python3 -m py_compile gateway/*.py client_sdk/*.py tests/*.py *.py
	@echo "[*] Checking Rust daemon workspace..."
	cargo check --manifest-path crates/x402-daemon/Cargo.toml

audit:
	@echo "[*] Running gateway and root configuration audits..."
	@python3 audit_gateway.py || true
	@python3 audit_root.py || true

clean:
	@echo "[*] Cleaning temporary databases, sockets, and cache files..."
	rm -f state.db state.db-wal state.db-shm gateway.sock fuzzed_state.db demo_state.db
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "[✔] Workspace cleaned successfully."
