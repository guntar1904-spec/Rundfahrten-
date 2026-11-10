# Autonomer KI-Agent

Ein autonomer Agent auf Basis von Claude (Anthropic API, Python). Du gibst ihm ein Ziel –
er plant, recherchiert im Web, schreibt Dateien, führt Skripte aus, prüft seine Arbeit
und meldet sich erst, wenn er fertig ist.

## Android

Installation auf dem Tablet mit **einem Befehl** – siehe [android/README.md](android/README.md).
Dort bedient der Agent auch das Tablet selbst (Apps, Wecker, Benachrichtigungen, Hintergrundaufgaben).

## Installation (PC)

```bash
# Keine Zusatzpakete nötig – nur Python 3.10+
export ANTHROPIC_API_KEY="sk-ant-..."   # Schlüssel von https://console.anthropic.com
```

## Benutzung

```bash
python -m agent "Recherchiere die 5 schönsten Motorrad-Rundfahrten im Schwarzwald und schreibe einen Bericht nach bericht.md"
```

Ohne Argument fragt der Agent nach dem Ziel.

| Option | Bedeutung |
|---|---|
| `--max-steps N` | Maximale Anzahl Modell-Antworten (Standard 40) |
| `--effort low…max` | Denktiefe des Modells (Standard `high`) |
| `--yes` | Shell-Befehle ohne Rückfrage ausführen (voll autonom) |

Ergebnisse landen im Ordner `workspace/` (änderbar über die Umgebungsvariable `AGENT_WORKSPACE`).

## Werkzeuge des Agenten

| Tool | Zweck |
|---|---|
| `web_search`, `web_fetch` | Websuche und Webseiten lesen (laufen bei Anthropic) |
| `list_files`, `read_file`, `write_file` | Dateien im Workspace (kein Zugriff außerhalb) |
| `run_command` | Shell-Befehl im Workspace ausführen – fragt standardmäßig um Erlaubnis |
| `read_memory`, `save_memory` | Langzeitgedächtnis über mehrere Läufe (`workspace/MEMORY.md`) |
| `current_datetime` | Aktuelles Datum/Uhrzeit |

## Aufbau

- `agent/main.py` – Kommandozeile, Systemprompt, Agenten-Schleife
- `agent/claude.py` – schlanker Client für die Claude-API (nur Standardbibliothek)
- `agent/tooling.py` – `@tool`-Decorator: Schema aus Signatur + Docstring
- `agent/tools.py` – Datei-, Shell- und Gedächtnis-Werkzeuge
- `agent/android_tools.py` – Tablet-Werkzeuge (nur aktiv unter Termux mit Termux:API)

Bewusst ohne das `anthropic`-SDK: Dessen Abhängigkeiten müssten auf Android erst mit Rust
kompiliert werden (10–20 Minuten, oft fehlerhaft). So ist der Agent in 1–3 Minuten installiert.

Modell: `claude-opus-5-5` mit adaptivem Denken. Lehnt ein Sicherheitsfilter eine Anfrage ab,
springt automatisch ein Ersatzmodell ein (`fallbacks: "default"`).

## Eigene Werkzeuge hinzufügen

In `agent/tools.py` eine Funktion mit `@tool` dekorieren (Docstring = Beschreibung für
das Modell, `Args:` = Parameterbeschreibungen) und in `LOCAL_TOOLS` eintragen. Fertig.

## Sicherheit

Dateitools sind auf den Workspace beschränkt. `run_command` startet zwar im Workspace, kann
aber – wie jede Shell – darüber hinaus wirken. Nutze `--yes` daher nur in einer Umgebung,
in der das unbedenklich ist (z. B. Container/VM).
