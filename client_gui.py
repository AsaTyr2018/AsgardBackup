import os
import json
import hashlib
import requests
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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
        self.version_var = tk.StringVar(value="Keine Version gewählt")
        self.files: dict[str, list[str]] = {}

        # Eingabefelder und Buttons
        tk.Label(self, text="Server-Adresse").grid(row=0, column=0, sticky="w")
        tk.Entry(self, textvariable=self.server_var, width=40).grid(row=0, column=1, columnspan=2, sticky="we")
        tk.Label(self, text="API Token").grid(row=1, column=0, sticky="w")
        tk.Entry(self, textvariable=self.token_var, width=40).grid(row=1, column=1, columnspan=2, sticky="we")
        tk.Button(self, text="Login", command=self.login).grid(row=2, column=0, pady=5)
        tk.Button(self, text="Datei hochladen", command=self.upload).grid(row=2, column=1, pady=5)
        tk.Button(self, text="Dateien laden", command=self.list_files).grid(row=2, column=2, pady=5)

        tk.Label(self, textvariable=self.version_var, font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=3, pady=(5, 0))

        # Dateiansicht
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.grid(row=4, column=0, columnspan=3, sticky="nsew")
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=1)

        ttk.Label(left, text="Dateien").pack(anchor="w")
        self.file_list = tk.Listbox(left)
        self.file_list.pack(fill="both", expand=True)
        self.file_list.bind("<<ListboxSelect>>", self.on_file_select)

        ttk.Label(right, text="Versionen").pack(anchor="w")
        self.version_list = tk.Listbox(right)
        self.version_list.pack(fill="both", expand=True)
        self.version_list.bind("<<ListboxSelect>>", self.on_version_select)
        ttk.Button(right, text="Herunterladen", command=self.restore).pack(pady=5)

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
        data = resp.json()["files"]
        self.files = data
        self.file_list.delete(0, tk.END)
        self.version_list.delete(0, tk.END)
        self.version_var.set("Keine Version gewählt")
        for fname in sorted(data.keys()):
            self.file_list.insert(tk.END, fname)

    def on_file_select(self, event):
        sel = self.file_list.curselection()
        if not sel:
            return
        fname = self.file_list.get(sel[0])
        versions = self.files.get(fname, [])
        self.version_list.delete(0, tk.END)
        for v in versions:
            self.version_list.insert(tk.END, v)
        if versions:
            self.version_list.selection_set(len(versions) - 1)
            self.version_var.set(versions[-1])
        else:
            self.version_var.set("Keine Version verfügbar")

    def on_version_select(self, event):
        sel = self.version_list.curselection()
        if sel:
            self.version_var.set(self.version_list.get(sel[0]))

    def restore(self):
        server = self.server_var.get()
        token = self.token_var.get()
        if not server or not token:
            messagebox.showerror("Fehler", "Bitte zuerst Login durchführen")
            return
        sel_file = self.file_list.curselection()
        if not sel_file:
            messagebox.showerror("Fehler", "Keine Datei ausgewählt")
            return
        name = self.file_list.get(sel_file[0])
        version = self.version_var.get()
        if version.startswith("Keine"):
            messagebox.showerror("Fehler", "Keine Version gewählt")
            return
        resp = requests.post(
            f"{server}/api/restore",
            params={"filename": name, "version": version},
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
