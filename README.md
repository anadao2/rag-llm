# RAG-LLM

API de ingestao para pipeline RAG usando FastAPI, OpenAI Embeddings, FAISS e worker assíncrono com Redis.

## Visao Geral

Este projeto indexa documentos `.txt` para uso em fluxos de Retrieval-Augmented Generation (RAG):

- Leitura de arquivos em `data/docs`
- Chunking de texto com sobreposicao configuravel
- Geracao de embeddings via OpenAI
- Persistencia vetorial local com FAISS
- Processamento por API ou por fila (worker + Redis)

## Tecnologias

- Python
- FastAPI + Uvicorn
- Redis
- FAISS (`faiss-cpu`)
- OpenAI API
- Docker Compose

## Estrutura do Projeto

```text
.
|-- app/
|   |-- api/routes/ingest.py
|   |-- core/config.py
|   |-- repositories/doc_repo.py
|   |-- services/
|   |-- schemas/
|   |-- main.py
|   `-- worker.py
|-- data/
|   |-- docs/
|   `-- faiss/
|-- docker-compose.yml
|-- Dockerfile
`-- requirements.txt
```

## Pre-requisitos

- Docker e Docker Compose
- Chave da OpenAI (`OPENAI_API_KEY`)

## Configuracao de Ambiente

1. Crie um arquivo `.env` na raiz do projeto.
2. Adicione ao menos a variavel:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Variaveis suportadas (com defaults):

- `DOCS_DIR` (padrao: `data/docs`)
- `FAISS_DIR` (padrao: `data/faiss`)
- `CHUNK_SIZE` (padrao: `600`)
- `CHUNK_OVERLAP` (padrao: `100`)
- `EMBEDDING_MODEL` (padrao: `text-embedding-3-small`)
- `REDIS_URL` (padrao: `redis://redis:6379/0`)
- `INGEST_QUEUE` (padrao: `ingest:jobs`)

## Como Executar

Suba os servicos:

```bash
docker compose up --build
```

Servicos iniciados:

- API: `http://localhost:8000`
- Redis: `localhost:6379`
- Worker de ingestao em background

## Endpoints

### Health check

```http
GET /health
```

Resposta esperada:

```json
{
  "api_status": "ok",
  "vector_store_status": "ok",
  "indexed_documents_count": 0
}
```

### Ingestao sincronas pela API

```http
POST /ingest
Content-Type: application/json
```

Body (opcional):

```json
{
  "docs_dir": "data/docs",
  "chunk_size": 600,
  "chunk_overlap": 100,
  "embedding_model": "text-embedding-3-small"
}
```

## Fluxo de Ingestao

1. Adicione arquivos `.txt` em `data/docs`.
2. Chame `POST /ingest`.
3. O indice FAISS e metadados serao salvos em `data/faiss`.

## Desenvolvimento Local (sem Docker)

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Para rodar o worker local:

```bash
python -m app.worker
```

## Contribuicao

1. Faça um fork do projeto
2. Crie uma branch de feature (`git checkout -b feature/minha-feature`)
3. Commit suas alteracoes (`git commit -m "feat: minha feature"`)
4. Push para sua branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

## Licenca

Defina aqui a licenca do projeto (ex.: MIT).
