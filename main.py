import os
import time
import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Body
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Tokens carregados via variáveis de ambiente
TOKENS_VALIDOS = {}

def carregar_tokens():
    global TOKENS_VALIDOS
    raw = os.environ.get("PMG_TOKENS")  # Ex: 'luan=ABC123,joao=XYZ456'
    TOKENS_VALIDOS = {}
    if raw:
        pares = raw.split(",")
        for par in pares:
            if "=" in par:
                usuario, chave = par.strip().split("=")
                TOKENS_VALIDOS[usuario] = chave

carregar_tokens()

def validar_license(usuario: str, license_key: str):
    return TOKENS_VALIDOS.get(usuario) == license_key

def limpar_arquivos_antigos(dias_para_manter=7):
    agora = time.time()
    limite = dias_para_manter * 24 * 3600
    print("Executando limpeza de arquivos antigos...")

    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for arquivo in files:
            caminho = os.path.join(root, arquivo)
            if os.path.isfile(caminho) and agora - os.path.getmtime(caminho) > limite:
                try:
                    os.remove(caminho)
                    print(f"Removido: {caminho}")
                except Exception as e:
                    print(f"Erro ao remover {caminho}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(limpar_arquivos_antigos, 'interval', hours=24)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.post("/upload")
async def upload(file: UploadFile = File(...), usuario: str = Query(...), license_key: str = Query(...)):
    if not validar_license(usuario, license_key):
        raise HTTPException(status_code=403, detail="Chave de licença inválida")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, license_key)
    os.makedirs(pasta_tecnico, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_tecnico, file.filename)

    with open(caminho_arquivo, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "ok", "filename": file.filename}

@app.post("/upload_json")
async def upload_json(usuario: str = Query(...), license_key: str = Query(...), data: dict = Body(...)):
    if not validar_license(usuario, license_key):
        raise HTTPException(status_code=403, detail="Chave de licença inválida")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, license_key)
    os.makedirs(pasta_tecnico, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{usuario}_{timestamp}.json"
    caminho = os.path.join(pasta_tecnico, nome_arquivo)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "ok", "filename": nome_arquivo}

@app.get("/list")
async def listar_arquivos(usuario: str = Query(...), license_key: str = Query(...)):
    if not validar_license(usuario, license_key):
        raise HTTPException(status_code=403, detail="Chave de licença inválida")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, license_key)
    if not os.path.exists(pasta_tecnico):
        return {"arquivos": []}

    arquivos = sorted(os.listdir(pasta_tecnico))
    return {"arquivos": arquivos}

@app.get("/pull")
async def pull(usuario: str = Query(...), license_key: str = Query(...)):
    if not validar_license(usuario, license_key):
        raise HTTPException(status_code=403, detail="Chave de licença inválida")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, license_key)
    if not os.path.exists(pasta_tecnico):
        raise HTTPException(status_code=404, detail="Nenhum arquivo encontrado")

    arquivos = [f for f in os.listdir(pasta_tecnico) if os.path.isfile(os.path.join(pasta_tecnico, f))]
    if not arquivos:
        raise HTTPException(status_code=404, detail="Nenhum arquivo encontrado")

    arquivos.sort(key=lambda f: os.path.getmtime(os.path.join(pasta_tecnico, f)), reverse=True)
    arquivo_mais_recente = arquivos[0]
    caminho_arquivo = os.path.join(pasta_tecnico, arquivo_mais_recente)

    return FileResponse(path=caminho_arquivo, filename=arquivo_mais_recente, media_type='application/json')

@app.delete("/delete")
async def delete_file(filename: str = Query(...), usuario: str = Query(...), license_key: str = Query(...)):
    if not validar_license(usuario, license_key):
        raise HTTPException(status_code=403, detail="Chave de licença inválida")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, license_key)
    caminho_arquivo = os.path.join(pasta_tecnico, filename)

    if not os.path.exists(caminho_arquivo):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    os.remove(caminho_arquivo)
    return {"status": "ok", "message": f"Arquivo {filename} removido"}

@app.get("/validate")
async def validate(usuario: str = Query(...), license_key: str = Query(...)):
    if validar_license(usuario, license_key):
        return {"status": "ok"}
    else:
        raise HTTPException(status_code=403, detail="Chave de licença inválida")
