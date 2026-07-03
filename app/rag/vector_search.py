from app.graph.neo4j_client import Neo4jClient
from app.ingestion.embedding_generator import embed_query


class VectorSearch:

    def __init__(self):
        self.db = Neo4jClient()

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        print("Generating query embedding...")
        embedding = embed_query(query)
        print(f"Embedding dimension: {len(embedding)}")

        try:
            result = self.db.run(
                """
                CALL db.index.vector.queryNodes(
                    'chunk_embeddings',
                    $top_k,
                    $embedding
                )
                YIELD node, score
                RETURN node.text AS text,
                node.id AS id,
                score
                """,
                {"embedding": embedding, "top_k": top_k},
            )
            print(f"Retrieved {len(result)} chunks")
            return result
        except Exception as e:
            print("Neo4j vector search failed:")
            print(type(e))
            print(e)
            raise