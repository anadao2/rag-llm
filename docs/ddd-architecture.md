# Arquitetura DDD - RAG-LLM

## Diagrama de Camadas (Layered Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE LAYER                          │
│  ┌─────────────────┐  ┌─────────────────┐                    │
│  │   API Routes    │  │  Schemas (DTO)  │                    │
│  │   ingest.py     │  │  Pydantic       │                    │
│  └────────┬────────┘  └─────────────────┘                    │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────┐                   │
│  │  Controllers (FastAPI Dependencies) │                   │
│  │         Factory Pattern              │                   │
│  └────────┬────────────────────────────┘                   │
└───────────┼─────────────────────────────────────────────────┘
            │
            │ Uses
            ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                          │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Use Cases     │  │   DTOs          │                  │
│  │                 │  │                 │                  │
│  │ - IngestDocs    │  │ - Request/Resp  │                  │
│  │ - GetHealth     │  │ - Data Transfer │                  │
│  └────────┬────────┘  └─────────────────┘                  │
│           │                                                 │
│  ┌────────┴──────────────────────────────────────────┐     │
│  │  Orquestra Domain Services e Repositories          │     │
│  │  NÃO contém lógica de negócio                     │     │
│  └─────────────────────────────────────────────────────┘     │
└───────────┼───────────────────────────────────────────────────┘
            │
            │ Uses (via interfaces)
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Entities    │  │ Value Objects│  │ Domain Services  │  │
│  │              │  │              │  │                  │  │
│  │ - Document   │  │ - DocumentId │  │ - Chunking       │  │
│  │ - Chunk      │  │ - ChunkId    │  │ - Embedding      │  │
│  │              │  │ - Embedding  │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐│
│  │  Repository Interfaces (Ports)                         ││
│  │  - DocumentRepository                                  ││
│  │  - ChunkRepository                                     ││
│  └────────────────────────────────────────────────────────┘│
│                                                             │
│  🎯 REGRA DE OURO: Zero dependências externas               │
└─────────────────────────────────────────────────────────────┘
            ▲
            │ Implements
┌───────────┴───────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Persistence    │  │   External      │  │  Message    │ │
│  │                 │  │                 │  │   Queue     │ │
│  │ - JSON Doc Repo │  │ - OpenAI        │  │ - Redis     │ │
│  │ - FAISS Chunk   │  │ - (Mais LLMs)   │  │   Worker    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │     Mappers     │  │    Adapters     │                   │
│  │  (Domain <->    │  │  (Interfaces    │                   │
│  │   Persistence)  │  │   externas)     │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Fluxo de Dependências

```
Interface ──► Application ──► Domain ◄─── Infrastructure
                 │              │
                 └──────────────┘
               (via interfaces/ports)
```

**Regra de Dependência:**
- Domain não conhece nenhuma outra camada
- Application conhece apenas Domain
- Interface conhece Application e Domain
- Infrastructure implementa interfaces do Domain

## Benefícios da Arquitetura DDD

### 1. Separação de Responsabilidades
- **Domain**: Regras de negócio puras, testáveis sem mocks complexos
- **Application**: Orquestração, transações, casos de uso
- **Infrastructure**: Detalhes técnicos (banco, API externa, fila)
- **Interface**: Adaptação para o mundo exterior (HTTP, CLI)

### 2. Testabilidade
```python
# Teste de Domain - sem mocks necessários
chunking_service = ChunkingService(chunk_size=600, overlap=100)
chunks = chunking_service.chunk_document(document)
assert len(chunks) > 0

# Teste de Application - mock nos repositories
mock_doc_repo = Mock(spec=DocumentRepository)
use_case = IngestDocumentsUseCase(mock_doc_repo, ...)
```

### 3. Substituibilidade
- Trocar FAISS por Pinecone: implementar `ChunkRepository`
- Trocar OpenAI por Local Embeddings: implementar `EmbeddingClient`
- Trocar JSON por PostgreSQL: implementar `DocumentRepository`

### 4. Independência de Framework
- O Domain não importa FastAPI, FAISS, Redis, OpenAI
- Pode ser extraído como biblioteca independente

## Mapeamento dos Conceitos DDD

| Conceito DDD | Implementação |
|--------------|---------------|
| **Entity** | `Document`, `Chunk` - identidade única, lifecycle |
| **Value Object** | `DocumentId`, `ChunkId`, `Embedding` - imutável, sem identidade |
| **Aggregate** | Document + Chunks (implicitamente) |
| **Repository** | Interfaces em `domain/repositories/` |
| **Domain Service** | `ChunkingService`, `EmbeddingService` |
| **Application Service** | `IngestDocumentsUseCase` |
| **Factory** | Métodos `create()` nas entidades |
| **DTO** | `IngestRequestDTO`, `IngestResultDTO` |
| **Adapter** | `OpenAIEmbedder`, `FaissChunkRepository` |
| **Port** | Interfaces de Repository |

## Anti-Corruption Layer

Os **Mappers** (`DocumentMapper`, `ChunkMapper`) atuam como Anti-Corruption Layer:
- Isolam mudanças no schema de persistência
- Permitem evolução independente do modelo de domínio
- Traduzem entre modelos internos e externos

## Exemplo de Fluxo: Ingestão

```
1. HTTP Request → Interface Layer (ingest.py)
   ↓
2. Cria DTO → Application Layer
   ↓
3. Use Case orquestra:
   - Carrega docs (Domain não conhece arquivos)
   - Chama ChunkingService (Domain Service)
   - Chama EmbeddingService (Domain Service)
   - Persiste via Repositories (Ports)
   ↓
4. Infrastructure implementa persistência:
   - JSON/FAISS salva dados
   - OpenAI gera embeddings
   ↓
5. Retorna resultado → Interface → HTTP Response
```
