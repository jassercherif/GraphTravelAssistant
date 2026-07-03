class ContextBuilder:
    """Builds a single text context block from vector chunks and graph results."""

    MAX_CONTEXT_TOKENS = 3000  # rough token budget for the context section

    def build(self, chunks: list[dict], graph: list[dict]) -> str:
        context = []

        context.append("=== VECTOR CHUNKS ===")
        if chunks:
            for c in chunks:
                text = c.get("text", "")
                # Truncate each chunk text to avoid individual bloat
                if len(text) > 2000:
                    text = text[:2000] + "... [truncated]"
                context.append(f"- {text}")
        else:
            context.append("(no relevant chunks found)")

        context.append("\n=== GRAPH KNOWLEDGE ===")
        if graph:
            for g in graph:
                node_id = g.get("node_id", "")
                node_type = g.get("node_type", "")
                context.append(f"- {node_type}: {node_id}")
        else:
            context.append("(no related graph entities found)")

        result = "\n".join(context)

        # Hard cap on total context length (characters, ~1 token = 4 chars)
        max_chars = self.MAX_CONTEXT_TOKENS * 4
        if len(result) > max_chars:
            result = result[:max_chars] + "\n... [context truncated due to length]"

        return result

    @staticmethod
    def _format_item(item) -> str:
        # Works whether Neo4jClient.run() returns plain dicts (via record.data())
        # or raw neo4j Node/Relationship objects.
        if isinstance(item, dict):
            return ", ".join(f"{k}={v}" for k, v in item.items())
        return str(item)