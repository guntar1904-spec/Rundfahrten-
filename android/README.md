# KI-Agent auf Android installieren

Der Agent läuft auf dem Handy in **Termux**, einer kostenlosen Linux-Terminal-App.

## 1. Termux installieren

Termux von **F-Droid** installieren: https://f-droid.org/packages/com.termux/
(Die Version im Google Play Store ist veraltet und funktioniert nicht zuverlässig.)

Damit der Agent das Tablet **selbst bedienen** kann, zusätzlich **Termux:API** von F-Droid
installieren: https://f-droid.org/packages/com.termux.api/

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

## Was der Agent auf dem Tablet selbstständig erledigen kann

| Bereich | Beispiele |
|---|---|
| Apps | installierte Apps auflisten und öffnen, Links/Karten/Mail öffnen, Text teilen |
| Uhr & Kalender | Wecker und Timer stellen, Kalendertermin vorbereiten (1 Tipp zum Bestätigen) |
| Benachrichtigungen | aktuelle Benachrichtigungen lesen, eigene senden |
| Sprache & Text | Text vorlesen, Zwischenablage lesen/schreiben |
| Gerät | Akku, WLAN, Lautstärke, Helligkeit, Standort, Foto aufnehmen |
| Selbstständig im Hintergrund | Aufgaben planen („jeden Morgen …“), auflisten, löschen |
| Wissen & Dateien | Websuche, Webseiten lesen, Dateien/Berichte schreiben, Gedächtnis |

Beispiele:

```bash
ki-agent "Stell mir einen Wecker für morgen 6:45 und einen 20-Minuten-Timer zum Tee"
ki-agent "Lies meine Benachrichtigungen und sag mir per Sprachausgabe, was wichtig ist"
ki-agent "Schick mir ab jetzt jeden Morgen eine Benachrichtigung mit dem Wetter in Freiburg"
ki-agent "Öffne YouTube"
```

### Berechtigungen

Android fragt beim ersten Benutzen nach. Falls etwas nicht klappt, unter
*Einstellungen → Apps → Termux:API* erlauben:
- **Benachrichtigungszugriff** – zum Lesen der Benachrichtigungen
- **Standort**, **Kamera** – für Standort und Fotos
- **Systemeinstellungen ändern** – für die Helligkeit

Und unter *Einstellungen → Apps → Termux*: **Über anderen Apps einblenden** – zum Öffnen von Apps.

Geplante Hintergrundaufgaben laufen ohne Rückfragen (`--yes`). Android führt sie ungefähr im
gewünschten Abstand aus (mindestens alle 15 Minuten), nicht auf die Minute genau. Für
zuverlässige Ausführung in den Akku-Einstellungen die Optimierung für Termux abschalten.

## Aktualisieren

```bash
cd Rundfahrten- && git pull && bash android/install.sh
```
