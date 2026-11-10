"""Werkzeuge, mit denen der Agent das Android-Tablet selbst bedienen kann.

Benötigt Termux + die App "Termux:API" (F-Droid) + `pkg install termux-api`.
Die Werkzeuge werden nur geladen, wenn diese Befehle vorhanden sind.
"""

from __future__ import annotations

import datetime as _dt
import json
import shlex
import shutil
import subprocess
from pathlib import Path

from .tooling import tool

from . import tools as _base


def is_available() -> bool:
    return shutil.which("termux-notification") is not None


def _run(args: list[str], timeout: int = 30, stdin: str | None = None) -> str:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, input=stdin)
    except FileNotFoundError:
        raise RuntimeError(f"Befehl '{args[0]}' fehlt. Ist 'pkg install termux-api' installiert?")
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"'{args[0]}' hat nicht geantwortet. Ist die App Termux:API installiert und hat sie die nötige Berechtigung?"
        )
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        raise RuntimeError(out or f"'{args[0]}' ist mit Code {proc.returncode} fehlgeschlagen.")
    return _base._truncate(out) or "OK"


def _start_activity(*am_args: str) -> str:
    return _run(["am", "start", "--user", "0", *am_args])


# --- Apps & Links -------------------------------------------------------------

@tool
def list_installed_apps(filter_text: str = "") -> str:
    """List package names of user-installed apps on the tablet.

    Args:
        filter_text: Optional case-insensitive text to filter package names, e.g. "whatsapp".
    """
    out = _run(["pm", "list", "packages", "-3"])
    pkgs = sorted(line.removeprefix("package:") for line in out.splitlines() if line.startswith("package:"))
    if filter_text:
        pkgs = [p for p in pkgs if filter_text.lower() in p.lower()]
    return "\n".join(pkgs) or "Keine passenden Apps gefunden."


@tool
def open_app(package_name: str) -> str:
    """Open (launch) an installed app on the tablet by its package name.

    Use list_installed_apps first if you do not know the package name.

    Args:
        package_name: Android package name, e.g. "com.google.android.youtube".
    """
    activity = _run(["cmd", "package", "resolve-activity", "--brief", package_name]).splitlines()[-1].strip()
    if "/" not in activity:
        raise RuntimeError(f"Keine startbare Activity für '{package_name}' gefunden.")
    _start_activity("-n", activity)
    return f"App {package_name} geöffnet."


@tool
def open_url(url: str) -> str:
    """Open a web link, map link (geo:), mail link (mailto:) or other URI on the tablet with the default app.

    Args:
        url: The URL or URI to open, e.g. "https://maps.google.com/?q=Freiburg".
    """
    return _run(["termux-open-url", url])


@tool
def share_text(text: str, title: str = "Teilen") -> str:
    """Open the Android share dialog with a text, so the user can send it via any app.

    Args:
        text: Text to share.
        title: Title of the share dialog.
    """
    return _run(["termux-share", "-a", "send", "-t", title], stdin=text)


# --- Wecker, Timer, Kalender ----------------------------------------------------

@tool
def set_alarm(hour: int, minute: int, label: str = "") -> str:
    """Set an alarm in the tablet's clock app.

    Args:
        hour: Hour 0-23.
        minute: Minute 0-59.
        label: Optional alarm label.
    """
    _start_activity(
        "-a", "android.intent.action.SET_ALARM",
        "--ei", "android.intent.extra.alarm.HOUR", str(hour),
        "--ei", "android.intent.extra.alarm.MINUTES", str(minute),
        "--es", "android.intent.extra.alarm.MESSAGE", label,
        "--ez", "android.intent.extra.alarm.SKIP_UI", "true",
    )
    return f"Wecker für {hour:02d}:{minute:02d} gestellt."


@tool
def set_timer(seconds: int, label: str = "") -> str:
    """Start a countdown timer in the tablet's clock app.

    Args:
        seconds: Timer length in seconds.
        label: Optional label.
    """
    _start_activity(
        "-a", "android.intent.action.SET_TIMER",
        "--ei", "android.intent.extra.alarm.LENGTH", str(seconds),
        "--es", "android.intent.extra.alarm.MESSAGE", label,
        "--ez", "android.intent.extra.alarm.SKIP_UI", "true",
    )
    return f"Timer über {seconds} Sekunden gestartet."


@tool
def add_calendar_event(title: str, start_iso: str, end_iso: str, location: str = "", description: str = "") -> str:
    """Open the calendar app with a pre-filled new event; the user confirms it with one tap.

    Args:
        title: Event title.
        start_iso: Start as ISO 8601 local time, e.g. "2026-11-12T14:00".
        end_iso: End as ISO 8601 local time.
        location: Optional location.
        description: Optional description.
    """
    start_ms = int(_dt.datetime.fromisoformat(start_iso).timestamp() * 1000)
    end_ms = int(_dt.datetime.fromisoformat(end_iso).timestamp() * 1000)
    _start_activity(
        "-a", "android.intent.action.INSERT",
        "-d", "content://com.android.calendar/events",
        "--es", "title", title,
        "--es", "eventLocation", location,
        "--es", "description", description,
        "--el", "beginTime", str(start_ms),
        "--el", "endTime", str(end_ms),
    )
    return "Kalender geöffnet – der Termin muss auf dem Tablet noch mit 'Speichern' bestätigt werden."


# --- Benachrichtigungen, Sprache, Zwischenablage --------------------------------

@tool
def send_notification(title: str, content: str) -> str:
    """Show a notification on the tablet (e.g. to report results or remind the user).

    Args:
        title: Notification title.
        content: Notification text.
    """
    return _run(["termux-notification", "--title", title, "--content", content])


@tool
def read_notifications() -> str:
    """Read the notifications currently shown on the tablet (app, title, text).

    Requires notification access for Termux:API in Android settings.
    """
    raw = _run(["termux-notification-list"])
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    lines = [f"[{n.get('packageName','?')}] {n.get('title','')}: {n.get('content','')}" for n in items]
    return _base._truncate("\n".join(lines)) or "Keine Benachrichtigungen."


@tool
def speak(text: str) -> str:
    """Read a text aloud on the tablet using text-to-speech.

    Args:
        text: Text to speak.
    """
    return _run(["termux-tts-speak", text], timeout=300)


@tool
def get_clipboard() -> str:
    """Return the current text in the tablet's clipboard."""
    return _run(["termux-clipboard-get"])


@tool
def set_clipboard(text: str) -> str:
    """Copy a text into the tablet's clipboard.

    Args:
        text: Text to copy.
    """
    _run(["termux-clipboard-set"], stdin=text)
    return "In die Zwischenablage kopiert."


# --- Geräteinfos & Hardware ------------------------------------------------------

@tool
def device_status() -> str:
    """Return battery status, Wi-Fi connection info and volume levels of the tablet."""
    parts = []
    for name, cmd in (
        ("Akku", ["termux-battery-status"]),
        ("WLAN", ["termux-wifi-connectioninfo"]),
        ("Lautstärke", ["termux-volume"]),
    ):
        try:
            parts.append(f"## {name}\n{_run(cmd)}")
        except RuntimeError as err:
            parts.append(f"## {name}\nnicht verfügbar: {err}")
    return "\n\n".join(parts)


@tool
def get_location() -> str:
    """Return the tablet's current location (latitude/longitude). Requires location permission for Termux:API."""
    return _run(["termux-location", "-p", "network", "-r", "once"], timeout=60)


@tool
def set_volume(stream: str, level: int) -> str:
    """Set the tablet's volume.

    Args:
        stream: One of "music", "ring", "notification", "alarm", "system", "call".
        level: Volume level (0-15 on most devices; use device_status to see the maximum).
    """
    return _run(["termux-volume", stream, str(level)])


@tool
def set_brightness(level: int) -> str:
    """Set the screen brightness.

    Args:
        level: Brightness 0-255.
    """
    return _run(["termux-brightness", str(max(0, min(level, 255)))])


@tool
def take_photo(filename: str = "", camera: int = 0) -> str:
    """Take a photo with the tablet camera and save it into the agent workspace.

    Args:
        filename: Optional file name (JPEG) relative to the workspace. Default: timestamped name.
        camera: Camera id: 0 = back camera, 1 = front camera.
    """
    name = filename or f"foto-{_dt.datetime.now():%Y%m%d-%H%M%S}.jpg"
    target = _base._safe_path(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    _run(["termux-camera-photo", "-c", str(camera), str(target)], timeout=60)
    return f"Foto gespeichert: {target.relative_to(_base.WORKSPACE)}"


# --- Zeitgesteuerte Aufgaben ----------------------------------------------------

JOBS_DIR = Path.home() / ".config" / "ki-agent" / "jobs"


@tool
def schedule_task(goal: str, every_minutes: int = 0, job_id: int = 0) -> str:
    """Schedule the agent to work on a goal by itself later, in the background (e.g. a daily summary).

    Android runs the job roughly at the interval (minimum 15 minutes); exact times are not guaranteed.
    The scheduled run executes commands without asking.

    Args:
        goal: What the agent should do on each run, written as a complete instruction.
        every_minutes: Repeat interval in minutes (minimum 15). 0 = run once, as soon as possible.
        job_id: Optional numeric id; reuse an existing id to replace that job. 0 = pick a new id.
    """
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    if not job_id:
        existing = [int(p.stem) for p in JOBS_DIR.glob("*.sh") if p.stem.isdigit()]
        job_id = max(existing, default=100) + 1
    script = JOBS_DIR / f"{job_id}.sh"
    script.write_text(
        "#!/data/data/com.termux/files/usr/bin/bash\n"
        f"# Ziel: {' '.join(goal.split())}\n"
        f"{shlex.quote(shutil.which('ki-agent') or 'ki-agent')} --yes {shlex.quote(goal)} >> {shlex.quote(str(JOBS_DIR / f'{job_id}.log'))} 2>&1\n",
        encoding="utf-8",
    )
    script.chmod(0o700)
    args = ["termux-job-scheduler", "--job-id", str(job_id), "--script", str(script), "--persisted", "true",
            "--network", "any"]
    if every_minutes:
        args += ["--period-ms", str(max(every_minutes, 15) * 60_000)]
    _run(args)
    when = f"alle {max(every_minutes, 15)} Minuten" if every_minutes else "einmalig"
    return f"Aufgabe #{job_id} geplant ({when}). Protokoll: {JOBS_DIR / f'{job_id}.log'}"


@tool
def list_scheduled_tasks() -> str:
    """List the agent's scheduled background tasks with their goals."""
    lines = []
    for script in sorted(JOBS_DIR.glob("*.sh")):
        goal = next((l[8:] for l in script.read_text(encoding="utf-8").splitlines() if l.startswith("# Ziel: ")), "?")
        lines.append(f"#{script.stem}: {goal}")
    return "\n".join(lines) or "Keine geplanten Aufgaben."


@tool
def cancel_scheduled_task(job_id: int) -> str:
    """Cancel a scheduled background task.

    Args:
        job_id: The id shown by list_scheduled_tasks.
    """
    _run(["termux-job-scheduler", "--cancel", "--job-id", str(job_id)])
    (JOBS_DIR / f"{job_id}.sh").unlink(missing_ok=True)
    return f"Aufgabe #{job_id} gelöscht."


ANDROID_TOOLS = [
    list_installed_apps, open_app, open_url, share_text,
    set_alarm, set_timer, add_calendar_event,
    send_notification, read_notifications, speak, get_clipboard, set_clipboard,
    device_status, get_location, set_volume, set_brightness, take_photo,
    schedule_task, list_scheduled_tasks, cancel_scheduled_task,
]

ANDROID_PROMPT = """
Du läufst direkt auf dem Android-Tablet des Benutzers (Termux) und kannst es mit den Android-Werkzeugen bedienen:
Apps öffnen, Links/Karten öffnen, Wecker/Timer stellen, Kalendertermine vorbereiten, Benachrichtigungen lesen und senden,
vorlesen, Zwischenablage, Lautstärke/Helligkeit, Fotos, Standort und zeitgesteuerte Hintergrundaufgaben (schedule_task).
- Erledige Aufgaben auf dem Tablet direkt mit diesen Werkzeugen, statt dem Benutzer Anleitungen zu geben.
- Wenn ein Werkzeug wegen fehlender Berechtigung scheitert, sag dem Benutzer genau, welche Berechtigung er in den
  Android-Einstellungen für "Termux:API" erteilen muss.
- Bei wiederkehrenden Wünschen ("jeden Morgen", "alle 2 Stunden") nutze schedule_task.
- Wenn du im Hintergrund läufst, melde Ergebnisse per send_notification."""
