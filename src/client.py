import argparse
import getpass
import socket
import sys
import threading


def receive_loop(sock: socket.socket) -> None:
    file = sock.makefile("r", encoding="utf-8", newline="\n")
    try:
        for line in file:
            print(line.rstrip())
    except OSError:
        pass
    finally:
        print("Ligacao fechada.")


def read_line(sock: socket.socket) -> str:
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("servidor desligou")
        data += chunk
    return data.decode("utf-8", errors="replace").strip()


def send_line(sock: socket.socket, text: str) -> None:
    sock.sendall((text + "\n").encode("utf-8"))


def main(args: argparse.Namespace) -> None:
    with socket.create_connection((args.host, args.port), timeout=10) as sock:
        print(read_line(sock))

        print(read_line(sock), end=" ")
        username = input()
        send_line(sock, username)

        print(read_line(sock), end=" ")
        password = getpass.getpass("")
        send_line(sock, password)

        status = read_line(sock)
        if status != "AUTH_OK":
            print("Login falhou.")
            return

        print("Login aceite. Escreve mensagens. Usa /who, /help ou /quit.")

        receiver = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
        receiver.start()

        for line in sys.stdin:
            message = line.rstrip("\n")
            send_line(sock, message)
            if message == "/quit":
                break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cliente do chat TCP.")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=9091)
    return parser.parse_args()


if __name__ == "__main__":
    main(parse_args())

