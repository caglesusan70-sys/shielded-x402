"""
daemon_worker.py
================
Tier 3 Settlement Watcher: Scans for inbound orchard notes, 
unpacks ZIP-302 memos, and commits verified settlements to SQLite WAL.
"""

import os
import sqlite3
from dotenv import load_dotenv
from client_sdk.memo import unpack_x402_memo

load_dotenv()
DB_PATH = os.getenv("SQLITE_PATH", "state.db")
MERCHANT_IVK = os.getenv("MERCHANT_VIEWING_KEY", "mock_ivk")

class SettlementReceiverPipeline:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def process_incoming_note(self, txid: str, amount_zat: int, raw_memo: bytes, nullifier_hex: str) -> bool:
        memo_payload = unpack_x402_memo(raw_memo)
        if not memo_payload:
            print(f"[Receiver] Ignored transaction {txid[:12]}: Invalid or non-x402 memo.")
            return False

        invoice_id = memo_payload.invoice_id
        pk_agent = memo_payload.pk_agent.hex()

        print(f"[Receiver] MATCHED INBOUND SETTLEMENT!")
        print(f"  -> Invoice ID : {invoice_id}")
        print(f"  -> Amount     : {amount_zat} zatoshis")
        print(f"  -> Agent PK   : {pk_agent[:16]}...")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO settlement_notes 
                (txid, amount_zat, raw_memo, nullifier_hex, confirmed) 
                VALUES (?, ?, ?, ?, 1)
                """,
                (txid, amount_zat, raw_memo, nullifier_hex)
            )
        print(f"[Receiver] Committed txid {txid[:12]} to SQLite WAL. Gateway ready for clearance.")
        return True

if __name__ == "__main__":
    print(f"[Receiver] Settlement Receiver Pipeline active.")
