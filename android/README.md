# KI-Agent auf dem Android-Tablet

Ein KI-Agent, der auf deinem Tablet selbstständig Dinge erledigt: Wecker stellen, Apps öffnen,
Benachrichtigungen lesen, im Web recherchieren, Berichte schreiben – auch automatisch im Hintergrund.

## Installation in 2 Schritten

**1. Termux installieren** (kostenlos, von F-Droid – *nicht* aus dem Play Store):
https://f-droid.org/packages/com.termux/

**2. Termux öffnen, diese Zeile einfügen und Enter drücken:**

```bash
curl -fsSL https://raw.githubusercontent.com/guntar1904-spec/Rundfahrten-/main/android/install.sh | bash
```

**Alternative ohne GitHub:** Die Datei `ki-agent-installer.sh` (enthält alles, erzeugt mit
`android/build-bundle.sh`) aufs Tablet in *Downloads* laden und in Termux eingeben:

```bash
termux-setup-storage && bash ~/storage/downloads/ki-agent-installer.sh
```

Das war's. Der Installer (ca. 1–3 Minuten) erledigt alles selbst und fragt dich nur nach:
- **Dateizugriff** → *Erlauben* tippen (damit Ergebnisse im Ordner **KI-Agent** landen)
- **API-Schlüssel** → von https://console.anthropic.com (*API Keys → Create Key*) kopieren und einfügen

Falls die App **Termux:API** noch fehlt, öffnet der Installer automatisch die Download-Seite –
dort einmal *Installieren* tippen.

## Benutzen

```bash
ki-agent "Stell mir einen Wecker für morgen 6:45"
ki-agent "Lies meine Benachrichtigungen und sag mir vor, was wichtig ist"
ki-agent "Schick mir jeden Morgen eine Benachrichtigung mit dem Wetter in Freiburg"
ki-agent                 # fragt nach deinem Auftrag
```

| Befehl | Wirkung |
|---|---|
| `ki-agent --yes "..."` | ohne Rückfragen bei Shell-Befehlen |
| `ki-agent --setup` | API-Schlüssel ändern |
| `ki-agent --update` | auf neueste Version aktualisieren |
| `ki-agent --uninstall` | entfernen (Ergebnisse bleiben erhalten) |

Symbol auf dem Homescreen: App **Termux:Widget** (F-Droid) installieren und das Widget „KI-Agent“ hinzufügen.

## Was der Agent auf dem Tablet erledigen kann

| Bereich | Beispiele |
|---|---|
| Apps | Apps finden und öffnen, Links/Karten/Mail öffnen, Text teilen |
| Uhr & Kalender | Wecker und Timer stellen, Kalendertermin vorbereiten (1 Tipp zum Bestätigen) |
| Benachrichtigungen | lesen und zusammenfassen, eigene senden |
| Sprache & Text | vorlesen, Zwischenablage lesen/schreiben |
| Gerät | Akku, WLAN, Lautstärke, Helligkeit, Standort, Foto |
| Im Hintergrund | Aufgaben planen („jeden Morgen …“), auflisten, löschen |
| Wissen & Dateien | Websuche, Webseiten lesen, Berichte schreiben, Gedächtnis |

## Berechtigungen (nur falls etwas nicht klappt)

Android fragt beim ersten Benutzen nach. Sonst unter *Einstellungen → Apps → Termux:API*:
**Benachrichtigungszugriff** (Benachrichtigungen lesen), **Standort**, **Kamera**,
**Systemeinstellungen ändern** (Helligkeit). Unter *Einstellungen → Apps → Termux*:
**Über anderen Apps einblenden** (Apps öffnen).

Geplante Hintergrundaufgaben laufen ohne Rückfragen. Android startet sie ungefähr im gewünschten
Abstand (mindestens 15 Minuten). Für zuverlässige Ausführung die Akku-Optimierung für Termux abschalten.
