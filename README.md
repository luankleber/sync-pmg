# PMG Report Sync Server

Servidor simples para sincronização automática de relatórios PMG gerados por técnicos em campo.

## Resumo do Projeto

Este projeto implementa um servidor web usando FastAPI que permite o upload, listagem, download e exclusão de arquivos (planilhas Excel) gerados pelos técnicos via app móvel. Cada técnico possui um token único que identifica seu espaço dedicado de arquivos no servidor.

O servidor também conta com uma rotina automática de limpeza que remove arquivos com mais de 7 dias para evitar acúmulo de dados desnecessários.

---

## Endpoints API

### 1. Upload de arquivo

**POST** `/upload?token=TOKEN`

- Parâmetros:
  - `token` (query): Token de autenticação do técnico.
  - `file` (form-data): Arquivo a ser enviado (upload multipart).
- Resposta:
  - `200 OK` e JSON com status e nome do arquivo.
- Erros:
  - `403 Forbidden` se o token for inválido.

---

### 2. Listar arquivos do técnico

**GET** `/list?token=TOKEN`

- Parâmetros:
  - `token` (query): Token do técnico.
- Resposta:
  - `200 OK` com JSON contendo lista dos nomes dos arquivos disponíveis.
- Erros:
  - `403 Forbidden` se token inválido.
  - `404 Not Found` se nenhum arquivo for encontrado.

---

### 3. Download de arquivo

**GET** `/pull?token=TOKEN&filename=NOME_DO_ARQUIVO`

- Parâmetros:
  - `token` (query): Token do técnico.
  - `filename` (query): Nome do arquivo a ser baixado.
- Resposta:
  - Arquivo para download.
- Erros:
  - `403 Forbidden` se token inválido.
  - `404 Not Found` se o arquivo não existir.

---

### 4. Deletar arquivo

**DELETE** `/delete?token=TOKEN&filename=NOME_DO_ARQUIVO`

- Parâmetros:
  - `token` (query): Token do técnico.
  - `filename` (query): Nome do arquivo a ser deletado.
- Resposta:
  - `200 OK` com confirmação da remoção.
- Erros:
  - `403 Forbidden` se token inválido.
  - `404 Not Found` se arquivo não existir.

---

## Configuração e execução

1. Certifique-se de ter Python 3.8+ instalado.
2. Instale dependências:
pip install fastapi uvicorn python-multipart apscheduler

markdown
Copy
Edit
3. Crie a pasta `uploads` na raiz do projeto.
4. Execute o servidor:
uvicorn main:app --host 0.0.0.0 --port 10000

yaml
Copy
Edit

---

## Observações

- Tokens válidos estão configurados no dicionário `TOKENS_VALIDOS` dentro do código.
- Os arquivos de cada técnico ficam armazenados em `uploads/{token}/`.
- A limpeza automática exclui arquivos com mais de 7 dias de criação.
- Use o método HTTP correto em cada endpoint (ex: DELETE para deletar).

---

## ToDos

- [ ] Implementar autenticação dinâmica de usuários/tokens via banco de dados.
- [ ] Criar interface web simples para técnicos visualizarem arquivos e status.
- [ ] Adicionar logs detalhados de acesso e operações para auditoria.
- [ ] Melhorar segurança com HTTPS e verificação de origem das requisições.
- [ ] Adicionar notificações automáticas para técnicos após upload/download.
- [ ] Implementar limites de tamanho e tipos permitidos para arquivos.
- [ ] Otimizar limpeza automática para rodar em horários específicos (ex: madrugada).
- [ ] Documentar melhor os fluxos de uso para técnicos e administradores.
- [ ] Criar scripts de backup e restauração dos arquivos armazenados.
