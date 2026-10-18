pub const MEMO_SIZE: usize = 512;
pub const PREFIX: &[u8; 4] = b"X402";

#[derive(Debug, Clone)]
pub struct ParsedMemo {
    pub invoice_id: String,
    pub pk_agent: [u8; 32],
}

pub fn parse_memo(raw: &[u8]) -> Option<ParsedMemo> {
    if raw.len() != MEMO_SIZE || &raw[0..4] != PREFIX {
        return None;
    }
    let inv_slice = &raw[4..20];
    let end = inv_slice.iter().position(|&b| b == 0).unwrap_or(16);
    let invoice_id = std::str::from_utf8(&inv_slice[..end]).ok()?.to_string();

    let mut pk_agent = [0u8; 32];
    pk_agent.copy_from_slice(&raw[20..52]);
    Some(ParsedMemo { invoice_id, pk_agent })
}
