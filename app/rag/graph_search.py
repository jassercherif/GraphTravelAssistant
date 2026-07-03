from app.graph.neo4j_client import Neo4jClient


class GraphSearch:

    def __init__(self):
        self.db = Neo4jClient()

    def expand_entities(self, entity_names: list[str], depth: int = 1) -> list[dict]:
        if not entity_names:
            return []

        # Use depth=1 by default to avoid exponential explosion.
        # Only return essential fields (id, type, text) — NOT full node properties.
        query = f"""
        UNWIND $names AS name
        MATCH (e:Entity {{id: name}})
        CALL (e) {{
            WITH e
            MATCH p = (e)-[r*1..{depth}]-(n:Entity)
            WHERE n.type IN ['City','Attraction','Restaurant','Food','Hotel','Activity']
            RETURN n.id AS node_id,
                   n.type AS node_type,
                   labels(n) AS node_labels
            LIMIT 30
        }}
        RETURN DISTINCT node_id, node_type, node_labels
        """

        try:
            return self.db.run(query, {"names": entity_names})
        except Exception as e:
            print("Neo4j graph expansion failed:")
            print(type(e))
            print(e)
            raise