# CHAT TCP com Autenticacao

Projeto 10 da unidade curricular de Gestao e Planeamento de Redes.

Este projeto implementa um chat TCP multiutilizador com autenticacao, usando o Raspberry Pi como servidor e o PC como cliente. O objetivo e demonstrar comunicacao cliente-servidor, autenticacao com base de dados, multiplos clientes em simultaneo e registo de eventos em logs.

## Funcionalidades

- Servidor TCP em Python com `asyncio`.
- Cliente grafico em Tkinter.
- Cliente alternativo em linha de comandos.
- Autenticacao com SQLite.
- Passwords guardadas com salt e hash PBKDF2.
- Multiplos utilizadores online em simultaneo.
- Mensagens publicas.
- Mensagens privadas com `/msg`.
- Lista de utilizadores online.
- Historico de mensagens.
- Logs em JSON Lines.
- Relatorio HTML e CSV a partir dos logs.

## Arquitetura

```text
PC Cliente 1  ----\
                  ---> Raspberry Pi: server.py
PC Cliente 2  ----/

Raspberry Pi:
- Servidor TCP
- Base de dados SQLite
- Logs JSONL
- Relatorio HTML
```

## Estrutura do Projeto

```text
projeto10_chat_tcp_raiz/
  data/
    .gitkeep
  logs/
    .gitkeep
  reports/
    .gitkeep
  src/
    auth_db.py
    init_db.py
    server.py
    client.py
    gui_client.py
    report_logs.py
  DEMO_RASPBERRY_PI.md
  README.md
  RELATORIO_FINAL_PROJETO10.md
  requirements.txt
```

## Utilizadores de Teste

Os utilizadores sao criados automaticamente pelo script `init_db.py`.

```text
admin / admin123
alice / redes2026
bruno / segredo
```

## Teste Local no PC

Criar ou recriar a base de dados:

```bash
python src/init_db.py --reset
```

Abrir o servidor local:

```bash
python src/server.py --host 127.0.0.1 --port 9091
```

Abrir o cliente grafico:

```bash
python src/gui_client.py --host 127.0.0.1 --port 9091
```

Para simular dois utilizadores, abrir duas janelas do cliente grafico e autenticar com:

```text
alice / redes2026
bruno / segredo
```

## Demonstracao com Raspberry Pi

No Raspberry Pi:

```bash
cd /home/ciisp/projeto10_chat_tcp_raiz
python3 src/init_db.py --reset
python3 src/server.py --host 0.0.0.0 --port 9091
```

No PC:

```powershell
cd "C:\Users\ruben\Documents\Codex\2026-05-12\files-mentioned-by-the-user-mini\projeto10_chat_tcp_raiz"
python src/gui_client.py --host IP_DO_RASPBERRY --port 9091
```

O IP do Raspberry Pi pode ser obtido com:

```bash
hostname -I
```

## Comandos do Chat

```text
/who
/msg utilizador mensagem
/history
/help
/quit
```

Exemplo de mensagem privada:

```text
/msg bruno Esta mensagem e privada
```

## Logs

Os eventos do servidor sao registados em:

```text
logs/chat_events.jsonl
```

Eventos registados:

- `server_start`
- `login`
- `join`
- `message`
- `private_message`
- `leave`
- `timeout`

## Gerar Relatorio HTML

Depois de usar o chat:

```bash
python src/report_logs.py --log logs/chat_events.jsonl --output reports/chat_report.html
```

O relatorio fica em:

```text
reports/chat_report.html
```

## Preparar Demonstracao Limpa

Antes da demonstracao, no Raspberry Pi:

```bash
cd /home/ciisp/projeto10_chat_tcp_raiz
rm reports/*
rm logs/chat_events.jsonl
touch logs/chat_events.jsonl
python3 src/init_db.py --reset
```

Assim, o relatorio gerado no fim contem apenas os eventos realizados durante a demonstracao.

## Tecnologias

- Python 3
- asyncio
- socket
- sqlite3
- Tkinter
- Raspberry Pi
- JSON Lines
- HTML/CSS

