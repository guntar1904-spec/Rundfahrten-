#!/usr/bin/env bash
# Baut dist/ki-agent-installer.sh: ein einzelnes Skript, das den Agenten komplett enthält
# (zum direkten Kopieren aufs Tablet, ohne Download von GitHub).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p dist
out=dist/ki-agent-installer.sh
{
  cat android/install.sh
  echo "__KI_AGENT_PAYLOAD__"
  tar --exclude='__pycache__' -czf - agent | base64
} > "$out"
chmod +x "$out"
echo "Erstellt: $out ($(wc -c < "$out") Bytes)"
