"""Werkzeuge (Tools), die der autonome Agent benutzen darf.

Alle Dateioperationen sind auf das Arbeitsverzeichnis (WORKSPACE) beschränkt,
damit der Agent nichts außerhalb davon verändern kann.
"""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
from pathlib import Path

from .tooling import tool

WORKSPACE = Path(os.environ.get("AGENT_WORKSPACE", "workspace")).resolve()
MEMORY_FILE = WORKSPACE / "MEMORY.md"
MAX_OUTPUT_CHARS = 20_000

# Wird von main.py gesetzt: Darf der Agent Shell-Befehle ohne Rückfrage ausführen?
AUTO_APPROVE_COMMANDS = False


def _safe_path(relative_path: str) -> Path:
    """Löst einen Pfad relativ zum Workspace auf und verhindert Ausbrüche (../)."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    path = (WORKSPACE / relative_path).resolve()
    if path != WORKSPACE and WORKSPACE not in path.parents:
        raise ValueError(f"Pfad '{relative_path}' liegt außerhalb des Arbeitsverzeichnisses.")
    return path


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n... [gekürzt, {len(text) - MAX_OUTPUT_CHARS} Zeichen ausgelassen]"


@tool
def list_files(directory: str = ".") -> str:
    """List files and folders inside the agent workspace.

    Args:
        directory: Folder relative to the workspace root, e.g. "." or "reports".
    """
    path = _safe_path(directory)
    if not path.exists():
        return f"Ordner '{directory}' existiert nicht."
    entries = sorted(path.rglob("*"))
    lines = [
        f"{p.relative_to(WORKSPACE)}{'/' if p.is_dir() else f'  ({p.stat().st_size} B)'}"
        for p in entries[:500]
    ]
    return "\n".join(lines) or "(leer)"


@tool
def read_file(path: str) -> str:
    """Read a UTF-8 text file from the agent workspace.

    Args:
        path: File path relative to the workspace root.
    """
    return _truncate(_safe_path(path).read_text(encoding="utf-8"))


@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a text file in the agent workspace. Parent folders are created automatically.

    Args:
        path: File path relative to the workspace root.
        content: The complete new file content.
    """
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"{len(content)} Zeichen nach '{path}' geschrieben."


@tool
def run_command(command: str, timeout_seconds: int = 60) -> str:
    """Run a shell command inside the agent workspace and return stdout, stderr and exit code.

    Use it to run scripts you wrote, inspect data or install nothing system-wide.
    The human operator may decline the command.

    Args:
        command: The shell command to run, e.g. "python3 analyse.py".
        timeout_seconds: Maximum runtime in seconds (1-600).
    """
    if not AUTO_APPROVE_COMMANDS:
        answer = input(f"\n⚠️  Agent möchte ausführen:\n    $ {command}\n   Erlauben? [j/N] ").strip().lower()
        if answer not in ("j", "ja", "y", "yes"):
            return "Der Benutzer hat die Ausführung dieses Befehls abgelehnt. Wähle einen anderen Weg."
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=max(1, min(timeout_seconds, 600)),
        )
    except subprocess.TimeoutExpired:
        return f"Zeitüberschreitung nach {timeout_seconds} s."
    return _truncate(f"exit_code: {proc.returncode}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")


@tool
def read_memory() -> str:
    """Read the agent's long-term memory (notes kept across runs)."""
    if not MEMORY_FILE.exists():
        return "(Noch keine Erinnerungen gespeichert.)"
    return _truncate(MEMORY_FILE.read_text(encoding="utf-8"))


@tool
def save_memory(note: str) -> str:
    """Append a short note to the agent's long-term memory so future runs can use it.

    Save durable facts only: user preferences, results, open to-dos. Not step-by-step logs.

    Args:
        note: The note to remember (one or a few sentences).
    """
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    with MEMORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"- [{stamp}] {note.strip()}\n")
    return "Gespeichert."


@tool
def current_datetime() -> str:
    """Return the current local date and time (ISO 8601)."""
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


# Server-Tools: laufen bei Anthropic, keine eigene Implementierung nötig.
SERVER_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 10},
    {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 10},
]

LOCAL_TOOLS = [
    list_files,
    read_file,
    write_file,
    run_command,
    read_memory,
    save_memory,
    current_datetime,
]
