import time
import random
import re
import uuid

from app.ingestion.sources import SOURCES
from app.ingestion.firecrawl_loader import load_page
from app.ingestion.chunker import chunk_text
from app.ingestion.graph_transformer import get_transformer
from app.ingestion.neo4j_client import Neo4jClient

from app.ingestion.embedding_generator import embed_documents


# ─────────────────────────────────────────────────────────────
# Rate Limiter
# ─────────────────────────────────────────────────────────────
class RateLimiter:
    def __init__(self, calls_per_minute=20):
        self.min_interval = 60.0 / calls_per_minute
        self.last_call = 0.0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


rate_limiter = RateLimiter(20)


# ─────────────────────────────────────────────────────────────
# Retry helper
# ─────────────────────────────────────────────────────────────
def call_with_retry(transformer, chunk, max_retries=5, base_delay=3.0):
    for attempt in range(1, max_retries + 1):
        try:
            rate_limiter.wait()
            return transformer.convert_to_graph_documents([chunk])

        except Exception as e:
            error = str(e).lower()

            if "api key" in error or "unauthorized" in error:
                raise

            if "429" in error or "rate limit" in error:
                delay = 30 + random.uniform(0, 10)
                time.sleep(delay)
                continue

            if attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
            else:
                return []

    return []


# ─────────────────────────────────────────────────────────────
# Neo4j Query (HYBRID GRAPH + VECTOR READY)
# ─────────────────────────────────────────────────────────────
INGEST_QUERY = """
UNWIND $chunks AS c

// ── CHUNK NODE (for vector search)
MERGE (ch:Chunk {id: c.id})
SET ch.text = c.text,
    ch.embedding = c.embedding

// ── PAGE NODE
MERGE (p:Page {url: c.source})
ON CREATE SET p.place = c.place

MERGE (p)-[:HAS_CHUNK]->(ch)

// ── ENTITY MENTIONS
WITH ch, c
UNWIND c.nodes AS n

MERGE (e:Entity {id: n.id})
SET e.type = n.label,
    e += n.intrinsic_properties

MERGE (ch)-[:MENTIONS]->(e)

// ── RELATIONSHIPS (GRAPH STRUCTURE)
WITH count(*) AS _
UNWIND $relationships AS r

MATCH (a:Entity {id: r.source})
MATCH (b:Entity {id: r.target})

MERGE (a)-[rel:RELATION {type: r.type, source: r.source_doc}]->(b)
ON CREATE SET rel.count = 1
ON MATCH SET rel.count = rel.count + 1
"""


# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────
def run_pipeline():
    print("🚀 Starting Hybrid GraphRAG ingestion...")

    transformer = get_transformer()
    db = Neo4jClient()

    total_chunks = 0
    total_errors = 0

    for place, url in SOURCES.items():
        print(f"\n📍 Processing: {place}")

        text = load_page(url)

        if not text or len(text.strip()) < 200:
            print("⚠️ Skipping empty page")
            continue

        chunks = chunk_text(
            text,
            metadata={"source": url, "place": place}
        )

        if not chunks:
            continue

        print(f"   📄 {len(chunks)} chunks")

        # ─────────────────────────────────────────────
        # 1. EMBEDDINGS (BATCH — IMPORTANT)
        # ─────────────────────────────────────────────
        chunk_texts = [c.page_content for c in chunks]
        embeddings = embed_documents(chunk_texts)

        # ─────────────────────────────────────────────
        # 2. PROCESS EACH CHUNK
        # ─────────────────────────────────────────────
        chunks_payload = []
        relationships_payload = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):

            graph_docs = call_with_retry(transformer, chunk)

            if not graph_docs:
                total_errors += 1
                continue

            chunk_id = str(uuid.uuid4())

            for doc in graph_docs:

                chunks_payload.append({
                    "id": chunk_id,
                    "text": chunk.page_content,
                    "embedding": embedding,
                    "source": url,
                    "place": place,
                    "nodes": [
                        {
                            "id": str(n.id),
                            "label": n.type,
                            "intrinsic_properties": dict(n.properties)
                        }
                        for n in doc.nodes
                    ]
                })

                relationships_payload.extend([
                    {
                        "source": str(r.source.id),
                        "target": str(r.target.id),
                        "type": r.type,
                        "source_doc": url
                    }
                    for r in doc.relationships
                ])

            total_chunks += 1

        # ─────────────────────────────────────────────
        # 3. STORE IN NEO4J
        # ─────────────────────────────────────────────
        try:
            db.run(
                INGEST_QUERY,
                {
                    "chunks": chunks_payload,
                    "relationships": relationships_payload
                }
            )
        except Exception as e:
            print(f"❌ Neo4j error: {e}")
            total_errors += 1

    db.close()

    print("\n✅ Ingestion completed!")
    print(f"   Chunks processed: {total_chunks}")
    print(f"   Errors:           {total_errors}")


if __name__ == "__main__":
    run_pipeline()