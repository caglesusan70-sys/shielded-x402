import hashlib, secrets, time
from typing import NamedTuple

class ChallengeRecord(NamedTuple):
    invoice_id: str
    challenge_hex: str
    merchant_zat: int
    fee_zat: int
    amount_zat: int  # total_zat = merchant_zat + fee_zat
    valid_until: int
    route_path: str

def calculate_split(merchant_zat: int, fee_bps: int = 0) -> tuple[int, int]:
    fee_zat = (merchant_zat * fee_bps) // 10000 if fee_bps > 0 else 0
    return fee_zat, merchant_zat + fee_zat
def create_challenge(route_path: str, merchant_zat: int, ttl_seconds: int = 300, fee_bps: int = 0) -> ChallengeRecord:
    inv_id = f"inv_{secrets.token_hex(6)}"
    ttl = int(time.time()) + ttl_seconds
    fee_zat, total_zat = calculate_split(merchant_zat, fee_bps)
    h = hashlib.blake2b(digest_size=32)
    h.update(f"{inv_id}{route_path}{total_zat}{ttl}".encode("ascii"))
    return ChallengeRecord(inv_id, h.hexdigest(), merchant_zat, fee_zat, total_zat, ttl, route_path)

def is_expired(valid_until: int) -> bool:
    return int(time.time()) > valid_until
