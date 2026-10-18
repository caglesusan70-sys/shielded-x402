export type Broadcaster = (recipient: string, amountZat: bigint, memo: Uint8Array) => Promise<string>;
export declare class ShieldedAgent {
    private broadcaster?;
    constructor(broadcaster?: Broadcaster | undefined);
    parseChallenge(authHdr: string): Record<string, string>;
    get(url: string, init?: RequestInit): Promise<Response>;
}
