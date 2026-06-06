import argparse
import queue
import socket
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk


class ChatGui:
    def __init__(self, root: tk.Tk, default_host: str, default_port: int) -> None:
        self.root = root
        self.root.title("CHAT")
        self.root.geometry("1040x680")
        self.root.minsize(900, 590)

        self.colors = {
            "app": "#eef3f8",
            "panel": "#ffffff",
            "border": "#d9e2ec",
            "text": "#102033",
            "muted": "#667085",
            "primary": "#2563eb",
            "primary_dark": "#1d4ed8",
            "success_bg": "#dcfce7",
            "success_fg": "#166534",
            "warn_bg": "#fef3c7",
            "warn_fg": "#92400e",
            "offline_bg": "#e5e7eb",
            "offline_fg": "#475569",
            "private_bg": "#f3e8ff",
            "private_fg": "#6d28d9",
            "other_bg": "#eff6ff",
            "other_fg": "#1e3a8a",
        }
        self.root.configure(bg=self.colors["app"])

        self.sock: socket.socket | None = None
        self.reader = None
        self.connected = False
        self.current_username = ""
        self.inbox: queue.Queue[str] = queue.Queue()

        self.host_var = tk.StringVar(value=default_host)
        self.port_var = tk.StringVar(value=str(default_port))
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Desligado")
        self.online_var = tk.StringVar(value="-")
        self.message_var = tk.StringVar()
        self.online_users: list[str] = []

        self.configure_style()
        self.build_login()
        self.build_chat()
        self.show_login()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(120, self.process_inbox)

    def configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("App.TFrame", background=self.colors["app"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure("Sidebar.TFrame", background="#f8fafc")
        style.configure("Footer.TFrame", background=self.colors["panel"])

        style.configure("Title.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 22, "bold"))
        style.configure("Hero.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 18, "bold"))
        style.configure("ChatTitle.TLabel", background=self.colors["app"], foreground=self.colors["text"], font=("Segoe UI", 20, "bold"))
        style.configure("Section.TLabel", background="#f8fafc", foreground=self.colors["text"], font=("Segoe UI", 10, "bold"))
        style.configure("Panel.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=self.colors["panel"], foreground=self.colors["muted"], font=("Segoe UI", 9))
        style.configure("SidebarMuted.TLabel", background="#f8fafc", foreground=self.colors["muted"], font=("Segoe UI", 9))
        style.configure("SidebarText.TLabel", background="#f8fafc", foreground=self.colors["text"], font=("Segoe UI", 10))

        style.configure("TEntry", padding=8, relief="flat", bordercolor=self.colors["border"], lightcolor=self.colors["border"], darkcolor=self.colors["border"])
        style.configure("Primary.TButton", padding=(14, 9), font=("Segoe UI", 10, "bold"), foreground="#ffffff", background=self.colors["primary"], borderwidth=0)
        style.map("Primary.TButton", background=[("active", self.colors["primary_dark"])])
        style.configure("Secondary.TButton", padding=(12, 8), font=("Segoe UI", 10), foreground=self.colors["text"], background="#edf2f7", borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#e2e8f0")])

    def build_login(self) -> None:
        self.login_frame = ttk.Frame(self.root, style="App.TFrame")
        self.login_frame.columnconfigure(0, weight=1)
        self.login_frame.rowconfigure(0, weight=1)

        card = ttk.Frame(self.login_frame, style="Panel.TFrame", padding=32)
        card.grid(row=0, column=0, sticky="", padx=24, pady=24)
        card.columnconfigure(0, weight=1)

        badge = tk.Label(
            card,
            text="TCP CHAT",
            bg="#dbeafe",
            fg=self.colors["primary"],
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
        )
        badge.grid(row=0, column=0, sticky="w", pady=(0, 14))

        ttk.Label(card, text="CHAT", style="Title.TLabel").grid(row=1, column=0, sticky="w")
        form = ttk.Frame(card, style="Panel.TFrame")
        form.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        form.columnconfigure(1, weight=1)

        self.add_form_row(form, 0, "Servidor / IP", self.host_var)
        self.add_form_row(form, 1, "Porta", self.port_var)
        self.add_form_row(form, 2, "Username", self.username_var)
        self.add_form_row(form, 3, "Password", self.password_var, show="*")

        actions = ttk.Frame(card, style="Panel.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(20, 0))
        ttk.Button(actions, text="Entrar no chat", style="Primary.TButton", command=self.connect).pack(side="left")
        ttk.Button(actions, text="Limpar", style="Secondary.TButton", command=self.clear_login).pack(side="left", padx=(10, 0))

    def add_form_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar, show: str | None = None) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=7, padx=(0, 16))
        ttk.Entry(parent, textvariable=variable, width=38, show=show or "").grid(row=row, column=1, sticky="ew", pady=7)

    def build_chat(self) -> None:
        self.chat_frame = ttk.Frame(self.root, style="App.TFrame", padding=18)
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(1, weight=1)

        header = ttk.Frame(self.chat_frame, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)

        title_box = ttk.Frame(header, style="App.TFrame")
        title_box.grid(row=0, column=0, sticky="w")
        ttk.Label(title_box, text="CHAT", style="ChatTitle.TLabel").pack(anchor="w")

        self.status_chip = tk.Label(
            header,
            textvariable=self.status_var,
            bg=self.colors["offline_bg"],
            fg=self.colors["offline_fg"],
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=6,
        )
        self.status_chip.grid(row=0, column=1, sticky="e")

        body = ttk.Frame(self.chat_frame, style="App.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(body, style="Sidebar.TFrame", padding=18)
        sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        sidebar.configure(width=230)
        sidebar.grid_propagate(False)

        online_header = ttk.Frame(sidebar, style="Sidebar.TFrame")
        online_header.pack(fill="x")
        self.create_user_icon(online_header).pack(side="left", padx=(0, 8))
        ttk.Label(online_header, text="Utilizadores online", style="Section.TLabel").pack(side="left")

        self.online_count_label = tk.Label(
            sidebar,
            text="0 online",
            bg="#e0f2fe",
            fg="#0369a1",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
        )
        self.online_count_label.pack(anchor="w", pady=(12, 10))

        self.online_list_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        self.online_list_frame.pack(fill="x", pady=(0, 18))
        self.update_online_users("-")

        ttk.Button(sidebar, text="Atualizar online", style="Secondary.TButton", command=lambda: self.send_raw("/who")).pack(fill="x")
        ttk.Button(sidebar, text="Historico", style="Secondary.TButton", command=lambda: self.send_raw("/history")).pack(fill="x", pady=(9, 0))
        ttk.Button(sidebar, text="Ajuda", style="Secondary.TButton", command=lambda: self.send_raw("/help")).pack(fill="x", pady=(9, 0))
        ttk.Button(sidebar, text="Sair", style="Secondary.TButton", command=self.disconnect).pack(fill="x", pady=(9, 0))

        main_panel = ttk.Frame(body, style="Panel.TFrame", padding=0)
        main_panel.grid(row=0, column=1, sticky="nsew")
        main_panel.columnconfigure(0, weight=1)
        main_panel.rowconfigure(0, weight=1)

        self.messages = tk.Text(
            main_panel,
            wrap="word",
            state="disabled",
            height=18,
            font=("Segoe UI", 10),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            insertbackground=self.colors["primary"],
            relief="flat",
            padx=18,
            pady=18,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["border"],
        )
        self.messages.grid(row=0, column=0, sticky="nsew")

        self.messages.tag_configure("system", foreground=self.colors["muted"], spacing1=4, spacing3=8)
        self.messages.tag_configure("mine", foreground=self.colors["success_fg"], background=self.colors["success_bg"], justify="right", lmargin1=190, lmargin2=190, rmargin=14, spacing1=6, spacing3=8)
        self.messages.tag_configure("other", foreground=self.colors["other_fg"], background=self.colors["other_bg"], lmargin1=14, lmargin2=14, rmargin=190, spacing1=6, spacing3=8)
        self.messages.tag_configure("private", foreground=self.colors["private_fg"], background=self.colors["private_bg"], lmargin1=52, lmargin2=52, rmargin=52, spacing1=6, spacing3=8)
        self.messages.tag_configure("history", foreground="#475569", background="#f8fafc", lmargin1=28, lmargin2=28, spacing1=4, spacing3=6)

        scroll = ttk.Scrollbar(main_panel, command=self.messages.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.messages.configure(yscrollcommand=scroll.set)

        footer = ttk.Frame(self.chat_frame, style="Footer.TFrame", padding=(0, 12, 0, 0))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        self.message_entry = ttk.Entry(footer, textvariable=self.message_var)
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.message_entry.bind("<Return>", lambda _event: self.send_message())
        ttk.Button(footer, text="Enviar", style="Primary.TButton", command=self.send_message).grid(row=0, column=1)

    def create_user_icon(self, parent: tk.Widget) -> tk.Canvas:
        icon = tk.Canvas(parent, width=24, height=24, bg="#f8fafc", highlightthickness=0)
        icon.create_oval(8, 3, 16, 11, fill=self.colors["primary"], outline=self.colors["primary"])
        icon.create_oval(5, 12, 19, 24, fill="#bfdbfe", outline="#bfdbfe")
        return icon

    def create_online_dot(self, parent: tk.Widget) -> tk.Canvas:
        dot = tk.Canvas(parent, width=14, height=14, bg="#f8fafc", highlightthickness=0)
        dot.create_oval(3, 3, 11, 11, fill="#22c55e", outline="#16a34a")
        return dot

    def update_online_users(self, raw_users: str) -> None:
        cleaned = raw_users.replace("Online:", "").strip()
        if cleaned in {"", "-", "nenhum"}:
            users: list[str] = []
        else:
            users = [user.strip() for user in cleaned.split(",") if user.strip()]

        self.online_users = users
        self.online_var.set(", ".join(users) if users else "-")

        if hasattr(self, "online_count_label"):
            self.online_count_label.configure(text=f"{len(users)} online")

        if not hasattr(self, "online_list_frame"):
            return

        for child in self.online_list_frame.winfo_children():
            child.destroy()

        if not users:
            tk.Label(
                self.online_list_frame,
                text="Sem utilizadores online",
                bg="#f8fafc",
                fg=self.colors["muted"],
                font=("Segoe UI", 9),
                anchor="w",
            ).pack(fill="x")
            return

        for user in users:
            row = tk.Frame(self.online_list_frame, bg="#f8fafc")
            row.pack(fill="x", pady=4)
            self.create_online_dot(row).pack(side="left", padx=(0, 8))
            label = f"{user} (tu)" if user == self.current_username else user
            tk.Label(
                row,
                text=label,
                bg="#f8fafc",
                fg=self.colors["text"],
                font=("Segoe UI", 10, "bold" if user == self.current_username else "normal"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

    def show_login(self) -> None:
        self.chat_frame.grid_forget()
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def show_chat(self) -> None:
        self.login_frame.grid_forget()
        self.chat_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.message_entry.focus_set()

    def clear_login(self) -> None:
        self.username_var.set("")
        self.password_var.set("")

    def set_status(self, text: str, state: str = "offline") -> None:
        self.status_var.set(text)
        if not hasattr(self, "status_chip"):
            return

        if state == "online":
            self.status_chip.configure(bg=self.colors["success_bg"], fg=self.colors["success_fg"])
        elif state == "connecting":
            self.status_chip.configure(bg=self.colors["warn_bg"], fg=self.colors["warn_fg"])
        else:
            self.status_chip.configure(bg=self.colors["offline_bg"], fg=self.colors["offline_fg"])

    def connect(self) -> None:
        if self.connected:
            return

        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Porta invalida", "A porta deve ser um numero.")
            return

        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showerror("Dados em falta", "Preenche username e password.")
            return

        self.set_status("A ligar...", "connecting")
        threading.Thread(
            target=self.connect_worker,
            args=(self.host_var.get().strip(), port, username, password),
            daemon=True,
        ).start()

    def connect_worker(self, host: str, port: int, username: str, password: str) -> None:
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.settimeout(None)
            reader = sock.makefile("r", encoding="utf-8", newline="\n")

            greeting = reader.readline().strip()
            username_prompt = reader.readline().strip()
            if not username_prompt.startswith("Username"):
                raise ConnectionError("protocolo inesperado")
            sock.sendall((username + "\n").encode("utf-8"))

            password_prompt = reader.readline().strip()
            if not password_prompt.startswith("Password"):
                raise ConnectionError("protocolo inesperado")
            sock.sendall((password + "\n").encode("utf-8"))

            status = reader.readline().strip()
            if status != "AUTH_OK":
                sock.close()
                self.root.after(0, lambda: self.login_failed("Login falhou. Verifica username/password."))
                return

            self.sock = sock
            self.reader = reader
            self.connected = True
            self.root.after(0, lambda: self.login_success(greeting, username))
            threading.Thread(target=self.receive_worker, daemon=True).start()
            self.send_raw("/who")
        except OSError as exc:
            self.root.after(0, lambda: self.login_failed(f"Nao foi possivel ligar ao servidor: {exc}"))

    def login_success(self, greeting: str, username: str) -> None:
        self.current_username = username
        self.set_status(f"Ligado como {username}", "online")
        self.show_chat()
        self.messages.configure(state="normal")
        self.messages.delete("1.0", "end")
        self.messages.configure(state="disabled")
        self.append_message(greeting, "system")

    def login_failed(self, message: str) -> None:
        self.set_status("Desligado", "offline")
        messagebox.showerror("Erro de ligacao", message)

    def receive_worker(self) -> None:
        assert self.reader is not None
        try:
            for line in self.reader:
                self.inbox.put(line.rstrip("\n"))
        except OSError:
            pass
        finally:
            self.inbox.put("__DISCONNECTED__")

    def process_inbox(self) -> None:
        while True:
            try:
                message = self.inbox.get_nowait()
            except queue.Empty:
                break

            if message == "__DISCONNECTED__":
                if self.connected:
                    self.connected = False
                    self.set_status("Desligado", "offline")
                    self.append_message("[sistema] Ligacao terminada.", "system")
                continue

            if message.startswith("Online:"):
                self.update_online_users(message.split(":", 1)[1].strip() or "-")
                continue

            self.append_message(message, self.tag_for_message(message))

        self.root.after(120, self.process_inbox)

    def tag_for_message(self, message: str) -> str:
        if message.startswith("[sistema]") or message.startswith("Online:") or message.startswith("Comandos:") or message.startswith("Uso:"):
            return "system"
        if message.startswith("[historico"):
            return "history"
        if message.startswith("[privado"):
            return "private"
        if self.current_username and message.startswith(f"[{self.current_username}]"):
            return "mine"
        return "other"

    def append_message(self, text: str, tag: str = "other") -> None:
        lines = text.splitlines() or [text]
        timestamp = datetime.now().strftime("%H:%M")

        self.messages.configure(state="normal")
        for line in lines:
            if not line:
                self.messages.insert("end", "\n")
                continue
            prefix = "" if tag == "system" else f"{timestamp}  "
            self.messages.insert("end", prefix + line + "\n", tag)
        self.messages.see("end")
        self.messages.configure(state="disabled")

    def send_raw(self, text: str) -> None:
        if not self.connected or self.sock is None:
            return
        try:
            self.sock.sendall((text + "\n").encode("utf-8"))
        except OSError:
            self.disconnect()

    def send_message(self) -> None:
        message = self.message_var.get().strip()
        if not message:
            return
        self.message_var.set("")
        self.send_raw(message)

    def disconnect(self) -> None:
        if self.sock is not None:
            try:
                self.sock.sendall(b"/quit\n")
            except OSError:
                pass
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.reader = None
        self.connected = False
        self.current_username = ""
        self.set_status("Desligado", "offline")
        self.update_online_users("-")
        self.show_login()

    def close(self) -> None:
        self.disconnect()
        self.root.destroy()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cliente grafico para o chat TCP.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9091)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    root = tk.Tk()
    ChatGui(root, args.host, args.port)
    root.mainloop()
