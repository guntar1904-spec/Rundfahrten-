#!/data/data/com.termux/files/usr/bin/bash
# Ein-Befehl-Installer für den KI-Agenten auf Android (Termux).
#
# In Termux einfügen:
#   curl -fsSL https://raw.githubusercontent.com/guntar1904-spec/Rundfahrten-/main/android/install.sh | bash
#
# Andere Quelle/Branch:  KI_AGENT_BRANCH=<branch> bash install.sh
set -euo pipefail

REPO="guntar1904-spec/Rundfahrten-"
BRANCH="${KI_AGENT_BRANCH:-main}"
APP_NAME="ki-agent"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
CONFIG_DIR="$HOME/.config/$APP_NAME"
ENV_FILE="$CONFIG_DIR/env"
BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m[x] %s\033[0m\n' "$*" >&2; exit 1; }

if [ -z "${TERMUX_VERSION:-}" ] && [ ! -d /data/data/com.termux ]; then
  die "Dieses Skript ist für Termux auf Android gedacht. Termux gibt es bei F-Droid: https://f-droid.org/packages/com.termux/"
fi

# --- 1. Pakete (fertig kompiliert, kein Warten auf Kompilieren) ---------------
say "1/4  Python und Android-Schnittstelle installieren"
export DEBIAN_FRONTEND=noninteractive
APT_OPTS=(-o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confnew)
pkg update -y "${APT_OPTS[@]}" </dev/null || pkg update -y </dev/null
pkg install -y "${APT_OPTS[@]}" python termux-api curl </dev/null

# --- 2. Agent holen ---------------------------------------------------------
say "2/4  KI-Agent installieren"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../agent/main.py" ]; then
  cp -r "$SCRIPT_DIR/../agent" "$TMP/agent"            # aus geklontem Repository
else
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" -o "$TMP/src.tgz" \
    || die "Download fehlgeschlagen (Internet? Ist das Repository öffentlich und der Branch '$BRANCH' vorhanden?)"
  tar -xzf "$TMP/src.tgz" -C "$TMP"
  mv "$TMP"/*/agent "$TMP/agent" || die "Im Download wurde kein Agent gefunden."
fi
mkdir -p "$INSTALL_DIR"
rm -rf "$INSTALL_DIR/agent"
mv "$TMP/agent" "$INSTALL_DIR/agent"
find "$INSTALL_DIR/agent" -name '__pycache__' -type d -prune -exec rm -rf {} +

# --- 3. Einstellungen -------------------------------------------------------
say "3/4  Einrichten"
WORKSPACE="$HOME/ki-agent-workspace"
if [ ! -d "$HOME/storage/shared" ]; then
  echo "Bitte im nächsten Fenster den Zugriff auf Dateien erlauben (für den Ergebnisordner)."
  termux-setup-storage 2>/dev/null || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do [ -d "$HOME/storage/shared" ] && break; sleep 1; done
fi
[ -d "$HOME/storage/shared" ] && WORKSPACE="$HOME/storage/shared/KI-Agent"
mkdir -p "$WORKSPACE" "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"
umask 077
touch "$ENV_FILE"

if ! grep -q '^ANTHROPIC_API_KEY=.' "$ENV_FILE"; then
  echo
  echo "Jetzt brauchst du deinen API-Schlüssel von https://console.anthropic.com"
  echo "(dort: API Keys > Create Key). Einfügen mit langem Tippen > Einfügen."
  read -r -s -p "API-Schlüssel: " KEY </dev/tty || KEY=""; echo
  [ -n "$KEY" ] || warn "Kein Schlüssel eingegeben – später mit 'ki-agent --setup' nachholen."
  { grep -v '^ANTHROPIC_API_KEY=' "$ENV_FILE" || true; printf 'ANTHROPIC_API_KEY=%s\n' "$KEY"; } > "$ENV_FILE.tmp"
  mv "$ENV_FILE.tmp" "$ENV_FILE"
fi
{ grep -v '^AGENT_WORKSPACE=' "$ENV_FILE" || true; printf 'AGENT_WORKSPACE=%s\n' "$WORKSPACE"; } > "$ENV_FILE.tmp"
mv "$ENV_FILE.tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# --- 4. Befehl & Verknüpfung --------------------------------------------------
say "4/4  Befehl 'ki-agent' und Homescreen-Verknüpfung anlegen"
cat > "$BIN_DIR/ki-agent" <<LAUNCHER
#!/data/data/com.termux/files/usr/bin/bash
set -a; . "$ENV_FILE"; set +a
case "\${1:-}" in
  --setup)
    read -r -s -p "Neuer API-Schlüssel: " KEY; echo
    { grep -v '^ANTHROPIC_API_KEY=' "$ENV_FILE"; printf 'ANTHROPIC_API_KEY=%s\n' "\$KEY"; } > "$ENV_FILE.tmp"
    mv "$ENV_FILE.tmp" "$ENV_FILE"; chmod 600 "$ENV_FILE"; echo "Gespeichert."; exit 0 ;;
  --update)
    curl -fsSL "https://raw.githubusercontent.com/$REPO/$BRANCH/android/install.sh" | KI_AGENT_BRANCH="$BRANCH" bash; exit ;;
  --uninstall)
    for job in "$CONFIG_DIR"/jobs/*.sh; do [ -e "\$job" ] && termux-job-scheduler --cancel --job-id "\$(basename "\$job" .sh)" >/dev/null 2>&1; done
    rm -rf "$INSTALL_DIR" "$CONFIG_DIR" "$BIN_DIR/ki-agent" "\$HOME/.shortcuts/KI-Agent"
    echo "Deinstalliert. Ergebnisse in $WORKSPACE wurden behalten."; exit 0 ;;
esac
termux-wake-lock 2>/dev/null || true
cd "$INSTALL_DIR"
python -m agent "\$@"
status=\$?
termux-wake-unlock 2>/dev/null || true
exit \$status
LAUNCHER
chmod 755 "$BIN_DIR/ki-agent"

mkdir -p "$HOME/.shortcuts"
cat > "$HOME/.shortcuts/KI-Agent" <<'SHORTCUT'
#!/data/data/com.termux/files/usr/bin/bash
ki-agent
echo; read -r -p "Fertig – Enter zum Schließen."
SHORTCUT
chmod 755 "$HOME/.shortcuts/KI-Agent"

# --- Prüfen, ob die App Termux:API da ist -------------------------------------
API_OK=1
if ! timeout 8 termux-battery-status >/dev/null 2>&1; then
  API_OK=0
  warn "Die App 'Termux:API' fehlt noch – sie wird gebraucht, damit der Agent das Tablet bedienen kann."
  echo "    Ich öffne die Download-Seite. Dort 'Installieren' tippen."
  termux-open-url "https://f-droid.org/packages/com.termux.api/" 2>/dev/null || true
fi

say "Fertig! 🎉"
cat <<DONE

  So startest du den Agenten:
      ki-agent "Stell mir einen Wecker für 7 Uhr"
      ki-agent                      (fragt nach deinem Auftrag)

  Ergebnisse:   Ordner "KI-Agent" auf dem Tablet
  Mehr:         ki-agent --setup | --update | --uninstall
DONE
[ "$API_OK" = 1 ] || echo "  Nicht vergessen: App 'Termux:API' installieren (Seite wurde geöffnet)."
