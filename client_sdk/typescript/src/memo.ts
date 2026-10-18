export const MEMO_TOTAL_SIZE = 512;
export const MAGIC_PREFIX = new Uint8Array([0x58, 0x34, 0x30, 0x32]); // 'X402'

export function packX402Memo(invoiceId: string, pkAgent: Uint8Array): Uint8Array {
  if (pkAgent.length !== 32) throw new Error("pkAgent must be 32 bytes");
  const memo = new Uint8Array(MEMO_TOTAL_SIZE);
  memo.set(MAGIC_PREFIX, 0);
  const enc = new TextEncoder().encode(invoiceId.slice(0, 16));
  memo.set(enc, 4);
  memo.set(pkAgent, 20);
  return memo;
}
export function unpackX402Memo(raw: Uint8Array): { invoiceId: string; pkAgent: Uint8Array } | null {
  if (raw.length !== MEMO_TOTAL_SIZE) return null;
  for (let i = 0; i < 4; i++) {
    if (raw[i] !== MAGIC_PREFIX[i]) return null;
  }
  const dec = new TextDecoder("ascii").decode(raw.slice(4, 20)).replace(/\0+$/, "");
  return { invoiceId: dec, pkAgent: raw.slice(20, 52) };
}
