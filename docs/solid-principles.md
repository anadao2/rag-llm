# Princípios SOLID - Implementação

## Visão Geral

Este documento descreve como os 5 princípios SOLID foram aplicados no projeto RAG-LLM.

---

## S - Single Responsibility Principle (SRP)

> **"Uma classe deve ter apenas um motivo para mudar."**

### Aplicações no Projeto

#### 1. Chunking Strategies
```python
# app/domain/strategies/chunking_strategy.py
class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, document: Document, config: ChunkingConfig) -> List[Chunk]:
        ...  # Apenas algoritmo de chunking

# app/domain/services/strategy_based_chunking_service.py  
class StrategyBasedChunkingService:
    def __init__(self, strategy: ChunkingStrategy) -> None:
        self._strategy = strategy  # Apenas orquestração
```
**SRP aplicado:**
- `ChunkingStrategy` apenas define interface de algoritmo
- `StrategyBasedChunkingService` apenas orquestra a estratégia
- `SentenceAwareChunking` apenas implementa chunking por sentença

#### 2. Specifications
```python
# app/domain/specifications/document_specifications.py
class DocumentProcessedSpecification(Specification[Document]):
    def is_satisfied_by(self, candidate: Document) -> bool:
        return candidate.status == "completed"  # Apenas verificação de status
```
**SRP aplicado:** Cada Specification tem uma única regra de filtro.

#### 3. Event Handlers
```python
# app/domain/events/document_events.py
class MetricsEventHandler(DomainEventHandler[DocumentProcessingCompleted]):
    def handle(self, event: DocumentProcessingCompleted) -> None:
        self._total_processed += 1  # Apenas métricas
```

### Benefícios
- Código mais coeso e focado
- Testes mais simples (uma responsabilidade por teste)
- Menor acoplamento

---

## O - Open/Closed Principle (OCP)

> **"Aberto para extensão, fechado para modificação."**

### Aplicações no Projeto

#### 1. Strategy Pattern para Chunking
```python
# Adicionar nova estratégia SEM modificar o serviço existente:
class SemanticChunking(ChunkingStrategy):  # Nova estratégia!
    def chunk(self, document, config):
        # Lógica baseada em embeddings semânticos
        ...

# Uso:
service = StrategyBasedChunkingService(SemanticChunking())
```

#### 2. Specification Pattern
```python
# Compor especificações SEM modificar as classes existentes:
# app/domain/specifications/specification.py
class AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self._left = left
        self._right = right
```

**Exemplo de uso (OCP):**
```python
from app.domain.specifications.document_specifications import *

# Composição de regras sem modificar nada
processed_txt = PROCESSED.and_(TXT_FILES)
failed_or_pdf = FAILED.or_(DocumentByExtensionSpecification(".pdf"))
```

#### 3. Event-Driven Architecture
```python
# Adicionar novo handler SEM modificar publicador:
class EmailNotificationHandler(DomainEventHandler[DocumentProcessingFailed]):
    def handle(self, event):
        send_email(f"Falha no documento {event.aggregate_id}")

# Registrar sem modificar EventBus
event_bus.subscribe(DocumentProcessingFailed, EmailNotificationHandler())
```

### Benefícios
- Adicionar funcionalidade sem risco de quebrar código existente
- Sistema evoluível
- Facilita manutenção

---

## L - Liskov Substitution Principle (LSP)

> **"Subclasses devem ser substituíveis por suas classes base."**

### Aplicações no Projeto

#### 1. Chunking Strategies
```python
# test_solid.py - Validação LSP
strategies = [
    SentenceAwareChunking(),  # Substitui ChunkingStrategy
    FixedSizeChunking(),      # Substitui ChunkingStrategy
]

for strategy in strategies:
    service = StrategyBasedChunkingService(strategy)  # LSP!
    chunks = service.chunk_document(doc, chunk_size=30, overlap=5)
    # Invariantes mantidas: sempre retorna List[Chunk]
    assert isinstance(chunks, list)
    assert all(isinstance(c, Chunk) for c in chunks)
```

#### 2. Repository Implementações
```python
# Qualquer implementação de DocumentRepository pode ser usada
class InMemoryDocumentRepository(DocumentRepository):  # Para testes
    ...

class JsonDocumentRepository(DocumentRepository):  # Produção
    ...

# Uso (LSP):
def process_documents(repo: DocumentRepository):  # Abstração
    ...

process_documents(InMemoryDocumentRepository())  # OK
process_documents(JsonDocumentRepository())      # OK
```

### Pré-condições e Pós-condições

| Invariante | SentenceAwareChunking | FixedSizeChunking |
|------------|----------------------|-------------------|
| Entrada | Document válido | Document válido |
| Saída | List[Chunk] | List[Chunk] |
| Chunk text não vazio | ✅ | ✅ |
| Ordem preservada | ✅ | ✅ |

### Benefícios
- Polimorfismo seguro
- Código cliente não precisa saber implementação concreta
- Testes mais robustos

---

## I - Interface Segregation Principle (ISP)

> **"Clientes não devem depender de interfaces que não usam."**

### Aplicações no Projeto

#### 1. Read vs Write Repositories
```python
# app/domain/repositories/read_repository.py
class ReadRepository(ABC, Generic[T, ID]):
    @abstractmethod
    def find_by_id(self, id: ID) -> T | None: ...
    @abstractmethod
    def find_all(self) -> List[T]: ...
    # Sem métodos de escrita!

# app/domain/repositories/write_repository.py
class WriteRepository(ABC, Generic[T]):
    @abstractmethod
    def save(self, entity: T) -> None: ...
    @abstractmethod
    def delete(self, entity: T) -> None: ...
    # Sem métodos de leitura!
```

**Uso (ISP):**
```python
class DocumentQueryService:
    def __init__(self, repository: ReadRepository[Document, DocumentId]):
        # Apenas leitura, não precisa de save/delete
        self._repo = repository
```

#### 2. ChunkingStrategy Minimal
```python
class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, document: Document, config: ChunkingConfig) -> List[Chunk]:
        ...
    
    @abstractmethod
    def get_name(self) -> str:
        ...
    # Apenas 2 métodos necessários!
```

#### 3. DomainEventHandler
```python
class DomainEventHandler(ABC, Generic[T]):
    @abstractmethod
    def handle(self, event: T) -> None: ...
    # Apenas 1 método!
```

### Anti-pattern evitado
```python
# ❌ ANTES (interface gorda)
class Repository(ABC):
    def find_by_id(self): ...
    def find_all(self): ...
    def save(self): ...
    def delete(self): ...
    def search_by_text(self): ...
    def export_to_csv(self): ...

# ✅ DEPOIS (interfaces segregadas)
class ReadRepository: ...
class WriteRepository: ...
class SearchRepository: ...
class ExportRepository: ...
```

### Benefícios
- Menor acoplamento
- Interfaces mais coesas
- Mocking mais simples em testes

---

## D - Dependency Inversion Principle (DIP)

> **"Dependa de abstrações, não de concretos."**

### Aplicações no Projeto

#### 1. Injeção de Dependência via Construtor
```python
# app/domain/services/strategy_based_chunking_service.py
class StrategyBasedChunkingService:
    def __init__(self, strategy: ChunkingStrategy) -> None:
        # DIP: Depende da abstração ChunkingStrategy
        self._strategy = strategy

# Uso (injeção de implementação concreta):
service = StrategyBasedChunkingService(SentenceAwareChunking())
```

#### 2. Use Cases
```python
# app/application/use_cases/ingest_documents.py
class IngestDocumentsUseCase:
    def __init__(
        self,
        document_repo: DocumentRepository,      # Abstração
        chunk_repo: ChunkRepository,              # Abstração
        embedding_client: EmbeddingClient,      # Abstração
    ) -> None:
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.embedding_client = embedding_client
```

#### 3. Event Bus (DIP na prática)
```python
# Publicador depende de DomainEvent (abstração)
event_bus.publish(DocumentCreated(...))

# Handler depende de DomainEventHandler (abstração)
class LoggingEventHandler(DomainEventHandler[DomainEvent]):
    def handle(self, event: DomainEvent) -> None:
        ...
```

### Diagrama de Dependências

```
ANTES (dependências diretas):
┌─────────────┐      ┌──────────────────┐
│   Service   │─────▶│ SentenceAwareChunking │
└─────────────┘      └──────────────────┘
                            ▲
                            │
                    [Quebrado se mudar]

DEPOIS (DIP aplicado):
┌─────────────┐      ┌──────────────────┐
│   Service   │─────▶│ ChunkingStrategy │◀─────┐
└─────────────┘      │   (abstração)    │      │
                     └──────────────────┘      │
                           ▲                    │
                           │                    │
              ┌────────────┴────────┐          │
              │                     │          │
    ┌─────────▼────────┐  ┌────────▼─────────┐ │
    │ SentenceAware    │  │ FixedSize        │─┘
    │ Chunking         │  │ Chunking         │
    └──────────────────┘  └──────────────────┘
```

### Inversão de Controle (IoC)
```python
# Factories para criação (DIP)
# app/domain/factories/service_factory.py
class ServiceFactory(ABC):
    @abstractmethod
    def create_chunking_service(self) -> ChunkingService: ...
    @abstractmethod
    def create_embedding_service(self) -> EmbeddingService: ...
    # Cliente depende da fábrica abstrata
```

### Benefícios
- Testabilidade (fácil injetar mocks)
- Flexibilidade (trocar implementações)
- Desacoplamento
- Segue o princípio "Programar para interfaces"

---

## Resumo por Camada

### Domain Layer
| Princípio | Aplicação |
|-----------|-----------|
| SRP | Entities, Value Objects, Specifications, Events |
| OCP | Strategy Pattern, Specification Pattern |
| LSP | ChunkingStrategy implementações |
| ISP | ReadRepository, WriteRepository |
| DIP | Repository interfaces, ServiceFactory |

### Application Layer
| Princípio | Aplicação |
|-----------|-----------|
| SRP | Cada Use Case tem uma responsabilidade |
| OCP | Novos DTOs sem modificar Use Cases |
| DIP | Injeção de Repositories e Services |

### Infrastructure Layer
| Princípio | Aplicação |
|-----------|-----------|
| LSP | Implementações de Repository |
| DIP | Implementação de interfaces do Domain |

---

## Testes de Validação

Execute os testes SOLID:
```bash
python tests/test_solid.py
```

Validações incluídas:
1. **SRP**: Classes não têm métodos fora de sua responsabilidade
2. **OCP**: Novas estratégias funcionam sem modificar serviço
3. **LSP**: Qualquer ChunkingStrategy pode ser usada no serviço
4. **ISP**: ReadRepository não tem métodos de escrita
5. **DIP**: Serviço depende de ChunkingStrategy (abstração)

---

## Conclusão

A aplicação dos princípios SOLID resultou em:

✅ **Código testável** - Mocks fáceis com interfaces
✅ **Código extensível** - Novas features sem modificar existentes
✅ **Código mantenível** - Responsabilidades claras
✅ **Código desacoplado** - Depende de abstrações
✅ **Código reutilizável** - Componentes coesos

---

*Documento criado como parte do refactor DDD + SOLID*
