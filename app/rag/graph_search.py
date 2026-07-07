from collections import defaultdict

from app.graph.neo4j_client import Neo4jClient
from app.rag.entity_constants import GENERIC_ENTITIES


class GraphSearch:

    ALLOWED_TARGET_TYPES = [
        "City", "Attraction", "Restaurant", "Food", "Hotel", "Activity",
    ]

    def __init__(self):
        self.db = Neo4jClient()

    def find_known_entities_in_text(self, text: str, limit: int = 5) -> list[str]:
        query = """
        MATCH (e:Entity)
        WHERE toLower($text) CONTAINS toLower(e.id)
        RETURN DISTINCT e.id AS id, size(e.id) AS len
        ORDER BY len DESC
        LIMIT $limit
        """
        try:
            rows = self.db.run(query, {"text": text, "limit": limit})
            return [r["id"] for r in rows]
        except Exception as e:
            print("Neo4j known-entity lookup failed:")
            print(type(e))
            print(e)
            return []

    def verify_entities_exist(self, candidates: list[str]) -> list[str]:
        """
        Single batched round trip that checks which chunk-derived candidates
        actually exist as :Entity nodes. Anything that doesn't exist
        (fragments, mojibake, headings) is discarded before it can consume
        one of the limited chunk-entity slots.
        """
        if not candidates:
            return []
        query = """
        UNWIND $candidates AS name
        MATCH (e:Entity)
        WHERE toLower(e.id) = toLower(name)
        RETURN DISTINCT e.id AS id
        """
        try:
            rows = self.db.run(query, {"candidates": candidates})
            return [r["id"] for r in rows]
        except Exception as e:
            print("Neo4j entity verification failed:")
            print(type(e))
            print(e)
            return []

    def expand_entities(
        self,
        entity_names: list[str],
        depth: int = 1,
        per_entity_limit: int = 8,
        total_limit: int = 15,
    ) -> list[dict]:
        if not entity_names:
            return []

        raw_limit_per_entity = 40

        query = f"""
        UNWIND $names AS name
        MATCH (e:Entity {{id: name}})
        CALL (e) {{
            WITH e
            MATCH (e)-[r*1..{depth}]-(n:Entity)
            WHERE n.type IN $allowed_types AND n.id <> e.id
            WITH e, n, r[0] AS rel
            RETURN e.id AS source,
                   type(rel) AS relation,
                   n.id AS target,
                   n.type AS target_type,
                   startNode(rel) = e AS is_outgoing
            LIMIT $raw_limit_per_entity
        }}
        RETURN DISTINCT source, relation, target, target_type, is_outgoing
        """

        try:
            rows = self.db.run(
                query,
                {
                    "names": entity_names,
                    "allowed_types": self.ALLOWED_TARGET_TYPES,
                    "raw_limit_per_entity": raw_limit_per_entity,
                },
            )
        except Exception as e:
            print("Neo4j graph expansion failed:")
            print(type(e))
            print(e)
            raise

        by_head = defaultdict(list)
        for row in rows:
            if row["is_outgoing"]:
                head, tail = row["source"], row["target"]
            else:
                head, tail = row["target"], row["source"]
            by_head[head].append({
                "head": head,
                "relation": row["relation"],
                "tail": tail,
                "tail_type": row["target_type"],
            })

        # Dedup key uses an UNORDERED pair + relation type, not (head, tail)
        # directly. With a generic 'RELATION' type, "Paris->Louvre" and
        # "Louvre->Paris" read as the same fact shown twice — this collapses
        # that into a single triple.
        triples: list[dict] = []
        seen = set()

        for head, items in by_head.items():
            if head in GENERIC_ENTITIES:
                type_counts = defaultdict(int)
                per_type_cap = 2
                for item in items:
                    key = (item["relation"], frozenset({item["head"], item["tail"]}))
                    if key in seen or type_counts[item["tail_type"]] >= per_type_cap:
                        continue
                    seen.add(key)
                    type_counts[item["tail_type"]] += 1
                    triples.append(item)
            else:
                for item in items[:per_entity_limit]:
                    key = (item["relation"], frozenset({item["head"], item["tail"]}))
                    if key in seen:
                        continue
                    seen.add(key)
                    triples.append(item)

        return triples[:total_limit]