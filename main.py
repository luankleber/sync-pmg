import os
import time
import json
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

UPLOAD_FOLDER = "uploads"

# Permitir chamadas de qualquer origem (ideal para testes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua por seu domínio específico se desejar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carregar usuários válidos e suas license keys a partir de variável de ambiente JSON
def carregar_usuarios():
    json_str = os.getenv("USUARIOS_LICENCA", "{}")
    try:
        return json.loads(json_str)
    except Exception:
        return {}

USUARIOS_LICENCA = carregar_usuarios()

def validar_token(usuario: str, chave: str):
    return USUARIOS_LICENCA.get(usuario) == chave

def limpar_arquivos_antigos(dias_para_manter=7):
    agora = time.time()
    limite = dias_para_manter * 24 * 3600
    print("Executando limpeza de arquivos antigos...")

    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for arquivo in files:
            caminho = os.path.join(root, arquivo)
            if agora - os.path.getmtime(caminho) > limite:
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
async def upload(file: UploadFile = File(...), usuario: str = Query(...), license_key: str = Query(...)):
    if not validar_token(usuario, license_key):
        raise HTTPException(status_code=403, detail="Credenciais inválidas")

    pasta_usuario = os.path.join(UPLOAD_FOLDER, license_key)
    os.makedirs(pasta_usuario, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_usuario, file.filename)

    with open(caminho_arquivo, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "ok", "filename": file.filename}

@app.get("/list")
async def listar_arquivos(usuario: str = Query(...), license_key: str = Query(...)):
    if not validar_token(usuario, license_key):
        raise HTTPException(status_code=403, detail="Credenciais inválidas")

    pasta_usuario = os.path.join(UPLOAD_FOLDER, license_key)

    if not os.path.exists(pasta_usuario):
        return {"arquivos": []}

    arquivos = os.listdir(pasta_usuario)
    return {"arquivos": arquivos}

@app.get("/pull")
async def pull(usuario: str = Query(...), license_key: str = Query(...)):
    if not validar_token(usuario, license_key):
        raise HTTPException(status_code=403, detail="Credenciais inválidas")

    pasta_usuario = os.path.join(UPLOAD_FOLDER, license_key)
    if not os.path.exists(pasta_usuario):
        raise HTTPException(status_code=404, detail="Nenhum arquivo encontrado")

    arquivos = [f for f in os.listdir(pasta_usuario) if os.path.isfile(os.path.join(pasta_usuario, f))]
    if not arquivos:
        raise HTTPException(status_code=404, detail="Nenhum arquivo encontrado")

    arquivos.sort(key=lambda f: os.path.getmtime(os.path.join(pasta_usuario, f)), reverse=True)
    arquivo_mais_recente = arquivos[0]
    caminho_arquivo = os.path.join(pasta_usuario, arquivo_mais_recente)

    return FileResponse(path=caminho_arquivo, filename=arquivo_mais_recente, media_type='application/vnd.ms-excel')

@app.delete("/delete")
async def delete_file(filename: str = Query(...), usuario: str = Query(...), license_key: str = Query(...)):
    if not validar_token(usuario, license_key):
        raise HTTPException(status_code=403, detail="Credenciais inválidas")

    pasta_usuario = os.path.join(UPLOAD_FOLDER, license_key)
    caminho_arquivo = os.path.join(pasta_usuario, filename)

    if not os.path.exists(caminho_arquivo):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    os.remove(caminho_arquivo)
    return {"status": "ok", "message": f"Arquivo {filename} removido"}
