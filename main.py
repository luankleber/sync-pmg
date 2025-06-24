
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
from typing import List
from datetime import datetime

app = FastAPI()

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.post("/upload")
async def upload_file(token: str = Query(...), file: UploadFile = File(...)):
    user_dir = os.path.join(UPLOAD_DIR, token)
    os.makedirs(user_dir, exist_ok=True)
    filename = f"{datetime.utcnow().isoformat()}_{file.filename}"
    filepath = os.path.join(user_dir, filename)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"status": "ok", "filename": filename}

@app.get("/pull")
def pull_files(token: str):
    user_dir = os.path.join(UPLOAD_DIR, token)
    if not os.path.exists(user_dir):
        return JSONResponse(content=[])
    files = sorted(os.listdir(user_dir))
    return JSONResponse(content=files)

@app.get("/download")
def download_file(token: str, filename: str):
    filepath = os.path.join(UPLOAD_DIR, token, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
