mod db;
mod memo;
mod scanner;

use db::{DbWorker, NoteEvent};
use scanner::Scanner;
use tokio::sync::mpsc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("[x402-daemon] Booting Production Settlement Daemon v0.1.0");
    let (tx, rx) = mpsc::channel::<NoteEvent>(1000);
    DbWorker::spawn("state.db".to_string(), rx);
    let scanner = Scanner::new("http://127.0.0.1:9067".to_string());

    tokio::select! {
        _ = scanner.run_with_reconnect() => {},
        _ = tokio::signal::ctrl_c() => {
            println!("\n[x402-daemon] Intercepted SIGINT. Clean shutdown.");
        }
    }
    drop(tx);
    Ok(())
}
