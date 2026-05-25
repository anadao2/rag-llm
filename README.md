# RAG-LLM

API de ingestão para pipeline RAG usando **Domain-Driven Design (DDD)** e princípios **SOLID**.

## Visão Geral

Este projeto implementa uma arquitetura moderna com:

- **Domain-Driven Design (DDD)** - Separação clara de domínio, aplicação e infraestrutura
- **Princípios SOLID** - Código testável, extensível e desacoplado
- **Pattern Strategy** - Múltiplas estratégias de chunking (OCP)
- **Pattern Specification** - Composição de regras de filtro (OCP)
- **Event-Driven** - Arquitetura desacoplada via eventos (DIP)

### Funcionalidades

- Leitura de arquivos `.txt` em `data/docs`
- **Chunking com Strategy Pattern**: Sentence-aware, Fixed-size, e extensível
- Geração de embeddings via OpenAI
- Persistência vetorial local com FAISS
- **Processamento**: Síncrono (API) ou assíncrono (Worker + Redis)

## Tecnologias

- **Python 3.12**
- **FastAPI** + Uvicorn
- **Redis** (fila de processamento)
- **FAISS** (`faiss-cpu`) - vetores
- **OpenAI API** - embeddings
- **Docker Compose**

## Arquitetura: DDD + SOLID

## Estrutura do Projeto (Arquitetura DDD)

```text
.
|-- app/
|   |-- domain/                    # Nucleo de negocio - zero dependencias externas
|   |   |-- entities/              # Document, Chunk (identidade, lifecycle)
|   |   |-- value_objects/         # DocumentId, ChunkId, Embedding (imutaveis)
|   |   |-- repositories/          # Interfaces (ports)
|   |   |-- services/              # Domain Services (chunking, embedding)
|   |
|   |-- application/               # Casos de uso - orquestracao
|   |   |-- use_cases/             # IngestDocumentsUseCase, GetHealthStatusUseCase
|   |   |-- dto/                   # Data Transfer Objects
|   |
|   |-- infrastructure/            # Implementacoes concretas (adapters)
|   |   |-- persistence/           # JSON/FAISS repositories + mappers
|   |   |-- external/              # OpenAI embedder
|   |   |-- message_queue/         # Redis worker
|   |
|   |-- interface/                 # API HTTP
|   |   |-- api/
|   |       |-- routes/            # FastAPI controllers
|   |       |-- schemas/           # Pydantic models
|   |
|   |-- core/config.py             # Configuracoes
|   |-- main.py                    # Entry point FastAPI
|   `-- worker.py                  # Entry point worker
|
|-- tests/                         # Testes unitarios, integracao, E2E
|-- data/
|   |-- docs/                      # Documentos de entrada (.txt)
|   `-- faiss/                     # Indices vetoriais
|-- docker-compose.yml
|-- Dockerfile
`-- requirements.txt
```

### Principios DDD Aplicados

| Conceito | Implementacao |
|----------|---------------|
| **Entity** | `Document`, `Chunk` - identidade unica, lifecycle |
| **Value Object** | `DocumentId`, `ChunkId`, `Embedding` - imutaveis, validados |
| **Repository** | Interfaces no Domain, implementacoes na Infrastructure |
| **Domain Service** | `ChunkingService`, `EmbeddingService` - logica compartilhada |
| **Application Service** | `IngestDocumentsUseCase` - orquestracao |
| **Anti-Corruption Layer** | Mappers isolam modelo de persistencia |

### Princípios SOLID Aplicados

| Princípio | Implementação | Benefício |
|-----------|---------------|-----------|
| **S**ingle Responsibility | Strategies, Specifications, Events separados | Código coeso e testável |
| **O**pen/Closed | Strategy Pattern, Specification Pattern | Extensível sem modificação |
| **L**iskov Substitution | Todas as estratégias de chunking substituíveis | Polimorfismo seguro |
| **I**nterface Segregation | `ReadRepository`, `WriteRepository` separados | Menor acoplamento |
| **D**ependency Inversion | Injeção via construtor, Abstract Factory | Testável e flexível |

### Patterns Implementados

| Pattern | Onde | Propósito |
|---------|------|-----------|
| **Strategy** | `app/domain/strategies/` | Múltiplos algoritmos de chunking |
| **Specification** | `app/domain/specifications/` | Composição de regras de filtro |
| **Repository** | `app/domain/repositories/` | Abstração de persistência |
| **Unit of Work** | `app/domain/repositories/unit_of_work.py` | Transações |
| **Event-Driven** | `app/domain/events/` | Desacoplamento via eventos |
| **Factory** | `app/domain/factories/` | Criação de objetos |
| **Mapper** | `app/infrastructure/persistence/mappers/` | ACL isolando domínio |

## Pré-requisitos

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

## Testes

O projeto inclui testes em **6 camadas** (27 testes no total):

### Rodar todos os testes
```bash
python run_tests.py
```

### Rodar com pytest
```bash
pytest tests/ -v
```

### Testes individuais por camada
```bash
# Domain Layer (Entities, Value Objects, Domain Services)
python tests/test_domain.py

# Application Layer (Use Cases)
python tests/test_application.py

# Infrastructure Layer (Repositories, Mappers)
python tests/test_infrastructure.py

# Integration (API endpoints)
python tests/test_integration.py

# End-to-End (Fluxo completo)
python tests/test_e2e.py

# SOLID Principles (Validação arquitetural) ✅ NOVO
python tests/test_solid.py
```

### Cobertura de Testes

| Suite | Foco | Testes |
|-------|------|--------|
| `test_domain.py` | Entities, Value Objects, Strategies, Specifications | 9 |
| `test_application.py` | Use Cases, DTOs | 4 |
| `test_infrastructure.py` | Repositories, Mappers | 3 |
| `test_integration.py` | FastAPI endpoints | 3 |
| `test_e2e.py` | Fluxo completo com mocks | 4 |
| `test_solid.py` | SRP, OCP, LSP, ISP, DIP | 7 |
| **Total** | | **30** |

### Resultado esperado
```
============================================================
📊 TEST SUMMARY
============================================================
✅ PASSED: Domain Layer Tests
✅ PASSED: Application Layer Tests
✅ PASSED: Infrastructure Layer Tests
✅ PASSED: Integration Tests
✅ PASSED: End-to-End Tests
✅ PASSED: SOLID Principles Tests

Results: 6/6 test suites passed (27 testes)
🎉 ALL TESTS PASSED!
============================================================
```

## Documentação

- **[Arquitetura DDD](docs/ddd-architecture.md)** - Diagramas e explicação da arquitetura em camadas
- **[Princípios SOLID](docs/solid-principles.md)** - Como cada princípio foi aplicado

## Exemplos de Uso

### Strategy Pattern (OCP)
```python
from app.domain.strategies import SentenceAwareChunking, FixedSizeChunking
from app.domain.services.strategy_based_chunking_service import StrategyBasedChunkingService

# Escolher estratégia em runtime
strategy = SentenceAwareChunking()
service = StrategyBasedChunkingService(strategy)
chunks = service.chunk_document(document, chunk_size=500, overlap=100)
```

### Specification Pattern (OCP)
```python
from app.domain.specifications import PROCESSED, TXT_FILES

# Compor regras sem modificar classes
processed_txt = PROCESSED.and_(TXT_FILES)
docs = [d for d in all_docs if processed_txt.is_satisfied_by(d)]
```

### Event-Driven (DIP)
```python
from app.domain.events import EventBus, MetricsEventHandler

event_bus = EventBus()
event_bus.subscribe(DocumentProcessingCompleted, MetricsEventHandler())
```

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch de feature (`git checkout -b feature/minha-feature`)
3. Commit suas alteracoes (`git commit -m "feat: minha feature"`)
4. Push para sua branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

## Licenca

Defina aqui a licenca do projeto (ex.: MIT).
