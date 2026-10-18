"""
client_sdk/zingo_driver.py
==========================
Headless driver wrapping zingo-cli for autonomous Orchard-shielded micropayments.
Includes automatic simulation/mock fallback when zingo-cli binary is absent.
"""

import os
import json
import shutil
import secrets
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class ZingoDaemonDriver:
    """Headless driver wrapping zingo-cli for programmatic Zcash Orchard spending."""

    def __init__(
        self,
        server_uri: str = "https://testnet.lightwalletd.com:9067",
        wallet_dir: Optional[str] = None,
        mock_mode: bool = False,
    ):
        self.server_uri = server_uri
        self.wallet_dir = wallet_dir or str(Path.home() / ".shielded_agent_wallet")
        self.mock_mode = mock_mode or os.getenv("ZINGO_MOCK_MODE", "0") == "1"
        self._bin = shutil.which("zingo-cli")

        if not self._bin and not self.mock_mode:
            self.mock_mode = True
            print("[!] Notice: 'zingo-cli' binary not found. Engaging safe MOCK mode.")

    def _exec_args(self, *subcommand: str) -> Dict[str, Any]:
        if self.mock_mode:
            cmd = subcommand[0] if subcommand else ""
            if cmd == "balance":
                return {"orchard_balance": 1500000, "sapling_balance": 0, "transparent_balance": 0}
            elif cmd == "sync":
                return {"result": "success", "latest_block": 2845920}
            elif cmd == "addresses":
                return {"orchard": ["utest1mockorchardshieldedaddress0000000000000000000000"]}
            return {"result": "mock_executed"}

        if not self._bin:
            raise FileNotFoundError("zingo-cli binary not found in system PATH.")

        args: List[str] = [
            self._bin,
            "--server", self.server_uri,
            "--data-dir", self.wallet_dir,
            *subcommand,
        ]
        res = subprocess.run(args, capture_output=True, text=True, check=True)
        try:
            return json.loads(res.stdout)
        except json.JSONDecodeError:
            return {"raw_output": res.stdout.strip()}

    def get_balances(self) -> Dict[str, Any]:
        return self._exec_args("balance")

    def sync(self) -> Dict[str, Any]:
        return self._exec_args("sync")

    def send_payment(
        self, recipient_address: str, amount_zatoshis: int, memo_hex: str
    ) -> str:
        if self.mock_mode:
            mock_txid = secrets.token_hex(32)
            print(f"[ZingoDriver Mock] Remitted {amount_zatoshis} zatoshis to {recipient_address[:12]}... [TxID: {mock_txid[:16]}...]")
            return mock_txid

        response = self._exec_args("send", recipient_address, str(amount_zatoshis), memo_hex)
        return response.get("txid", response.get("txids", [""])[0])
