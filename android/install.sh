#!/data/data/com.termux/files/usr/bin/bash
# Installer für den KI-Agenten auf Android (Termux).
#
# Benutzung in Termux:
#   pkg install -y git
#   git clone https://github.com/guntar1904-spec/Rundfahrten-.git
#   bash Rundfahrten-/android/install.sh
set -euo pipefail

APP_NAME="ki-agent"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
CONFIG_DIR="$HOME/.config/$APP_NAME"
ENV_FILE="$CONFIG_DIR/env"
BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m[x] %s\033[0m\n' "$*" >&2; exit 1; }

# --- 0. Umgebung prüfen ------------------------------------------------------
if [ -z "${TERMUX_VERSION:-}" ] && [ ! -d /data/data/com.termux ]; then
  die "Dieses Skript ist für Termux auf Android gedacht. Termux gibt es bei F-Droid: https://f-droid.org/packages/com.termux/"
fi
[ -f "$SRC_DIR/agent/main.py" ] || die "Agent-Quellcode nicht gefunden in $SRC_DIR. Bitte das Repository klonen und das Skript daraus starten."

# --- 1. Systempakete ---------------------------------------------------------
say "Pakete aktualisieren und Python installieren (kann ein paar Minuten dauern)"
pkg update -y
pkg install -y python git termux-api

# --- 2. Python-Abhängigkeiten ------------------------------------------------
say "Virtuelle Python-Umgebung anlegen"
mkdir -p "$INSTALL_DIR"
python -m venv "$INSTALL_DIR/venv"
PIP="$INSTALL_DIR/venv/bin/pip"
"$PIP" install --upgrade pip >/dev/null

say "Anthropic-SDK installieren"
if ! "$PIP" install --prefer-binary -r "$SRC_DIR/requirements.txt"; then
  # pydantic-core (Abhängigkeit des SDK) hat für Termux oft kein fertiges Paket
  # und muss dann mit Rust kompiliert werden. Das dauert einmalig 10–20 Minuten.
  warn "Fertiges Paket nicht verfügbar – kompiliere mit Rust (einmalig 10–20 Minuten, Handy am Strom lassen)."
  pkg install -y rust binutils
  export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk 2>/dev/null || echo 24)"
  "$PIP" install -r "$SRC_DIR/requirements.txt"
fi

# --- 3. Agent-Code kopieren --------------------------------------------------
say "Agent installieren nach $INSTALL_DIR"
rm -rf "$INSTALL_DIR/agent"
cp -r "$SRC_DIR/agent" "$INSTALL_DIR/agent"
find "$INSTALL_DIR/agent" -name '__pycache__' -type d -prune -exec rm -rf {} +

# --- 4. Speicherort für Ergebnisse -------------------------------------------
WORKSPACE="$HOME/ki-agent-workspace"
if [ -d "$HOME/storage/shared" ] || { say "Zugriff auf den Handyspeicher erlauben (Dialog bestätigen)"; termux-setup-storage 2>/dev/null && sleep 3 && [ -d "$HOME/storage/shared" ]; }; then
  WORKSPACE="$HOME/storage/shared/KI-Agent"
fi
mkdir -p "$WORKSPACE"

# --- 5. API-Schlüssel ---------------------------------------------------------
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"
if [ -f "$ENV_FILE" ] && grep -q '^ANTHROPIC_API_KEY=.' "$ENV_FILE"; then
  say "API-Schlüssel ist bereits gespeichert (ändern mit: ki-agent --setup)"
else
  say "Anthropic-API-Schlüssel eingeben (von https://console.anthropic.com – Eingabe bleibt unsichtbar)"
  read -r -s -p "API-Schlüssel: " KEY </dev/tty; echo
  [ -n "$KEY" ] || warn "Kein Schlüssel eingegeben – später mit 'ki-agent --setup' nachholen."
  umask 077
  printf 'ANTHROPIC_API_KEY=%s\n' "$KEY" > "$ENV_FILE"
fi
umask 077
grep -v '^AGENT_WORKSPACE=' "$ENV_FILE" > "$ENV_FILE.tmp" || true
printf 'AGENT_WORKSPACE=%s\n' "$WORKSPACE" >> "$ENV_FILE.tmp"
mv "$ENV_FILE.tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# --- 6. Startbefehl 'ki-agent' ----------------------------------------------
say "Befehl 'ki-agent' anlegen"
cat > "$BIN_DIR/ki-agent" <<LAUNCHER
#!/data/data/com.termux/files/usr/bin/bash
set -a; . "$ENV_FILE"; set +a
if [ "\${1:-}" = "--setup" ]; then
  read -r -s -p "Neuer API-Schlüssel: " KEY; echo
  { grep -v '^ANTHROPIC_API_KEY=' "$ENV_FILE"; printf 'ANTHROPIC_API_KEY=%s\n' "\$KEY"; } > "$ENV_FILE.tmp"
  mv "$ENV_FILE.tmp" "$ENV_FILE"; chmod 600 "$ENV_FILE"; echo "Gespeichert."; exit 0
fi
if [ "\${1:-}" = "--uninstall" ]; then
  for job in "$CONFIG_DIR"/jobs/*.sh; do [ -e "\$job" ] && termux-job-scheduler --cancel --job-id "\$(basename "\$job" .sh)" >/dev/null 2>&1; done
  rm -rf "$INSTALL_DIR" "$CONFIG_DIR" "$BIN_DIR/ki-agent" "\$HOME/.shortcuts/KI-Agent"
  echo "Deinstalliert. Ergebnisse in $WORKSPACE wurden behalten."; exit 0
fi
termux-wake-lock 2>/dev/null || true
cd "$INSTALL_DIR"
"$INSTALL_DIR/venv/bin/python" -m agent "\$@"
status=\$?
termux-wake-unlock 2>/dev/null || true
exit \$status
LAUNCHER
chmod 755 "$BIN_DIR/ki-agent"

# --- 7. Verknüpfung für den Homescreen (Termux:Widget) -----------------------
mkdir -p "$HOME/.shortcuts"
cat > "$HOME/.shortcuts/KI-Agent" <<'SHORTCUT'
#!/data/data/com.termux/files/usr/bin/bash
ki-agent
echo; read -r -p "Fertig – Enter zum Schließen."
SHORTCUT
chmod 755 "$HOME/.shortcuts/KI-Agent"

say "Fertig! 🎉"
cat <<DONE

  Starten:        ki-agent "Dein Ziel ..."
  Ohne Ziel:      ki-agent            (fragt nach dem Ziel)
  Voll autonom:   ki-agent --yes "..."
  Schlüssel neu:  ki-agent --setup
  Entfernen:      ki-agent --uninstall

  Ergebnisse:     $WORKSPACE
  WICHTIG:        App "Termux:API" von F-Droid installieren, damit der Agent das Tablet
                  bedienen kann (Apps öffnen, Wecker, Benachrichtigungen, ...).
                  Für "Apps öffnen": Einstellungen > Apps > Termux > "Über anderen Apps einblenden" erlauben.
  Homescreen:     App "Termux:Widget" (F-Droid) installieren und Widget "KI-Agent" hinzufügen.
DONE
