import os
import json
import time
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.responses import FileResponse

app = FastAPI()
UPLOAD_FOLDER = "uploads"

# Carrega JSON com usuários e license keys da variável de ambiente
USERS_JSON = os.getenv("USERS_JSON", "{}")
try:
    USERS = json.loads(USERS_JSON)
except json.JSONDecodeError:
    USERS = {}

def validar_licenca(usuario: str, license_key: str):
    return USERS.get(usuario) == license_key

def limpar_arquivos_antigos(dias_para_manter=7):
    agora = time.time()
    limite = dias_para_manter * 24 * 3600
    print("Executando limpeza de arquivos antigos...")

    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for arquivo in files:
            caminho = os.path.join(root, arquivo)
            tempo_mod = os.path.getmtime(caminho)
            if agora - tempo_mod > limite:
                try:
                    os.remove(caminho)
                    print(f"Arquivo removido: {caminho}")
                except Exception as e:
                    print(f"Erro ao remover {caminho}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(limpar_arquivos_antigos, 'interval', hours=24)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.post("/upload")
async def upload(
    usuario: str = Query(...),
    license_key: str = Query(...),
    file: UploadFile = File(...)
):
    if not validar_licenca(usuario, license_key):
        raise HTTPException(status_code=403, detail="Usuário ou License Key inválidos")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, usuario)
    os.makedirs(pasta_tecnico, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_tecnico, file.filename)

    with open(caminho_arquivo, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "ok", "filename": file.filename}

@app.delete("/delete")
async def delete_file(
    filename: str = Query(...),
    usuario: str = Query(...),
    license_key: str = Query(...)
):
    if not validar_licenca(usuario, license_key):
        raise HTTPException(status_code=403, detail="Usuário ou License Key inválidos")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, usuario)
    caminho_arquivo = os.path.join(pasta_tecnico, filename)

    if not os.path.exists(caminho_arquivo):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    os.remove(caminho_arquivo)
    return {"status": "ok", "message": f"Arquivo {filename} removido"}

@app.get("/pull")
async def pull(
    usuario: str = Query(...),
    license_key: str = Query(...)
):
    if not validar_licenca(usuario, license_key):
        raise HTTPException(status_code=403, detail="Usuário ou License Key inválidos")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, usuario)
    if not os.path.exists(pasta_tecnico):
        raise HTTPException(status_code=404, detail="Nenhum arquivo encontrado")

    arquivos = [f for f in os.listdir(pasta_tecnico) if os.path.isfile(os.path.join(pasta_tecnico, f))]
    if not arquivos:
        raise HTTPException(status_code=404, detail="Nenhum arquivo encontrado")

    arquivos.sort(key=lambda f: os.path.getmtime(os.path.join(pasta_tecnico, f)), reverse=True)
    arquivo_mais_recente = arquivos[0]
    caminho_arquivo = os.path.join(pasta_tecnico, arquivo_mais_recente)

    return FileResponse(path=caminho_arquivo, filename=arquivo_mais_recente, media_type='application/vnd.ms-excel')

@app.get("/list")
async def listar_arquivos(
    usuario: str = Query(...),
    license_key: str = Query(...)
):
    if not validar_licenca(usuario, license_key):
        raise HTTPException(status_code=403, detail="Usuário ou License Key inválidos")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, usuario)

    if not os.path.exists(pasta_tecnico):
        return {"arquivos": []}

    arquivos = os.listdir(pasta_tecnico)
    return {"arquivos": arquivos}
