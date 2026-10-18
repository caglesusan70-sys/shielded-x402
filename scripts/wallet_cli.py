import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
#!/usr/bin/env python3
import os, sys, argparse, getpass
from pathlib import Path
from client_sdk.zingo_driver import ZingoDaemonDriver

DEFAULT_WALLET_DIR = Path.home() / ".shielded_agent_wallet"

def cmd_init(args):
    wallet_path = Path(args.wallet_dir)
    wallet_path.mkdir(parents=True, exist_ok=True)
    os.chmod(wallet_path, 0o700)
    print(f"[*] Initializing secure wallet at: {wallet_path}")
    seed = getpass.getpass("Enter recovery seed (leave blank for new): ").strip()
    try:
        driver = ZingoDaemonDriver(server_uri=args.server, wallet_dir=str(wallet_path))
        driver.sync()
        print("[✔] Wallet synced & locked (0700).")
    except Exception as e:
        print(f"[!] Note: Storage ready, sync notice: {e}")
def cmd_address(args):
    try:
        driver = ZingoDaemonDriver(server_uri=args.server, wallet_dir=args.wallet_dir)
        print("--- ADDRESS ---", driver._exec_args("addresses"))
    except Exception as e:
        print(f"[!] Error: {e}")

def cmd_info(args):
    try:
        driver = ZingoDaemonDriver(server_uri=args.server, wallet_dir=args.wallet_dir)
        print("--- BALANCES ---", driver.get_balances())
    except Exception as e:
        print(f"[!] Error: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="https://testnet.lightwalletd.com:9067")
    subs = parser.add_subparsers(dest="command", required=True)
    p1 = subs.add_parser("init"); p1.add_argument("--wallet-dir", default=str(DEFAULT_WALLET_DIR))
    p2 = subs.add_parser("address"); p2.add_argument("--wallet-dir", default=str(DEFAULT_WALLET_DIR))
    p3 = subs.add_parser("info"); p3.add_argument("--wallet-dir", default=str(DEFAULT_WALLET_DIR))
    args = parser.parse_args()
    if args.command == "init": cmd_init(args)
    elif args.command == "address": cmd_address(args)
    elif args.command == "info": cmd_info(args)

if __name__ == "__main__": main()
