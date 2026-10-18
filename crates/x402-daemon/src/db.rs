use rusqlite::{params, Connection};
use tokio::sync::mpsc;

#[derive(Debug)]
pub struct NoteEvent {
    pub txid: String,
    pub amount: i64,
    pub memo: Vec<u8>,
    pub nullifier: String,
}

pub struct DbWorker;

impl DbWorker {
    pub fn spawn(path: String, mut rx: mpsc::Receiver<NoteEvent>) {
        std::thread::spawn(move || {
            let conn = Connection::open(&path).expect("Failed DB open");
            conn.pragma_update(None, "journal_mode", "WAL").unwrap();
            conn.pragma_update(None, "busy_timeout", 5000).unwrap();

            while let Some(note) = rx.blocking_recv() {
                let _ = conn.execute(
                    "INSERT OR REPLACE INTO settlement_notes VALUES (?1, ?2, ?3, ?4, 1)",
                    params![note.txid, note.amount, note.memo, note.nullifier],
                );
            }
        });
    }
}
