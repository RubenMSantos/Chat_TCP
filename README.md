# CHAT TCP com Autenticacao

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



## Tecnologias

- Python 3
- asyncio
- socket
- sqlite3
- Tkinter
- Raspberry Pi
- JSON Lines
- HTML/CSS

