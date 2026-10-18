import sqlite3, time
from gateway.validator import ShieldedNoteRecord

class SQLiteStateStore:
    def __init__(self, p="state.db"):
        self.p = p
        self._m = sqlite3.connect(":memory:", check_same_thread=False) if p == ":memory:" else None
        with self._c() as c:
            if not self._m: c.execute("PRAGMA journal_mode=WAL;")
            c.executescript("""
            CREATE TABLE IF NOT EXISTS challenges (invoice_id TEXT PRIMARY KEY, challenge_hex TEXT, amount_zat INT, valid_until INT, route_path TEXT, consumed INT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS settlement_notes (txid TEXT PRIMARY KEY, amount_zat INT, raw_memo BLOB, nullifier_hex TEXT UNIQUE, confirmed INT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS spent_nullifiers (nullifier_hex TEXT PRIMARY KEY, invoice_id TEXT, claimed_at INT);
            """)
    def _c(self):
        return self._m if self._m else sqlite3.connect(self.p, timeout=5.0)

    def get_challenge(self, i):
        with self._c() as c:
            r = c.execute("SELECT challenge_hex, amount_zat, valid_until, route_path, consumed FROM challenges WHERE invoice_id=?", (i,)).fetchone()
            return {"challenge_hex": r[0], "amount_zat": r[1], "valid_until": r[2], "route_path": r[3], "consumed": bool(r[4])} if r else None

    def save_challenge(self, r):
        with self._c() as c:
            c.execute("INSERT OR REPLACE INTO challenges VALUES (?,?,?,?,?,0)", (r.invoice_id, r.challenge_hex, r.amount_zat, r.valid_until, r.route_path))

    def mark_invoice_consumed(self, i):
        with self._c() as c: c.execute("UPDATE challenges SET consumed=1 WHERE invoice_id=?", (i,))
    def get_settlement_note(self, t):
        with self._c() as c:
            r = c.execute("SELECT txid, amount_zat, raw_memo, nullifier_hex, confirmed FROM settlement_notes WHERE txid=?", (t,)).fetchone()
            return ShieldedNoteRecord(r[0], r[1], bytes(r[2]), r[3], bool(r[4])) if r else None

    def is_nullifier_spent(self, n):
        with self._c() as c: return c.execute("SELECT 1 FROM spent_nullifiers WHERE nullifier_hex=?", (n,)).fetchone() is not None

    def register_spent_nullifier(self, n, i):
        try:
            with self._c() as c: c.execute("INSERT INTO spent_nullifiers VALUES (?,?,?)", (n, i, int(time.time())))
            return True
        except sqlite3.DatabaseError:
            return False
