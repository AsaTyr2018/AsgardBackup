# Anweisungen fuer Codex-Agenten

Dieses Projekt heisst **AsgardBackup** und soll eine einfache, aber leistungsfähige Backup-Lösung werden. Die Hauptsprache des Repositories ist Deutsch.

## Ziele
- Vollautomatisches Benutzer-Datenbackup (Blacklist-basiert)
- Möglichst unkompliziertes Setup für Nutzer
- Versionierte Backups (später Kompression und Deduplikation möglich)
- Wiederherstellung über Webinterface oder CLI
- Server/Client-Architektur mit Multi-User-Unterstützung
- Clients für Windows und Linux, Server läuft auf Linux

## Client-Funktionalität
- Automatische Benutzererkennung (Windows: `USERNAME`, Linux: `USER`)
- Self-Registration beim ersten Kontakt zum Server
- Erster Durchlauf sichert alles (außer Blacklist); danach inkrementelles Backup
- Manuelle Sicherung/Wiederherstellung über GUI oder CLI
- Kommunikation über REST-API mit Token-Authentifizierung

## Server-Funktionalität
- Benutzer werden automatisch angelegt
- Getrennte Backup-Verzeichnisse je Benutzer
- Versionierung (standardmäßig max. 4 Versionen, konfigurierbar)
- Deduplikation per Hash-Prüfung
- Älteste Versionen werden gelöscht, sobald das Limit erreicht ist
- Speicher-Backend frei wählbar (lokal, NFS, Ceph, S3-kompatibel)

## API-Endpunkte (Beispiele)
- `POST /api/login` – Authentifizierung/Registrierung
- `POST /api/upload` – Backup-Upload
- `POST /api/check` – Hash-Vergleich vor Upload
- `GET /api/list` – Dateien auflisten
- `POST /api/restore` – Datei wiederherstellen

## Technologie-Vorschläge
- FastAPI + uvicorn als Server
- Token-basierte Authentifizierung (später JWT möglich)
- Python mit `os`, `hashlib` oder `blake3`; Metadaten z. B. in `sqlite`
- Optionale GUI mit PySimpleGUI oder Tkinter
- Kommunikation via HTTPS

## Features der ersten Version
- Backup anhand einer Blacklist
- Versionierte Ablage in Zeitstempel-Verzeichnissen
- Geänderte Dateien per Hash erkennen
- Wiederherstellung per Kommandozeile
- Plattformübergreifend: Windows und Linux

### Beispielhafte Projektstruktur
```
AsgardBackup/
├── asgardbackup.py
├── config.yaml
├── backup_engine.py
├── restore_engine.py
├── storage/
├── logs/
├── utils.py
└── README.md
```

### Beispiel-Konfiguration (Ausschnitt)
```
backup_root: "D:/AsgardBackup"
blacklist:
  - "C:/Windows"
  - "C:/Program Files"
  - "C:/Program Files (x86)"
  - "C:/ProgramData"
  - "C:/Users/%USERNAME%/AppData/Local"
  - "C:/$Recycle.Bin"
  - "C:/System Volume Information"
user_folders:
  - "C:/Users/%USERNAME%/Documents"
  - "C:/Users/%USERNAME%/Desktop"
  - "C:/Users/%USERNAME%/Pictures"
```

### Backup-Empfehlungen
- **Windows:** Systemordner und temporäre Daten ausschließen; Benutzerdaten wie `Documents`, `Pictures`, `Desktop` sichern.
- **Linux:** `/home`, `/etc`, `/opt`, `/srv`, `/root` sichern; `/proc`, `/sys`, `/dev`, `/tmp`, `/run`, `/var/run` u. a. ausschließen.
- Container-Daten wie `/var/lib/docker` nur sichern, falls erforderlich.

Weitere Ideen wie Kompression, Verschlüsselung oder Multi-Storage können später umgesetzt werden. Details stehen in `ideas.md`.
