import argparse
from pathlib import Path

from auth_db import init_database, list_users


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "chat_users.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inicializa a base de dados SQLite do chat.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--reset", action="store_true", help="Apaga e recria a base de dados.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    init_database(args.db, reset=args.reset)
    print(f"Base de dados pronta: {args.db}")
    print("Utilizadores:")
    for username in list_users(args.db):
        print(f"  - {username}")

