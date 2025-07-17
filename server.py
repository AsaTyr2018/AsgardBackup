from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Header,
    Form,
    Request,
    Cookie,
)
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
import os
import secrets
import hashlib
import sqlite3

app = FastAPI(title="AsgardBackup Server")

STORAGE_ROOT = os.path.join(os.path.dirname(__file__), "storage")
TOKENS = {}

DB_PATH = os.path.join(os.path.dirname(__file__), "asgard.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS admin (username TEXT PRIMARY KEY, password_hash TEXT)"
    )
    return conn


def create_admin(username: str, password: str) -> None:
    conn = get_db()
    h = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn.execute(
            "INSERT INTO admin (username, password_hash) VALUES (?, ?)", (username, h)
        )
        conn.commit()
    finally:
        conn.close()


def check_admin(username: str, password: str) -> bool:
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT password_hash FROM admin WHERE username = ?", (username,)
        )
        row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return False
    return hashlib.sha256(password.encode()).hexdigest() == row[0]


ADMIN_SESSIONS: dict[str, str] = {}


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form():
    return (
        "<h2>Admin Login</h2>"
        "<form method='post'>"
        "<input name='username' placeholder='Benutzername'>"
        "<input type='password' name='password' placeholder='Passwort'>"
        "<button type='submit'>Login</button>"
        "</form>"
    )


@app.post("/admin/login")
async def admin_login(username: str = Form(...), password: str = Form(...)):
    if check_admin(username, password):
        session_id = secrets.token_hex(16)
        ADMIN_SESSIONS[session_id] = username
        response = RedirectResponse("/admin", status_code=302)
        response.set_cookie("session_id", session_id, httponly=True)
        return response
    raise HTTPException(status_code=401, detail="Login fehlgeschlagen")


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(session_id: str | None = Cookie(None)):
    if session_id is None or session_id not in ADMIN_SESSIONS:
        return RedirectResponse("/admin/login")
    token_list = "<br>".join(
        f"{u}: {t}" for t, u in TOKENS.items()
    ) or "Keine aktiven Tokens"
    return f"<h2>API Verwaltung</h2><p>{token_list}</p>"


def get_username(x_token: str | None = Header(None)) -> str:
    if x_token is None or x_token not in TOKENS:
        raise HTTPException(status_code=401, detail="Ungültiger Token")
    return TOKENS[x_token]


@app.post("/api/login")
async def login(username: str):
    token = secrets.token_hex(16)
    TOKENS[token] = username
    os.makedirs(os.path.join(STORAGE_ROOT, username), exist_ok=True)
    return {"token": token}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), username: str = Header(...), x_token: str | None = Header(None)):
    user = get_username(x_token)
    if user != username:
        raise HTTPException(status_code=403, detail="Token passt nicht zum Benutzer")
    user_dir = os.path.join(STORAGE_ROOT, user)
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "hochgeladen"}


@app.post("/api/check")
async def check(filename: str, filehash: str, x_token: str | None = Header(None)):
    user = get_username(x_token)
    file_path = os.path.join(STORAGE_ROOT, user, filename)
    if not os.path.exists(file_path):
        return {"exists": False}
    with open(file_path, "rb") as f:
        data = f.read()
    existing_hash = hashlib.sha256(data).hexdigest()
    return {"exists": existing_hash == filehash}


@app.get("/api/list")
async def list_files(x_token: str | None = Header(None)):
    user = get_username(x_token)
    user_dir = os.path.join(STORAGE_ROOT, user)
    files = os.listdir(user_dir) if os.path.exists(user_dir) else []
    return {"files": files}


@app.post("/api/restore")
async def restore(filename: str, x_token: str | None = Header(None)):
    user = get_username(x_token)
    file_path = os.path.join(STORAGE_ROOT, user, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    return FileResponse(path=file_path, filename=filename)


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="AsgardBackup Server")
    sub = parser.add_subparsers(dest="cmd")
    create = sub.add_parser("create-admin", help="Admin anlegen")
    create.add_argument("username")
    create.add_argument("password")
    serve = sub.add_parser("serve", help="Server starten")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.cmd == "create-admin":
        create_admin(args.username, args.password)
        print("Admin erstellt")
    else:
        os.makedirs(STORAGE_ROOT, exist_ok=True)
        uvicorn.run(app, host=args.host, port=args.port)

