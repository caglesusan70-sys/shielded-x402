import { EphemeralSigner } from "./signer.js";
import { packX402Memo } from "./memo.js";

export type Broadcaster = (recipient: string, amountZat: bigint, memo: Uint8Array) => Promise<string>;

export class ShieldedAgent {
  constructor(private broadcaster?: Broadcaster) {}

  parseChallenge(authHdr: string): Record<string, string> {
    const p: Record<string, string> = {};
    if (!authHdr.startsWith("x402 ")) return p;
    for (const item of authHdr.slice(5).split(",")) {
      const [k, v] = item.split("=").map(s => s.trim().replace(/^"|"$/g, ""));
      if (k && v) p[k] = v;
    }
    return p;
  }
  async get(url: string, init?: RequestInit): Promise<Response> {
    const r1 = await fetch(url, init);
    if (r1.status !== 402) return r1;

    const ch = this.parseChallenge(r1.headers.get("WWW-Authenticate") || "");
    if (!this.broadcaster) throw new Error("Broadcaster required");

    const signer = new EphemeralSigner();
    const memo = packX402Memo(ch.invoice_id, signer.pubKey);
    const txid = await this.broadcaster(ch.recipient, BigInt(ch.amount_zat), memo);
    const sig = await signer.signChallenge(ch.challenge, txid);

    const auth = `x402 invoice_id="${ch.invoice_id}", txid="${txid}", pk_agent="${signer.pubKeyHex}", signature="${sig}"`;
    const headers = new Headers(init?.headers);
    headers.set("Authorization", auth);
    return fetch(url, { ...init, headers });
  }
}
