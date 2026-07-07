# Travel AI Agent - GraphRAG API

A FastAPI-based Travel Assistant using GraphRAG (Graph-based Retrieval Augmented Generation) with Neo4j.

## Project Structure

```
TravelAIAgent/
├── main.py                 # Application entry point
├── pyproject.toml         # Project dependencies
├── docker-compose.yaml    # Docker setup
└── app/
    ├── app.py             # FastAPI application
    ├── brains.py          # LLM and embedding models
    ├── api/
    │   ├── routes.py      # API endpoints
    │   └── schemas.py     # Pydantic models
    ├── core/
    │   └── config.py      # Configuration
    ├── graph/
    │   └── neo4j_client.py
    ├── ingestion/
    │   ├── pipeline.py
    │   ├── chunker.py
    │   ├── embedding_generator.py
    │   ├── graph_transformer.py
    │   └── prompts/
    └── rag/
        ├── rag_pipeline.py
        ├── retriever.py
        ├── context_builder.py
        ├── vector_search.py
        └── graph_search.py
```

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# API Keys
OPENROUTER_KEY=your_openrouter_key
GROQ_KEY=your_groq_key
COHERE_KEY=your_cohere_key
FIREWORKS_KEY=your_fireworks_key
FIRECRAWL_API_KEY=your_firecrawl_key
```

### 3. Start Neo4j

```bash
docker-compose up -d
```

## Running the Application

### Option 1: Using main.py (Recommended)

```bash
uv run main.py
```

### Option 2: Using uvicorn directly

```bash
uv run uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check

```bash
GET http://localhost:8000/
```

Response:
```json
{
  "status": "ok",
  "message": "Travel AI Assistant API running"
}
```

### Chat Endpoint

```bash
POST http://localhost:8000/chat/
Content-Type: application/json

{
  "query": "What are the best attractions in Paris?"
}
```

Response:
```json
{
  "query": "What are the best attractions in Paris?",
  "answer": "Based on the context..."
}
```

## Important Notes

### Running from Project Root

**ALWAYS** run the application from the project root directory (`TravelAIAgent/`), not from subdirectories.

✅ Correct:
```bash
cd TravelAIAgent
uv run main.py
```

❌ Wrong:
```bash
cd TravelAIAgent/app
uv run app.py  # This will fail with import errors
```

### Why?

The project uses absolute imports (e.g., `from app.rag.rag_pipeline import RAGPipeline`). Python needs to see `app/` as a package, which only works when running from the project root.

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'app.rag'`:

1. Make sure you're in the project root directory
2. Verify all `__init__.py` files exist

### Missing Dependencies

```bash
uv pip install -e .
```

### Neo4j Connection Issues

1. Check if Neo4j is running: `docker ps`
2. Verify credentials in `.env`
3. Test connection: `bolt://localhost:7687`

## Development

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
