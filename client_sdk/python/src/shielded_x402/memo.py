import struct
from typing import NamedTuple, Optional

MEMO_TOTAL_SIZE = 512
MAGIC_PREFIX = b"X402"
FMT = ">4s16s32s"

class ShieldedMemoPayload(NamedTuple):
    invoice_id: str
    pk_agent: bytes

def pack_x402_memo(invoice_id: str, pk_agent: bytes) -> bytes:
    inv = invoice_id.encode("ascii")[:16].ljust(16, b"\x00")
    header = struct.pack(FMT, MAGIC_PREFIX, inv, pk_agent)
    return header.ljust(MEMO_TOTAL_SIZE, b"\x00")

def unpack_x402_memo(raw_memo: bytes) -> Optional[ShieldedMemoPayload]:
    if len(raw_memo) != MEMO_TOTAL_SIZE:
        return None
    prefix, raw_inv, pk = struct.unpack_from(FMT, raw_memo, 0)
    if prefix != MAGIC_PREFIX:
        return None
    try:
        return ShieldedMemoPayload(raw_inv.rstrip(b"\x00").decode("ascii"), pk)
    except UnicodeDecodeError:
        return None
