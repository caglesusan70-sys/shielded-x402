export declare class EphemeralSigner {
    private privKey;
    pubKey: Uint8Array;
    constructor();
    get pubKeyHex(): string;
    signChallenge(challengeHex: string, txid: string): Promise<string>;
}
