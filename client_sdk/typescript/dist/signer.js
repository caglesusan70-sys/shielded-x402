import * as ed from "@noble/ed25519";
const toHex = (b) => Array.from(b).map(x => x.toString(16).padStart(2, "0")).join("");
export class EphemeralSigner {
    privKey;
    pubKey;
    constructor() {
        this.privKey = ed.utils.randomPrivateKey();
        this.pubKey = ed.getPublicKey(this.privKey);
    }
    get pubKeyHex() {
        return toHex(this.pubKey);
    }
    async signChallenge(challengeHex, txid) {
        const msg = new TextEncoder().encode(`${challengeHex}:${txid}`);
        const sig = await ed.signAsync(msg, this.privKey);
        return toHex(sig);
    }
}
