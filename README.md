# AsgardBackup
A simple but Thunderous Backup Solution

## Start des Servers

Nach Installation der Abhängigkeiten aus `requirements.txt` lässt sich der Server mit folgendem Befehl starten:

```bash
uvicorn server:app --reload
```

Die API steht danach auf Port 8000 zur Verfügung.
## Maintainer-Skript

Zur Installation und Aktualisierung gibt es `maintainer.sh`.
Die Initialinstallation erfolgt mit

```bash
sudo ./maintainer.sh install <repo-url>
```

Das Skript klont das Repository nach `/opt/asgardbackup`, richtet eine Python-`venv` ein,
installiert die Abhängigkeiten und startet den systemd-Service.

Fuer Updates genuegt

```bash
sudo ./maintainer.sh update
```

Dabei wird `git pull` ausgefuehrt, die Abhaengigkeiten werden aktualisiert und der Service neu gestartet.


## Admin-Webinterface

Die Verwaltung der API-Token erfolgt über ein kleines Webinterface unter `/admin`.
Nach der Installation muss zunächst ein Administrator über die Kommandozeile angelegt werden.
Da die Datenbank im Installationsverzeichnis liegt, sind hierfür Root-Rechte notwendig.
Nutze dabei explizit das Python der eingerichteten venv:

```bash
sudo ./venv/bin/python server.py create-admin <benutzername> <passwort>
```

Anschließend kann der Server gestartet werden (wie oben beschrieben oder mit `python server.py serve`).
Der Admin meldet sich über das Webformular unter `/admin/login` an (kein HTTP-Auth).

## Clients

Für Linux steht eine Kommandozeile zur Verfügung, für Windows eine kleine GUI.

- **CLI (Linux):**
  ```bash
  python client_cli.py login --server http://<server>:8000
  python client_cli.py upload <Datei>
  ```
  Nach dem ersten Login wird der erhaltene Token in `~/.asgard_client.json` gespeichert.

- **GUI (Windows):**
  ```bash
  python client_gui.py
  ```
  Dort können Serveradresse und API‑Token eingegeben sowie Dateien hochgeladen und wiederhergestellt werden.


## Feature-Checkliste

- ✅ API-Endpunkte (`/api/login`, `/api/upload`, `/api/check`, `/api/list`, `/api/restore`)
- ✅ Token-basierte Authentifizierung
- ✅ Benutzer werden automatisch angelegt
- ✅ Getrennte Backup-Verzeichnisse je Benutzer
- ✅ Admin-Webinterface (Token-Verwaltung)
- ✅ Versionierung (max. 4 Versionen)
- ✅ Deduplikation per Hash-Prüfung
- ✅ Blacklist-Backup
- ☑️ Wiederherstellung per Kommandozeile
- ☑️ Plattformübergreifend: Windows und Linux

### Versionierung und Deduplikation

Hochgeladene Dateien werden in einem Unterordner mit dem Dateinamen
gespeichert. Jede Version erhält einen Zeitstempel als Namen. Der Server
bewahrt maximal vier Versionen einer Datei auf und entfernt automatisch die
ältesten. Bevor eine neue Version angelegt wird, vergleicht der Server den
Hashwert aller vorhandenen Versionen und überspringt identische Dateien.

### Backup-Blacklist

Bestimmte Pfade oder Dateinamen können vom Backup ausgeschlossen werden. Die
Blacklist ist derzeit statisch im Code hinterlegt. Enthält der übertragene
Pfad einen dieser Einträge, lehnt der Server die Datei ab.

