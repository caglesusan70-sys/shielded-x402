# Shielded x402: Architecture Overview
**CONFIDENTIAL & PROPRIETARY** (c) 2026. All Rights Reserved.

## System Topology
- Tier 1: Client Agent SDK (Python / HTTPX)
- Tier 2: API Gateway (FastAPI / ASGI Middleware)
- Tier 3: Settlement Daemon (Rust / librustzcash / gRPC)
- State Layer: Local SQLite configured with PRAGMA journal_mode=WAL.

## Execution Modes
- Mode A (<500ms): Zero-conf mempool stream ingestion for micropayments.
- Mode B (Confirmed): 1-confirmation wait for high-value macro transfers.
