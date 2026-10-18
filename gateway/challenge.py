import hashlib, secrets, time
from typing import NamedTuple

class ChallengeRecord(NamedTuple):
    invoice_id: str
    challenge_hex: str
    amount_zat: int
    valid_until: int
    route_path: str

def create_challenge(route_path: str, amount_zat: int, ttl_seconds: int = 300) -> ChallengeRecord:
    inv_id = f"inv_{secrets.token_hex(6)}"
    ttl = int(time.time()) + ttl_seconds
    h = hashlib.blake2b(digest_size=32)
    h.update(f"{inv_id}{route_path}{amount_zat}{ttl}".encode("ascii"))
    return ChallengeRecord(inv_id, h.hexdigest(), amount_zat, ttl, route_path)

def is_expired(valid_until: int) -> bool:
    return int(time.time()) > valid_until
