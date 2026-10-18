export declare const MEMO_TOTAL_SIZE = 512;
export declare const MAGIC_PREFIX: Uint8Array<ArrayBuffer>;
export declare function packX402Memo(invoiceId: string, pkAgent: Uint8Array): Uint8Array;
export declare function unpackX402Memo(raw: Uint8Array): {
    invoiceId: string;
    pkAgent: Uint8Array;
} | null;
