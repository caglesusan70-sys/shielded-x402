import httpx
from fastapi import Request, Response

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "te", "trailers",
    "transfer-encoding", "upgrade", "content-length"
}

def clean_headers(headers: httpx.Headers) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP}
async def proxy_request(upstream_base: str, path: str, request: Request) -> Response:
    url = f"{upstream_base.rstrip('/')}/{path.lstrip('/')}"
    content = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.request(
            method=request.method,
            url=url,
            params=request.query_params,
            content=content,
            headers=headers
        )
        return Response(content=resp.content, status_code=resp.status_code, headers=clean_headers(resp.headers))
