"""Autonomer KI-Agent auf Basis von Claude.

Beispiel:
    python -m agent "Recherchiere die 5 schönsten Rundfahrten im Schwarzwald und schreibe einen Bericht nach bericht.md"
"""

from __future__ import annotations

import argparse
import sys

import anthropic

from . import android_tools, tools

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


def _print_progress(message) -> None:
    for block in message.content:
        if block.type == "text" and block.text.strip():
            print(f"\n🤖 {block.text.strip()}")
        elif block.type == "tool_use":
            args = ", ".join(f"{k}={str(v)[:60]!r}" for k, v in block.input.items())
            print(f"   🔧 {block.name}({args})")
        elif block.type == "server_tool_use":
            print(f"   🌐 {block.name}: {str(block.input)[:100]}")


def run(goal: str, max_steps: int, effort: str) -> int:
    client = anthropic.Anthropic()
    local_tools = list(tools.LOCAL_TOOLS)
    system = SYSTEM_PROMPT
    if android_tools.is_available():
        local_tools += android_tools.ANDROID_TOOLS
        system += "\n" + android_tools.ANDROID_PROMPT
        print("📱 Android-Werkzeuge aktiv.")
    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=16000,
        system=system,
        tools=[*local_tools, *tools.SERVER_TOOLS],
        thinking={"type": "adaptive"},
        output_config={"effort": effort},
        # Falls ein Sicherheitsfilter ablehnt, übernimmt automatisch ein passendes Ersatzmodell.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        max_iterations=max_steps,
        messages=[{"role": "user", "content": goal}],
    )

    last = None
    try:
        for message in runner:
            _print_progress(message)
            last = message
    except anthropic.AuthenticationError:
        print("❌ Kein gültiger API-Schlüssel. Setze ANTHROPIC_API_KEY.", file=sys.stderr)
        return 1
    except anthropic.RateLimitError:
        print("❌ Rate-Limit erreicht – bitte später erneut versuchen.", file=sys.stderr)
        return 1
    except anthropic.APIStatusError as err:
        print(f"❌ API-Fehler {err.status_code}: {err.message}", file=sys.stderr)
        return 1
    except anthropic.APIConnectionError:
        print("❌ Keine Verbindung zur Anthropic-API.", file=sys.stderr)
        return 1

    if last is None:
        return 1
    if last.stop_reason == "refusal":
        print("\n⛔ Die Anfrage wurde abgelehnt.", file=sys.stderr)
        return 2
    if last.stop_reason in ("tool_use", "pause_turn"):
        print(f"\n⏸️  Schrittlimit ({max_steps}) erreicht, bevor der Agent fertig war. Mit --max-steps erhöhen.")
        return 3
    if last.stop_reason == "max_tokens":
        print("\n⚠️  Antwort wurde wegen max_tokens abgeschnitten.")
    print(f"\n✅ Fertig. Ergebnisse liegen in: {tools.WORKSPACE}")
    return 0


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
