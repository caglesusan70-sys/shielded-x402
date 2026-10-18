import os, socket, struct, uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from uvicorn.protocols.http.auto import AutoHTTPProtocol

SOCKET_PATH = "gateway.sock"
SO_PEERCRED = 17
UCRED_SIZE = struct.calcsize("3i")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(SOCKET_PATH):
        os.chmod(SOCKET_PATH, 0o600)
    yield
    if os.path.exists(SOCKET_PATH):
        try: os.unlink(SOCKET_PATH)
        except OSError: pass

app = FastAPI(title="Shielded x402 Gateway", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "secure", "gate": "kernel_verified", "uid": os.getuid()}
def verify_peer(sock: socket.socket):
    cred = sock.getsockopt(socket.SOL_SOCKET, SO_PEERCRED, UCRED_SIZE)
    pid, uid, gid = struct.unpack("3i", cred)
    if uid != os.getuid():
        raise PermissionError(f"Foreign UID {uid} rejected (PID: {pid})")
    return pid, uid, gid

class GuardedProtocol(AutoHTTPProtocol):
    def connection_made(self, transport):
        sock = transport.get_extra_info("socket")
        if sock:
            try:
                pid, uid, _ = verify_peer(sock)
                print(f"[Gate 1 PASSED] Client PID: {pid}, UID: {uid}")
            except PermissionError as e:
                print(f"[Gate 1 BLOCKED] {e}")
                transport.abort()
                return
        super().connection_made(transport)
def run():
    if os.path.exists(SOCKET_PATH):
        try: os.unlink(SOCKET_PATH)
        except OSError: pass

    cfg = uvicorn.Config(app=app, uds=SOCKET_PATH, http=GuardedProtocol, log_level="warning")
    server = uvicorn.Server(cfg)
    server.run()

if __name__ == "__main__":
    run()
