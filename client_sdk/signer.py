from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class EphemeralSigner:
    def __init__(self):
        self.sk = ed25519.Ed25519PrivateKey.generate()
        self.pk = self.sk.public_key()

    @property
    def public_key_bytes(self) -> bytes:
        return self.pk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)

    @property
    def public_key_hex(self) -> str:
        return self.public_key_bytes.hex()

    def sign_challenge(self, challenge_hex: str, txid: str) -> str:
        msg = f"{challenge_hex}:{txid}".encode("ascii")
        return self.sk.sign(msg).hex()
