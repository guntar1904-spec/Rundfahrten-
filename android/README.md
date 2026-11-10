# KI-Agent auf Android installieren

Der Agent läuft auf dem Handy in **Termux**, einer kostenlosen Linux-Terminal-App.

## 1. Termux installieren

Termux von **F-Droid** installieren: https://f-droid.org/packages/com.termux/
(Die Version im Google Play Store ist veraltet und funktioniert nicht zuverlässig.)

Optional für ein Homescreen-Symbol: **Termux:Widget** von F-Droid.

## 2. Installer starten

Termux öffnen und eingeben:

```bash
pkg install -y git
git clone https://github.com/guntar1904-spec/Rundfahrten-.git
bash Rundfahrten-/android/install.sh
```

Der Installer
1. installiert Python,
2. installiert das Anthropic-SDK (falls nötig wird einmalig mit Rust kompiliert – das dauert
   10–20 Minuten, Handy am Strom lassen),
3. fragt nach Speicherzugriff, damit die Ergebnisse im Handy-Ordner **KI-Agent** landen,
4. fragt nach deinem API-Schlüssel von https://console.anthropic.com (wird nur lokal mit
   Zugriffsrechten `600` gespeichert),
5. legt den Befehl `ki-agent` und eine Homescreen-Verknüpfung an.

## 3. Benutzen

```bash
ki-agent "Plane eine Tagesrundfahrt ab Freiburg mit 4 Aussichtspunkten und schreib sie nach tour.md"
ki-agent                 # fragt nach dem Ziel
ki-agent --yes "..."     # Shell-Befehle ohne Rückfrage
ki-agent --setup         # API-Schlüssel ändern
ki-agent --uninstall     # entfernen (Ergebnisse bleiben erhalten)
```

Während der Agent arbeitet, hält er das Handy per Wake-Lock wach.

## Aktualisieren

```bash
cd Rundfahrten- && git pull && bash android/install.sh
```
