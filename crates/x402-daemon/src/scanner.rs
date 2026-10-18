use std::time::Duration;
use tokio::time::sleep;
use crate::memo::parse_memo;

pub struct Scanner {
    pub grpc_url: String,
}

impl Scanner {
    pub fn new(grpc_url: String) -> Self {
        Self { grpc_url }
    }

    pub async fn run_with_reconnect(&self) {
        let mut backoff = Duration::from_secs(1);
        loop {
            println!("[x402-daemon] Connecting to lightwalletd at {}...", self.grpc_url);
            sleep(backoff).await;
            backoff = std::cmp::min(backoff * 2, Duration::from_secs(30));
        }
    }
}
