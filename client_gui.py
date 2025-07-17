import os
import json
import hashlib
import requests
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

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
    username = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
    resp = requests.post(f"{server}/api/login", params={"username": username})
    resp.raise_for_status()
    token = resp.json()["token"]
    cfg["server"] = server
    cfg["token"] = token
    save_config(cfg)
    return token


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AsgardBackup Client")
        cfg = load_config()
        self.server_var = tk.StringVar(value=cfg.get("server", ""))
        self.token_var = tk.StringVar(value=cfg.get("token", ""))

        tk.Label(self, text="Server-Adresse").grid(row=0, column=0, sticky="w")
        tk.Entry(self, textvariable=self.server_var, width=40).grid(row=0, column=1)
        tk.Label(self, text="API Token").grid(row=1, column=0, sticky="w")
        tk.Entry(self, textvariable=self.token_var, width=40).grid(row=1, column=1)
        tk.Button(self, text="Login", command=self.login).grid(row=2, column=0, pady=5)
        tk.Button(self, text="Datei hochladen", command=self.upload).grid(row=2, column=1, pady=5)
        tk.Button(self, text="Dateien auflisten", command=self.list_files).grid(row=3, column=0, pady=5)
        tk.Button(self, text="Wiederherstellen", command=self.restore).grid(row=3, column=1, pady=5)
        self.output = tk.Text(self, height=10, width=60)
        self.output.grid(row=4, column=0, columnspan=2, pady=5)

    def login(self):
        server = self.server_var.get()
        if not server:
            messagebox.showerror("Fehler", "Server-Adresse fehlt")
            return
        token = ensure_token(server)
        self.token_var.set(token)
        messagebox.showinfo("Info", "Token gespeichert")

    def upload(self):
        server = self.server_var.get()
        token = self.token_var.get()
        if not server or not token:
            messagebox.showerror("Fehler", "Bitte zuerst Login durchführen")
            return
        path = filedialog.askopenfilename()
        if not path:
            return
        filename = os.path.basename(path)
        h = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        check = requests.post(
            f"{server}/api/check",
            params={"filename": filename, "filehash": h},
            headers={"X-Token": token},
        )
        check.raise_for_status()
        if check.json().get("exists"):
            messagebox.showinfo("Info", "Datei bereits vorhanden")
            return
        with open(path, "rb") as f:
            resp = requests.post(
                f"{server}/api/upload",
                files={"file": (filename, f)},
                headers={"X-Token": token, "username": os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"},
            )
        resp.raise_for_status()
        messagebox.showinfo("Erfolg", "Upload abgeschlossen")

    def list_files(self):
        server = self.server_var.get()
        token = self.token_var.get()
        if not server or not token:
            messagebox.showerror("Fehler", "Bitte zuerst Login durchführen")
            return
        resp = requests.get(f"{server}/api/list", headers={"X-Token": token})
        resp.raise_for_status()
        self.output.delete(1.0, tk.END)
        data = resp.json()["files"]
        for fname, versions in data.items():
            self.output.insert(tk.END, f"{fname}\n")
            for v in versions:
                self.output.insert(tk.END, f"  {v}\n")

    def restore(self):
        server = self.server_var.get()
        token = self.token_var.get()
        if not server or not token:
            messagebox.showerror("Fehler", "Bitte zuerst Login durchführen")
            return
        filename = filedialog.askopenfilename(title="Datei wählen für Restore")
        if not filename:
            return
        name = os.path.basename(filename)
        resp = requests.post(
            f"{server}/api/restore",
            params={"filename": name},
            headers={"X-Token": token},
        )
        resp.raise_for_status()
        out_path = filedialog.asksaveasfilename(initialfile=name)
        if not out_path:
            return
        with open(out_path, "wb") as f:
            f.write(resp.content)
        messagebox.showinfo("Fertig", f"Gespeichert unter {out_path}")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
