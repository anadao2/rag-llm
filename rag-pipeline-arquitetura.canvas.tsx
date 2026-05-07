import { Callout, Divider, Grid, H1, H2, H3, Pill, Stack, Table, Text } from 'cursor/canvas';

export default function RagPipelineArquitetura() {
  return (
    <Stack gap={20}>
      <H1>Arquitetura RAG ideal (FastAPI + FAISS + OpenAI + Docker Compose)</H1>
      <Text tone="secondary">
        Pipeline modular para ingestao, chunking, embeddings, indexacao vetorial e retrieval, com
        deploy local e pronto para evoluir para producao.
      </Text>

      <Grid columns={3} gap={12}>
        <Pill tone="info">FastAPI: API e orquestracao</Pill>
        <Pill tone="info">FAISS: indice vetorial local</Pill>
        <Pill tone="info">OpenAI: embeddings</Pill>
      </Grid>

      <Divider />

      <H2>Estrutura de pastas</H2>
      <Table
        headers={["Caminho", "Tipo", "Responsabilidade"]}
        rows={[
          ["/app/main.py", "API", "Inicializa FastAPI, middlewares, healthcheck e roteadores"],
          ["/app/api/routes/ingest.py", "Rota", "Endpoint para upload e disparo de ingestao"],
          ["/app/api/routes/retrieval.py", "Rota", "Endpoint para busca semantica por pergunta"],
          ["/app/core/config.py", "Core", "Settings (env vars), chaves e parametros do pipeline"],
          ["/app/core/logging.py", "Core", "Logging estruturado e correlacao por request id"],
          ["/app/schemas/", "Schema", "Modelos Pydantic para requests/responses"],
          ["/app/services/loader.py", "Servico", "Leitura de PDF, TXT, DOCX e normalizacao de texto"],
          ["/app/services/chunker.py", "Servico", "Chunking (tamanho, overlap, estrategia por tipo)"],
          ["/app/services/embedder.py", "Servico", "Geracao de embeddings via OpenAI"],
          ["/app/services/vector_store.py", "Servico", "Operacoes FAISS (add/search/save/load)"],
          ["/app/services/retriever.py", "Servico", "Busca top-k, filtros e ranking final"],
          ["/app/repositories/doc_repo.py", "Repo", "Persistencia de metadados de documentos/chunks"],
          ["/data/raw/", "Dados", "Arquivos recebidos para ingestao"],
          ["/data/processed/", "Dados", "Chunks limpos e prontos para embedding"],
          ["/data/faiss/", "Dados", "Indice FAISS e artefatos do vetor store"],
          ["/docker-compose.yml", "Infra", "Servicos app + worker + volumes + rede"],
        ]}
      />

      <Divider />

      <H2>Responsabilidades dos modulos</H2>
      <Grid columns={2} gap={14}>
        <Stack gap={8}>
          <H3>Camada de API</H3>
          <Text>- Expor endpoints para ingestao e retrieval.</Text>
          <Text>- Validar payloads e retornar erros padronizados.</Text>
          <Text>- Nao conter regra de negocio complexa.</Text>
        </Stack>
        <Stack gap={8}>
          <H3>Camada de Servicos</H3>
          <Text>- Conter logica de pipeline (load, chunk, embed, index, search).</Text>
          <Text>- Garantir idempotencia na ingestao por hash de documento.</Text>
          <Text>- Encapsular detalhes do provider de embedding e do FAISS.</Text>
        </Stack>
        <Stack gap={8}>
          <H3>Camada de Repositorio</H3>
          <Text>- Guardar metadados de documentos e chunks.</Text>
          <Text>- Mapear id de chunk para vetor no indice.</Text>
          <Text>- Facilitar auditoria e reprocessamento.</Text>
        </Stack>
        <Stack gap={8}>
          <H3>Camada de Infra</H3>
          <Text>- Docker Compose para padronizar ambiente.</Text>
          <Text>- Volumes persistentes para dados e indice.</Text>
          <Text>- Variaveis de ambiente para configuracao por ambiente.</Text>
        </Stack>
      </Grid>

      <Divider />

      <H2>Fluxo do pipeline (fim a fim)</H2>
      <Table
        headers={["Etapa", "Entrada", "Processo", "Saida"]}
        rows={[
          [
            "1. Ingestao",
            "Arquivo bruto (PDF/TXT/DOCX)",
            "Upload via endpoint /ingest e registro de metadados",
            "Documento salvo em /data/raw",
          ],
          [
            "2. Chunking",
            "Texto extraido",
            "Split por tamanho + overlap + limpeza",
            "Lista de chunks com metadados",
          ],
          [
            "3. Embeddings",
            "Chunks textuais",
            "Chamada OpenAI embeddings em lote com retry",
            "Vetores densos por chunk",
          ],
          [
            "4. Vector Store",
            "Vetores + metadados",
            "Indexacao no FAISS e persistencia em disco",
            "Indice pronto para busca",
          ],
          [
            "5. Retrieval",
            "Pergunta do usuario",
            "Embedding da pergunta + busca top-k + rerank leve",
            "Contexto relevante para etapa de geracao",
          ],
        ]}
      />

      <Callout tone="success" title="Boas praticas recomendadas">
        Defina chunk_size e overlap por tipo de documento, use batch embedding com controle de
        taxa, e persista versao do indice para rollback seguro.
      </Callout>
    </Stack>
  );
}
