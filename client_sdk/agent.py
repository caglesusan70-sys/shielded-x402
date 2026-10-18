"""
client_sdk/agent.py
===================
Universal autonomous agent client supporting both legacy tests and 
zingo_driver integration, ZIP-302 memo packing, and RFC 9421 clearance.
"""

import re
import httpx
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from client_sdk.zingo_driver import ZingoDaemonDriver
from client_sdk.memo import pack_x402_memo


class ShieldedAgent:
    """Universal autonomous agent client supporting multi-pattern initialization."""

    def __init__(
        self,
        zingo_driver: Optional[ZingoDaemonDriver] = None,
        upstream_url: Optional[str] = None,
        zcash_wallet_adapter=None,
        settlement_broadcaster=None,
    ):
        self.driver = zingo_driver
        self.upstream_url = (upstream_url or "http://127.0.0.1:8000").rstrip("/")
        
        # Resolve broadcaster handle
        if settlement_broadcaster:
            self.broadcaster = settlement_broadcaster
        elif zcash_wallet_adapter:
            self.broadcaster = lambda r, a, m: zcash_wallet_adapter.send_shielded_payment(r, a, m)
        elif zingo_driver:
            self.broadcaster = lambda r, a, m: zingo_driver.send_payment(r, a, m.hex())
        else:
            self.broadcaster = lambda r, a, m: "0" * 64

        self.client = httpx.Client(timeout=30.0)
        
        # Ephemeral Ed25519 identity keypair (RFC 9421)
        self.identity_private_key = ed25519.Ed25519PrivateKey.generate()
        self.identity_public_key = self.identity_private_key.public_key()
        self.pk_bytes = self.identity_public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def _parse_x402_header(self, auth_header: str) -> Dict[str, str]:
        params = {}
        if not auth_header.startswith("x402 "):
            return params
        pattern = re.compile(r'([a-zA-Z0-9_-]+)=(?:"([^"]*)"|([^\s,]+))')
        for match in pattern.finditer(auth_header[5:]):
            key = match.group(1)
            val = match.group(2) if match.group(2) is not None else match.group(3)
            params[key] = val
        return params

    def get(self, url: str, **kwargs) -> httpx.Response:
        """Legacy support for test_live.py style calls."""
        full_url = url if url.startswith("http") else f"{self.upstream_url}/{url.lstrip('/')}"
        resp = self.client.get(full_url, **kwargs)
        if resp.status_code != 402:
            return resp

        auth_header = resp.headers.get("WWW-Authenticate", "")
        params = self._parse_x402_header(auth_header)
        invoice_id = params.get("invoice_id")
        recipient = params.get("recipient")
        challenge = params.get("challenge")
        amount_zat = int(params.get("amount_zat", 50000))

        memo_bytes = pack_x402_memo(invoice_id=invoice_id, pk_agent=self.pk_bytes)
        txid = self.broadcaster(recipient, amount_zat, memo_bytes)

        signing_payload = f"{challenge}:{txid}".encode("ascii")
        signature = self.identity_private_key.sign(signing_payload)

        auth_val = (
            f'x402 invoice_id="{invoice_id}", '
            f'txid="{txid}", '
            f'pk_agent="{self.pk_bytes.hex()}", '
            f'signature="{signature.hex()}"'
        )
        headers = kwargs.get("headers", {})
        headers["Authorization"] = auth_val
        kwargs["headers"] = headers
        return self.client.get(full_url, **kwargs)

    def request(self, endpoint_path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Modern support for test_receiving_pipeline.py style calls."""
        target_url = f"{self.upstream_url}/{endpoint_path.lstrip('/')}"
        payload = payload or {}
        
        response = self.client.post(target_url, json=payload)
        if response.status_code != 402:
            try:
                return response.json()
            except Exception:
                return {"status_code": response.status_code, "raw_text": response.text}

        auth_header = response.headers.get("WWW-Authenticate", "")
        params = self._parse_x402_header(auth_header)
        invoice_id = params.get("invoice_id")
        recipient = params.get("recipient")
        challenge = params.get("challenge")
        amount_zat = int(params.get("amount_zat", 50000))

        memo_bytes = pack_x402_memo(invoice_id=invoice_id, pk_agent=self.pk_bytes)
        txid = self.broadcaster(recipient, amount_zat, memo_bytes)

        signing_payload = f"{challenge}:{txid}".encode("ascii")
        signature = self.identity_private_key.sign(signing_payload)

        retry_headers = {
            "Authorization": (
                f'x402 invoice_id="{invoice_id}", '
                f'txid="{txid}", '
                f'pk_agent="{self.pk_bytes.hex()}", '
                f'signature="{signature.hex()}"'
            )
        }
        final_response = self.client.post(target_url, json=payload, headers=retry_headers)
        try:
            return final_response.json()
        except Exception:
            return {"status_code": final_response.status_code, "raw_text": final_response.text}
