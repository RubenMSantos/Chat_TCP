import argparse
import csv
import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "logs" / "chat_events.jsonl"
DEFAULT_OUTPUT = ROOT / "reports" / "chat_report.html"


def load_events(path: Path) -> list[dict]:
    events = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    if not events:
        raise SystemExit("O ficheiro de logs esta vazio.")
    return events


def minute_of(timestamp: str) -> str:
    return timestamp[:16].replace("T", " ")


def write_csv(path: Path, header: tuple[str, str], counter: Counter) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for label, value in counter.most_common():
            writer.writerow([label, value])


def rows(counter: Counter) -> str:
    if not counter:
        return "<tr><td colspan='2'>Sem dados</td></tr>"
    return "\n".join(
        f"<tr><td>{html.escape(str(label))}</td><td>{value}</td></tr>"
        for label, value in counter.most_common()
    )


def build_report(events: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    report_dir = output.parent

    by_event = Counter(event["event"] for event in events)
    by_user = Counter(event.get("username") or "-" for event in events if event.get("username"))
    by_ip = Counter(event.get("source_ip", "unknown") for event in events)
    by_minute = Counter(minute_of(event["timestamp"]) for event in events)
    messages_by_user = Counter(event.get("username") for event in events if event["event"] == "message")
    private_by_user = Counter(event.get("username") for event in events if event["event"] == "private_message")
    private_by_target = Counter(event.get("target") for event in events if event["event"] == "private_message")

    successful_logins = sum(1 for event in events if event["event"] == "login" and event.get("success"))
    failed_logins = sum(1 for event in events if event["event"] == "login" and not event.get("success"))

    write_csv(report_dir / "events_by_type.csv", ("event", "count"), by_event)
    write_csv(report_dir / "events_by_user.csv", ("username", "count"), by_user)
    write_csv(report_dir / "events_by_ip.csv", ("source_ip", "count"), by_ip)
    write_csv(report_dir / "events_by_minute.csv", ("minute", "count"), by_minute)
    write_csv(report_dir / "messages_by_user.csv", ("username", "messages"), messages_by_user)

    recent = "\n".join(
        "<tr>"
        f"<td>{html.escape(event.get('timestamp', ''))}</td>"
        f"<td>{html.escape(event.get('event', ''))}</td>"
        f"<td>{html.escape(str(event.get('username') or '-'))}</td>"
        f"<td>{html.escape(str(event.get('source_ip') or '-'))}</td>"
        "</tr>"
        for event in events[-15:][::-1]
    )

    document = f"""<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <title>Projeto 10 - Relatorio do Chat TCP</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f4f7fb; color: #172033; }}
    header {{ background: #111827; color: white; padding: 28px 36px; }}
    main {{ width: min(1100px, calc(100% - 32px)); margin: 24px auto 40px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 18px; }}
    .metric, section {{ background: white; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; }}
    .metric span {{ display: block; color: #667085; font-size: 13px; }}
    .metric strong {{ display: block; margin-top: 8px; font-size: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #d9e2ec; padding: 9px 8px; text-align: left; }}
    th {{ color: #667085; }}
  </style>
</head>
<body>
  <header>
    <h1>Projeto 10 - Chat TCP com Autenticacao</h1>
    <p>Relatorio gerado em {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
  </header>
  <main>
    <div class="metrics">
      <div class="metric"><span>Eventos</span><strong>{len(events)}</strong></div>
      <div class="metric"><span>Logins OK</span><strong>{successful_logins}</strong></div>
      <div class="metric"><span>Logins falhados</span><strong>{failed_logins}</strong></div>
      <div class="metric"><span>Mensagens</span><strong>{by_event.get('message', 0)}</strong></div>
      <div class="metric"><span>Utilizadores</span><strong>{len([u for u in by_user if u != '-'])}</strong></div>
    </div>
    <div class="grid">
      <section><h2>Eventos por tipo</h2><table><tr><th>Evento</th><th>Total</th></tr>{rows(by_event)}</table></section>
      <section><h2>Mensagens por utilizador</h2><table><tr><th>Utilizador</th><th>Mensagens</th></tr>{rows(messages_by_user)}</table></section>
      <section><h2>Mensagens privadas enviadas</h2><table><tr><th>Utilizador</th><th>Total</th></tr>{rows(private_by_user)}</table></section>
      <section><h2>Destinatarios privados</h2><table><tr><th>Utilizador</th><th>Total</th></tr>{rows(private_by_target)}</table></section>
      <section><h2>Eventos por IP</h2><table><tr><th>IP</th><th>Total</th></tr>{rows(by_ip)}</table></section>
      <section><h2>Eventos por minuto</h2><table><tr><th>Minuto</th><th>Total</th></tr>{rows(by_minute)}</table></section>
    </div>
    <section style="margin-top: 18px;">
      <h2>Eventos recentes</h2>
      <table><tr><th>Hora</th><th>Evento</th><th>Utilizador</th><th>IP</th></tr>{recent}</table>
    </section>
  </main>
</body>
</html>
"""
    output.write_text(document, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera relatorio HTML e CSV a partir dos logs do chat.")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_report(load_events(args.log), args.output)
    print(f"Relatorio gravado em {args.output}")
