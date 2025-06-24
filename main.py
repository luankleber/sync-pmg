import os
import time
import json
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

UPLOAD_FOLDER = "uploads"

# Exemplo simples de tokens válidos
# Você pode carregar de um arquivo JSON ou banco depois
TOKENS_VALIDOS = {
    "luan": "4f2b1fc2-3e5d-44c0-b126-fadadf870b65",
    "joao": "e8894ef1-0d12-4fd5-91cb-2d8c857fa272"
}

def validar_token(token: str):
    return token in TOKENS_VALIDOS.values()

def limpar_arquivos_antigos(dias_para_manter=7):
    agora = time.time()
    limite = dias_para_manter * 24 * 3600  # segundos
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

# Scheduler para rodar limpeza todo dia
scheduler = BackgroundScheduler()
scheduler.add_job(limpar_arquivos_antigos, 'interval', hours=24)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.post("/upload")
async def upload(file: UploadFile = File(...), token: str = Query(...)):
    if not validar_token(token):
        raise HTTPException(status_code=403, detail="Token inválido")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, token)
    os.makedirs(pasta_tecnico, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_tecnico, file.filename)

    with open(caminho_arquivo, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "ok", "filename": file.filename}

@app.delete("/delete")
async def delete_file(filename: str = Query(...), token: str = Query(...)):
    if not validar_token(token):
        raise HTTPException(status_code=403, detail="Token inválido")

    pasta_tecnico = os.path.join(UPLOAD_FOLDER, token)
    caminho_arquivo = os.path.join(pasta_tecnico, filename)

    if not os.path.exists(caminho_arquivo):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    os.remove(caminho_arquivo)
    return {"status": "ok", "message": f"Arquivo {filename} removido"}
