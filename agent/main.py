"""Autonomer KI-Agent auf Basis von Claude.

Beispiel:
    python -m agent "Recherchiere die 5 schönsten Rundfahrten im Schwarzwald und schreibe einen Bericht nach bericht.md"
"""

from __future__ import annotations

import argparse
import sys

from . import android_tools, claude, tools
from .tooling import Tool

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """Du bist ein autonomer Agent. Du bekommst ein Ziel und arbeitest es selbstständig bis zum Ende ab.

Arbeitsweise:
- Lies zu Beginn dein Langzeitgedächtnis (read_memory), falls frühere Läufe relevant sein könnten.
- Plane kurz, dann handle: nutze die Werkzeuge, statt nur zu beschreiben, was man tun könnte.
- Für aktuelle Informationen nutze web_search und web_fetch. Gib bei Fakten aus dem Web die Quelle an.
- Ergebnisse, die bleiben sollen, schreibst du mit write_file in das Arbeitsverzeichnis.
- Prüfe deine Arbeit (z. B. Dateien erneut lesen, Skripte ausführen), bevor du fertig meldest.
- Wenn ein Befehl abgelehnt wird oder fehlschlägt, such einen anderen Weg, statt aufzugeben.
- Speichere am Ende wichtige, dauerhafte Erkenntnisse mit save_memory.
- Frage nur nach, wenn das Ziel ohne Klärung wirklich nicht erreichbar ist.

Zum Abschluss: eine kurze Zusammenfassung auf Deutsch, was erledigt wurde, wo die Ergebnisse liegen und was offen ist."""


def _print_progress(content: list[dict]) -> None:
    for block in content:
        kind = block.get("type")
        if kind == "text" and block.get("text", "").strip():
            print(f"\n🤖 {block['text'].strip()}")
        elif kind == "tool_use":
            args = ", ".join(f"{k}={str(v)[:60]!r}" for k, v in block.get("input", {}).items())
            print(f"   🔧 {block['name']}({args})")
        elif kind == "server_tool_use":
            print(f"   🌐 {block['name']}: {str(block.get('input'))[:100]}")


def _run_tools(content: list[dict], registry: dict[str, Tool]) -> list[dict]:
    """Führt alle tool_use-Blöcke aus und liefert die tool_result-Blöcke (alle in einer Nachricht)."""
    results = []
    for block in content:
        if block.get("type") != "tool_use":
            continue
        result: dict = {"type": "tool_result", "tool_use_id": block["id"]}
        tool_obj = registry.get(block["name"])
        try:
            if tool_obj is None:
                raise ValueError(f"Unbekanntes Werkzeug: {block['name']}")
            result["content"] = tool_obj.call(block.get("input") or {})
        except Exception as exc:  # Fehler an das Modell zurückgeben, nicht abbrechen
            result["content"] = f"Fehler: {exc}"
            result["is_error"] = True
        results.append(result)
    return results


def run(goal: str, max_steps: int, effort: str) -> int:
    local_tools = list(tools.LOCAL_TOOLS)
    system = SYSTEM_PROMPT
    if android_tools.is_available():
        local_tools += android_tools.ANDROID_TOOLS
        system += "\n" + android_tools.ANDROID_PROMPT
        print("📱 Android-Werkzeuge aktiv.")
    registry = {t.name: t for t in local_tools}

    messages: list[dict] = [{"role": "user", "content": goal}]
    body = {
        "model": MODEL,
        "max_tokens": 16000,
        "system": system,
        "tools": [*(t.to_dict() for t in local_tools), *tools.SERVER_TOOLS],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": effort},
        # Falls ein Sicherheitsfilter ablehnt, übernimmt automatisch ein passendes Ersatzmodell.
        "fallbacks": "default",
        "messages": messages,
    }

    for _ in range(max_steps):
        try:
            response = claude.create_message(body, betas=["server-side-fallback-2026-07-01"])
        except claude.APIError as err:
            hints = {401: "Ungültiger API-Schlüssel (ändern mit: ki-agent --setup).", 429: "Rate-Limit erreicht."}
            print(f"❌ {hints.get(err.status, err)}", file=sys.stderr)
            return 1

        content = response.get("content", [])
        _print_progress(content)
        messages.append({"role": "assistant", "content": content})
        stop = response.get("stop_reason")

        if stop == "tool_use":
            messages.append({"role": "user", "content": _run_tools(content, registry)})
            continue
        if stop == "pause_turn":  # Server-Tool (z. B. Websuche) braucht noch einen Durchgang
            continue
        if stop == "refusal":
            print("\n⛔ Die Anfrage wurde abgelehnt.", file=sys.stderr)
            return 2
        if stop == "max_tokens":
            print("\n⚠️  Antwort wurde wegen max_tokens abgeschnitten.")
        print(f"\n✅ Fertig. Ergebnisse liegen in: {tools.WORKSPACE}")
        return 0

    print(f"\n⏸️  Schrittlimit ({max_steps}) erreicht, bevor der Agent fertig war. Mit --max-steps erhöhen.")
    return 3


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomer KI-Agent (Claude)")
    parser.add_argument("goal", nargs="*", help="Das Ziel / die Aufgabe für den Agenten")
    parser.add_argument("--max-steps", type=int, default=40, help="Maximale Anzahl Modell-Antworten (Standard: 40)")
    parser.add_argument(
        "--effort",
        choices=["low", "medium", "high", "xhigh", "max"],
        default="high",
        help="Denktiefe des Modells (Standard: high)",
    )
    parser.add_argument("--yes", action="store_true", help="Shell-Befehle ohne Rückfrage ausführen (voll autonom)")
    args = parser.parse_args()

    goal = " ".join(args.goal).strip() or input("Welches Ziel soll der Agent verfolgen?\n> ").strip()
    if not goal:
        parser.error("Kein Ziel angegeben.")

    tools.AUTO_APPROVE_COMMANDS = args.yes
    sys.exit(run(goal, args.max_steps, args.effort))


if __name__ == "__main__":
    main()
