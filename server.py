from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import FileResponse
import os
import secrets
import hashlib

app = FastAPI(title="AsgardBackup Server")

STORAGE_ROOT = os.path.join(os.path.dirname(__file__), "storage")
TOKENS = {}


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
    import uvicorn
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)

