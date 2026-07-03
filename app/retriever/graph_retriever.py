

# app/retriever/graph_retriever.py

class GraphRetriever:
    def __init__(self, db):
        self.db = db

    def search(self, query: str):
        cypher = """
        MATCH (n)
        WHERE toLower(n.id) CONTAINS toLower($query)
        MATCH p=(n)-[*1..2]-(m)
        RETURN p
        LIMIT 20
        """

        result = self.db.run(cypher, {"query": query})
        return result