import argparse
import os
import json
import hashlib
import requests
from pathlib import Path

CONFIG_PATH = Path.home() / ".asgard_client.json"


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f)


def ensure_token(server: str) -> str:
    cfg = load_config()
    token = cfg.get("token")
    if token:
        return token
    username = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    resp = requests.post(f"{server}/api/login", params={"username": username})
    resp.raise_for_status()
    token = resp.json()["token"]
    cfg["server"] = server
    cfg["token"] = token
    save_config(cfg)
    return token


def cmd_login(args):
    token = ensure_token(args.server)
    print(f"Token gespeichert: {token}")


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_upload(args):
    cfg = load_config()
    server = args.server or cfg.get("server")
    if not server:
        raise SystemExit("Serveradresse nicht angegeben")
    token = cfg.get("token")
    if not token:
        token = ensure_token(server)
    path = Path(args.file)
    if not path.is_file():
        raise SystemExit("Datei nicht gefunden")
    fh = file_hash(path)
    check = requests.post(
        f"{server}/api/check",
        params={"filename": path.name, "filehash": fh},
        headers={"X-Token": token},
    )
    check.raise_for_status()
    if check.json().get("exists"):
        print("Datei bereits vorhanden, überspringe Upload")
        return
    with open(path, "rb") as f:
        up = requests.post(
            f"{server}/api/upload",
            files={"file": (path.name, f)},
            headers={"X-Token": token, "username": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"},
        )
    up.raise_for_status()
    print(up.json())


def cmd_list(args):
    cfg = load_config()
    server = args.server or cfg.get("server")
    token = cfg.get("token")
    if not server or not token:
        raise SystemExit("Bitte zuerst login ausführen")
    resp = requests.get(f"{server}/api/list", headers={"X-Token": token})
    resp.raise_for_status()
    for fname, versions in resp.json()["files"].items():
        print(fname + ":" )
        for v in versions:
            print("  " + v)


def cmd_restore(args):
    cfg = load_config()
    server = args.server or cfg.get("server")
    token = cfg.get("token")
    if not server or not token:
        raise SystemExit("Bitte zuerst login ausführen")
    data = {"filename": args.filename}
    if args.version:
        data["version"] = args.version
    resp = requests.post(f"{server}/api/restore", params=data, headers={"X-Token": token})
    resp.raise_for_status()
    out_path = Path(args.output or args.filename)
    with open(out_path, "wb") as f:
        f.write(resp.content)
    print(f"Datei gespeichert unter {out_path}")


def main():
    parser = argparse.ArgumentParser(description="AsgardBackup CLI")
    parser.add_argument("--server", help="Serveradresse, z.B. http://localhost:8000")
    sub = parser.add_subparsers(dest="cmd")

    login = sub.add_parser("login", help="Token vom Server holen")
    login.set_defaults(func=cmd_login)

    upload = sub.add_parser("upload", help="Datei hochladen")
    upload.add_argument("file")
    upload.set_defaults(func=cmd_upload)

    ls = sub.add_parser("list", help="Dateien auflisten")
    ls.set_defaults(func=cmd_list)

    restore = sub.add_parser("restore", help="Datei wiederherstellen")
    restore.add_argument("filename")
    restore.add_argument("--version")
    restore.add_argument("--output", help="Zielpfad")
    restore.set_defaults(func=cmd_restore)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
