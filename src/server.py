import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from auth_db import last_messages, save_message, verify_login


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "chat_users.db"
DEFAULT_LOG = ROOT / "logs" / "chat_events.jsonl"


@dataclass
class Client:
    username: str
    writer: asyncio.StreamWriter
    source_ip: str
    source_port: int


clients: dict[str, Client] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_log(log_path: Path, event: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event["timestamp"] = utc_now()
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


async def send(writer: asyncio.StreamWriter, message: str) -> None:
    writer.write((message + "\n").encode("utf-8"))
    await writer.drain()


async def read_line(reader: asyncio.StreamReader, timeout: float | None = None) -> str:
    if timeout is None:
        data = await reader.readline()
    else:
        data = await asyncio.wait_for(reader.readline(), timeout=timeout)
    if not data:
        raise ConnectionError("cliente desligou")
    return data.decode("utf-8", errors="replace").strip()


async def broadcast(message: str, exclude_username: str | None = None) -> None:
    disconnected = []
    for username, client in list(clients.items()):
        if username == exclude_username:
            continue
        try:
            await send(client.writer, message)
        except (ConnectionError, OSError):
            disconnected.append(username)

    for username in disconnected:
        clients.pop(username, None)


async def update_online_list() -> None:
    online = ", ".join(sorted(list(clients))) or "nenhum"
    await broadcast(f"Online: {online}")


async def send_private(sender: str, target: str, message: str, db_path: Path, log_path: Path, source_ip: str) -> None:
    sender_client = clients.get(sender)
    target_client = clients.get(target)
    if target_client is None:
        if sender_client:
            await send(sender_client.writer, f"[sistema] O utilizador '{target}' nao esta online.")
        return

    save_message(db_path, sender, message, to_user=target)
    write_log(
        log_path,
        {
            "event": "private_message",
            "username": sender,
            "target": target,
            "source_ip": source_ip,
            "message_length": len(message),
        },
    )
    text = f"[privado {sender} -> {target}] {message}"
    await send(target_client.writer, text)
    if sender_client:
        await send(sender_client.writer, text)


async def send_history(username: str, db_path: Path) -> None:
    client = clients.get(username)
    if client is None:
        return
    rows = last_messages(db_path, limit=10)
    if not rows:
        await send(client.writer, "[historico] Sem mensagens guardadas.")
        return
    await send(client.writer, "[historico] Ultimas mensagens:")
    for timestamp, from_user, to_user, message, is_private in rows:
        if is_private:
            if username not in {from_user, to_user}:
                continue
            await send(client.writer, f"[historico privado {from_user} -> {to_user}] {timestamp}: {message}")
        else:
            await send(client.writer, f"[historico {from_user}] {timestamp}: {message}")


async def authenticate(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    db_path: Path,
    log_path: Path,
    source_ip: str,
    source_port: int,
) -> str | None:
    await send(writer, "Username:")
    username = await read_line(reader, timeout=30.0)

    await send(writer, "Password:")
    password = await read_line(reader, timeout=30.0)

    valid_credentials = verify_login(db_path, username, password)
    already_online = username in clients
    success = valid_credentials and not already_online

    write_log(
        log_path,
        {
            "event": "login",
            "username": username,
            "success": success,
            "reason": "ok" if success else "invalid_or_already_online",
            "source_ip": source_ip,
            "source_port": source_port,
        },
    )

    if not success:
        await send(writer, "AUTH_FAIL")
        return None

    await send(writer, "AUTH_OK")
    return username


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    db_path: Path,
    log_path: Path,
) -> None:
    peer = writer.get_extra_info("peername")
    source_ip, source_port = peer[:2] if peer else ("unknown", 0)
    username = None

    try:
        await send(writer, "CHAT")
        username = await authenticate(reader, writer, db_path, log_path, source_ip, source_port)

        if username is None:
            return

        clients[username] = Client(username, writer, source_ip, source_port)
        write_log(log_path, {"event": "join", "username": username, "source_ip": source_ip})

        await send(writer, "Login aceite. Usa /help para ver comandos.")
        await broadcast(f"[sistema] {username} entrou no chat.", exclude_username=username)
        await update_online_list()

        while True:
            message = await read_line(reader, timeout=None)

            if message == "/quit":
                await send(writer, "A sair do chat.")
                break

            if message == "/help":
                await send(writer, "Comandos: /who, /msg utilizador mensagem, /history, /help, /quit")
                continue

            if message == "/who":
                online = ", ".join(sorted(clients)) or "nenhum"
                await send(writer, f"Online: {online}")
                continue

            if message == "/history":
                await send_history(username, db_path)
                continue

            if message.startswith("/msg "):
                parts = message.split(" ", 2)
                if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
                    await send(writer, "Uso: /msg utilizador mensagem")
                    continue
                await send_private(username, parts[1].strip(), parts[2].strip(), db_path, log_path, source_ip)
                continue

            if not message:
                continue

            save_message(db_path, username, message)
            write_log(
                log_path,
                {
                    "event": "message",
                    "username": username,
                    "source_ip": source_ip,
                    "message_length": len(message),
                },
            )
            await broadcast(f"[{username}] {message}")

    except asyncio.TimeoutError:
        write_log(log_path, {"event": "timeout", "username": username or "", "source_ip": source_ip})
    except (ConnectionError, OSError):
        pass
    finally:
        if username:
            clients.pop(username, None)
            write_log(log_path, {"event": "leave", "username": username, "source_ip": source_ip})
            await broadcast(f"[sistema] {username} saiu do chat.", exclude_username=username)
            await update_online_list()

        writer.close()
        await writer.wait_closed()


async def main_async(args: argparse.Namespace) -> None:
    if not args.db.exists():
        raise SystemExit(f"Base de dados nao encontrada: {args.db}. Executa primeiro: python src/init_db.py")

    write_log(args.log, {"event": "server_start", "host": args.host, "port": args.port})

    server = await asyncio.start_server(
        lambda reader, writer: handle_client(reader, writer, args.db, args.log),
        args.host,
        args.port,
    )

    print(f"Servidor de chat ativo em {args.host}:{args.port}")
    print(f"Base de dados: {args.db}")
    print(f"Logs: {args.log}")

    async with server:
        await server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servidor TCP de chat com autenticacao SQLite.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9091)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))
