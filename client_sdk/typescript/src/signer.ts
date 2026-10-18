import * as ed from "@noble/ed25519";

const toHex = (b: Uint8Array) => Array.from(b).map(x => x.toString(16).padStart(2, "0")).join("");

export class EphemeralSigner {
  private privKey: Uint8Array;
  public pubKey: Uint8Array;

  constructor() {
    this.privKey = ed.utils.randomPrivateKey();
    this.pubKey = ed.getPublicKey(this.privKey);
  }

  get pubKeyHex(): string {
    return toHex(this.pubKey);
  }
  async signChallenge(challengeHex: string, txid: string): Promise<string> {
    const msg = new TextEncoder().encode(`${challengeHex}:${txid}`);
    const sig = await ed.signAsync(msg, this.privKey);
    return toHex(sig);
  }
}
