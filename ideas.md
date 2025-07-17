### **Projektname:**

**AsgardBackup**

### **Motto:**
**„A simple but Thunderous Backup Solution.“**

Main Landuage: German

---

## **Grundidee:**

* **Vollautomatisches User-Daten-Backup mit Blacklist**
* **Kein kompliziertes Setup für die User**
* **Versionsbasiertes Dateibackup** (optional Kompression & Dedupe später)
* **Restore per Webinterface oder CLI möglich**
* **Server / Client Komponenten**
* **Multi User Enviroment**
* **Client Support für Windows und Linux**
* **Server auf Linux**
* **Backup und Restore vom Client aus**

---

### **Client-Funktionalität:**

| Funktion                                | Beschreibung                                                                   |
| --------------------------------------- | ------------------------------------------------------------------------------ |
| **User-Detection**                      | Erkennt automatisch den angemeldeten User (Windows: `USERNAME`, Linux: `USER`) |
| **Server-Login per API**                | Erstverbindung meldet User automatisch am Server an                            |
| **Self-Registration**                   | Kein manuelles Anlegen von Usern nötig                                         |
| **Full-Backup bei Erstlauf**            | Beim ersten Run wird der komplette erlaubte Datenbereich gesichert             |
| **Inkrementelles Backup danach**        | Nur geänderte Dateien werden gesichert                                         |
| **Manuelles Backup/Restore per Client** | GUI oder CLI: Benutzer können selbst sichern und wiederherstellen              |
| **Kommunikation**                       | REST-API mit Token-Auth, optional JWT oder OAuth später                        |

---

### **Server-Funktionalität:**

| Funktion                       | Beschreibung                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------- |
| **User-Management**            | User werden automatisch angelegt bei API-Login                                |
| **Backup-Verwaltung per User** | Separater Speicherbereich je User (`/backups/<user>/…`)                       |
| **Versionierung**              | Pro Datei max. 4 Versionen (konfigurierbar, z. B. über `config.yaml`)         |
| **Deduplikation**              | Erkennung gleicher Dateien per Hash (z. B. SHA256 oder `blake3`)              |
| **Speicherbereinigung**        | Älteste Versionen werden gelöscht, wenn das Limit erreicht ist                |
| **Storage-Backend flexibel**   | Lokaler Speicher, NFS, Ceph, S3-kompatibel – je nachdem wie fancy du’s willst |
| **Admin-Webinterface**         | Verwaltung der API-Token über ein Login-geschütztes Webinterface |

---

## **API-Kommunikation:**

| Aktion                             | API Endpoint   | Methode                                                               |
| ---------------------------------- | -------------- | --------------------------------------------------------------------- |
| **Login & Registrierung**          | `/api/login`   | `POST`                                                                |
| **Backup Upload**                  | `/api/upload`  | `POST` (Multipart-File-Upload)                                        |
| **Backup Prüfen (Hash-Vergleich)** | `/api/check`   | `POST` (Hash wird übertragen, Server prüft, ob Datei schon vorhanden) |
| **Dateien listen (Versionen)**     | `/api/list`    | `GET`                                                                 |
| **Restore anfordern**              | `/api/restore` | `POST` (gibt Datei zurück)                                            |

---

## **Ablauf des Backups:**

1. **Client-Start**
   → Erkennt User
2. **Anmeldung am Server**
   → User wird registriert oder geauthentifiziert
3. **Erstes Full-Backup**
   → Alles wird hochgeladen, was nicht in der Blacklist steht
4. **Nachfolgende Backups:**
   → Nur geänderte Dateien (per Hash-Prüfung)
5. **Server verwaltet Versionen & Dedupe**
   → Bei mehr als 4 Versionen: Älteste wird entfernt

---

## **Technologie-Vorschlag:**

| Bereich              | Technik                                                                |
| -------------------- | ---------------------------------------------------------------------- |
| **API-Server**       | `FastAPI` + `uvicorn` (superschnell, async, Swagger-Doku gleich dabei) |
| **Auth**             | API-Token (z. B. per `secrets.token_hex()`), später JWT möglich        |
| **Storage-Handling** | Python mit `os`, `hashlib` oder `blake3`, evtl. `sqlite` für Metadaten |
| **Client-GUI**       | Optional `PySimpleGUI` oder `tkinter`, CLI sowieso                     |
| **Transport**        | HTTPS mit SSL/TLS, self-signed für intern reicht                       |

---

## **Zusatzoptionen für später:**

* **Compression on-the-fly** (z. B. mit `zstd` für schnelle Kompression)
* **Backup-Encryption per Client** (AES256 mit `cryptography`, optional)
* **Push-Notifications / Mail-Reports**
* **Monitoring-Endpoint fürs AsgardBackup-Cluster**
* **Multi-Storage-Backend (Local, S3, MinIO)**

## **Modul-Struktur-Vorschlag:**

```
AsgardBackup/
├── asgardbackup.py           # Haupt-Skript
├── config.yaml                # Konfiguration (Blacklists, Serverpfade, etc.)
├── backup_engine.py           # Backup-Logik
├── restore_engine.py          # Restore-Logik
├── storage/                   # Backups (z. B. als Ordner mit Zeitstempeln)
├── logs/                      # Logs (Backup-Reports, Fehler)
├── utils.py                   # Hilfsfunktionen (Hashing, Logging, etc.)
└── README.md                  # Projektbeschreibung
```

---

## **Features (erste Version):**

| Feature                   | Beschreibung                          |
| ------------------------- | ------------------------------------- |
| **Blacklist-Backup**      | Alles sichern außer definierte Ordner |
| **Versionierung**         | Backups in Zeitstempel-Ordnern        |
| **Hash-Prüfung**          | Nur geänderte Dateien sichern         |
| **Restore-Option**        | Per Kommandozeile wiederherstellen    |
| **Plattformübergreifend** | Windows & Linux, Fokus auf User-Daten |
| **Admin-Webinterface**    | API-Verwaltung über Login-Seite, Admin wird per CLI erstellt |

---

## **Beispiel-Config (config.yaml)**

```yaml
backup_root: "D:/AsgardBackup"  # Zielordner fürs Backup
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

## Backup Logik (Inklude/Exklude listen)

Windows:
Blacklist für Windows-Datenbackup
Ordner	Warum ausschließen?
C:\Windows\	Betriebssystem – macht im User-Backup keinen Sinn
C:\Program Files\ & C:\Program Files (x86)\	Programme kann man neu installieren
C:\ProgramData\	Enthält oft nur Caches und temporäre Dateien
C:\Users\<User>\AppData\Local\	Lokale Caches, temporäre Daten
C:\Users\<User>\AppData\Roaming\	Optional: Je nachdem ob du App-Settings mitsichern willst
C:\$Recycle.Bin\	Papierkorb – muss nicht ins Backup
C:\System Volume Information\	Geschützt vom System
pagefile.sys, hiberfil.sys, swapfile.sys	RAM-Dumps, Swapfiles – nutzlos im Backup

Whitelist für Windows-Datenbackup:
Ordner	Warum?
C:\Users\<User>\Documents\	Wichtige Dokumente
C:\Users\<User>\Pictures\	Bilder
C:\Users\<User>\Desktop\	Meistens liegt da auch was Wichtiges
C:\Users\<User>\Downloads\	Optional, je nach Firma
C:\Users\<User>\AppData\Roaming\	Für bestimmte Einstellungen (z. B. Outlook-Profile)

Linux:
Linux Backup: Blacklist (Ausschlüsse)
Typische Ordner, die du NICHT sichern solltest:
Ordner	Warum?
/proc	Virtuelles Dateisystem (Runtime-Kernelinfos, ändert sich ständig)
/sys	Virtuelles Dateisystem für Kernel und Hardware
/dev	Geräteknoten, keine echten Dateien
/tmp	Temporäre Daten, nach Neustart weg
/run	Temporäre Systeminfos (RAM-only)
/var/run	Alias für /run (Legacy)
/mnt	Temporäre Mountpoints – je nachdem
/media	Externe Laufwerke – je nachdem
/swapfile	Swap-File – Unsinn im Backup
/boot	Nur sichern, wenn du wirklich willst (meist nicht nötig für User-Daten-Backup)
/lib, /lib64, /usr/lib	Systembibliotheken – Pakete kannst du neu installieren
/bin, /sbin, /usr/bin	Systemprogramme – auch neu installierbar
/var/cache	Caches – nicht sichern
/var/tmp	Temporäre Daten

Linux Backup: Whitelist (was sichern?)
Typische Ordner, die sinnvoll fürs Backup sind:
Ordner	Warum?
/home	User-Daten, das Wichtigste
/etc	System-Konfigurationsdateien (sehr sinnvoll, wenn du Server sicherst)
/opt	Optionale Programme, falls du dort Software hast
/srv	Server-Daten (z. B. Webseiten, Datenbanken – je nach Einsatz)
/root	Root-Home-Verzeichnis (wenn da was Wichtiges liegt)

Sonderfall: Docker / Virtualisierung
Wenn du Container nutzt, dann:

Ordner	Warum?
/var/lib/docker	Nur sichern, wenn du Container-States brauchst (sonst Images neu ziehen)
/var/lib/libvirt	Falls du virtuelle Maschinen per libvirt nutzt

Zusammengefasst:
Sinnvoll sichern	Lieber ausschließen
/home	/proc, /sys, /dev
/etc	/tmp, /run, /var/run
/opt	/lib, /usr/lib, /bin, /sbin
/srv	/var/cache, /var/tmp
/root (optional)	/swapfile
