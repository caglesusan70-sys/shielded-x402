import enum
from dataclasses import dataclass
from typing import Optional, Protocol
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from client_sdk.memo import unpack_x402_memo
from gateway.challenge import is_expired

class ClearanceStatus(str, enum.Enum):
    CLEARED = "CLEARED"
    CHALLENGE_NOT_FOUND = "CHALLENGE_NOT_FOUND"
    CHALLENGE_EXPIRED = "CHALLENGE_EXPIRED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    PAYMENT_NOT_FOUND = "PAYMENT_NOT_FOUND"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    MEMO_CORRUPTED = "MEMO_CORRUPTED"
    MEMO_MISMATCH = "MEMO_MISMATCH"
    NULLIFIER_REUSED = "NULLIFIER_REUSED"
    ALREADY_CONSUMED = "ALREADY_CONSUMED"

@dataclass(frozen=True)
class AuthParameters:
    invoice_id: str
    txid: str
    pk_agent_hex: str
    signature_hex: str

@dataclass(frozen=True)
class ShieldedNoteRecord:
    txid: str
    amount_zat: int
    raw_memo: bytes
    nullifier_hex: str
    confirmed: bool

@dataclass(frozen=True)
class ClearanceResult:
    status: ClearanceStatus
    http_status_code: int
    error_message: Optional[str] = None
    @property
    def is_cleared(self) -> bool:
        return self.status == ClearanceStatus.CLEARED

class StateStoreProtocol(Protocol):
    def get_challenge(self, invoice_id: str) -> Optional[dict]: ...
    def mark_invoice_consumed(self, invoice_id: str) -> bool: ...
    def get_settlement_note(self, txid: str) -> Optional[ShieldedNoteRecord]: ...
    def is_nullifier_spent(self, nullifier_hex: str) -> bool: ...
    def register_spent_nullifier(self, nullifier_hex: str, invoice_id: str) -> bool: ...

class ClearanceEngine:
    def __init__(self, state_store: StateStoreProtocol):
        self.state = state_store

    def evaluate_request(self, auth: AuthParameters, route_path: str) -> ClearanceResult:
        rec = self.state.get_challenge(auth.invoice_id)
        if not rec:
            return ClearanceResult(ClearanceStatus.CHALLENGE_NOT_FOUND, 404, "Invoice not found")
        if rec.get("consumed", False):
            return ClearanceResult(ClearanceStatus.ALREADY_CONSUMED, 403, "Invoice already redeemed")
        if is_expired(rec["valid_until"]):
            return ClearanceResult(ClearanceStatus.CHALLENGE_EXPIRED, 402, "Challenge expired")
        if rec.get("route_path") != route_path:
            return ClearanceResult(ClearanceStatus.CHALLENGE_NOT_FOUND, 403, "Route mismatch")

        try:
            pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(auth.pk_agent_hex))
            pk.verify(bytes.fromhex(auth.signature_hex), f"{rec['challenge_hex']}:{auth.txid}".encode("ascii"))
        except (InvalidSignature, ValueError) as err:
            return ClearanceResult(ClearanceStatus.INVALID_SIGNATURE, 401, str(err))

        note = self.state.get_settlement_note(auth.txid)
        if not note:
            return ClearanceResult(ClearanceStatus.PAYMENT_NOT_FOUND, 402, "Note not found")
        if note.amount_zat < rec["amount_zat"]:
            return ClearanceResult(ClearanceStatus.INSUFFICIENT_FUNDS, 402, "Insufficient funds")

        memo = unpack_x402_memo(note.raw_memo)
        if not memo:
            return ClearanceResult(ClearanceStatus.MEMO_CORRUPTED, 400, "Corrupted memo")
        if memo.invoice_id != auth.invoice_id or memo.pk_agent != bytes.fromhex(auth.pk_agent_hex):
            return ClearanceResult(ClearanceStatus.MEMO_MISMATCH, 403, "Memo mismatch")

        if self.state.is_nullifier_spent(note.nullifier_hex):
            return ClearanceResult(ClearanceStatus.NULLIFIER_REUSED, 403, "Nullifier spent")

        try:
            if self.state.register_spent_nullifier(note.nullifier_hex, auth.invoice_id) is False:
                return ClearanceResult(ClearanceStatus.NULLIFIER_REUSED, 403, "Nullifier spent")
        except Exception:
            return ClearanceResult(ClearanceStatus.NULLIFIER_REUSED, 403, "Nullifier spent")
        self.state.mark_invoice_consumed(auth.invoice_id)
        return ClearanceResult(ClearanceStatus.CLEARED, 200)
