import os, re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from gateway.challenge import create_challenge
from gateway.validator import ClearanceEngine, AuthParameters
from gateway.state import SQLiteStateStore
from gateway.proxy import proxy_request

app = FastAPI(title="Shielded x402 Reverse Proxy")
store = SQLiteStateStore(os.getenv("SQLITE_PATH", "state.db"))
engine = ClearanceEngine(store)

UPSTREAM_URL = os.getenv("UPSTREAM_API_URL", "http://127.0.0.1:9000")
MERCHANT_UA = os.getenv("MERCHANT_UA", "u1mockmerchantdiversifiedaddress99999")
PRICE_ZAT = int(os.getenv("PRICE_ZAT", "50000"))
PROTECTED_PREFIXES = ["v1/"]
HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
def sanitize_hex(val: str, expected_len: int) -> bool:
    return bool(val and len(val) == expected_len and HEX_RE.match(val))

@app.get("/healthz")
async def healthz():
    return {"status": "healthy", "upstream": UPSTREAM_URL, "engine": "online"}
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def pipeline_gateway(path: str, request: Request):
    # Pass through unprotected paths
    if not any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return await proxy_request(UPSTREAM_URL, path, request)

    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("x402 "):
        c = create_challenge(f"/{path}", PRICE_ZAT, ttl_seconds=300)
        store.save_challenge(c)
        h = f'x402 invoice_id="{c.invoice_id}", recipient="{MERCHANT_UA}", amount_zat="{c.amount_zat}", challenge="{c.challenge_hex}", valid_until="{c.valid_until}"'
        return JSONResponse(status_code=402, headers={"WWW-Authenticate": h}, content={"error": "Payment Required", "invoice_id": c.invoice_id})

    params = {}
    for item in auth[5:].split(","):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            params[k.strip()] = v.strip().strip('"')

    for k in ["invoice_id", "txid", "pk_agent", "signature"]:
        if k not in params:
            return JSONResponse(status_code=400, content={"error": f"Missing {k}"})

    if not sanitize_hex(params["txid"], 64) or not sanitize_hex(params["pk_agent"], 64) or not sanitize_hex(params["signature"], 128):
        return JSONResponse(status_code=400, content={"error": "Malformed cryptographic parameters"})

    auth_params = AuthParameters(params["invoice_id"], params["txid"], params["pk_agent"], params["signature"])
    res = engine.evaluate_request(auth_params, f"/{path}")
    if not res.is_cleared:
        return JSONResponse(status_code=res.http_status_code, content={"error": res.error_message, "code": res.status.value})

    # Clearance verified -> Forward to Upstream API
    return await proxy_request(UPSTREAM_URL, path, request)
