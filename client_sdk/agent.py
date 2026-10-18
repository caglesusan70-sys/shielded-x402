import httpx
from client_sdk.signer import EphemeralSigner
from client_sdk.memo import pack_x402_memo

class ShieldedAgent:
    def __init__(self, settlement_broadcaster=None):
        self.broadcaster = settlement_broadcaster
        self.client = httpx.Client()
    def get(self, url: str):
        resp = self.client.get(url)
        if resp.status_code != 402:
            return resp

        auth = resp.headers.get("WWW-Authenticate", "")
        params = {}
        for item in auth[5:].split(","):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                params[k.strip()] = v.strip().strip('"')

        signer = EphemeralSigner()
        memo = pack_x402_memo(params["invoice_id"], signer.public_key_bytes)

        if self.broadcaster:
            txid = self.broadcaster(params["recipient"], int(params["amount_zat"]), memo)
        else:
            raise RuntimeError("Broadcaster required to submit settlement")

        sig = signer.sign_challenge(params["challenge"], txid)
        auth_hdr = f'x402 invoice_id="{params["invoice_id"]}", txid="{txid}", pk_agent="{signer.public_key_hex}", signature="{sig}"'
        return self.client.get(url, headers={"Authorization": auth_hdr})
