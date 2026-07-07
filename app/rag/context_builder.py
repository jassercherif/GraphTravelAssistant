class ContextBuilder:
    """Builds a single text context block from vector chunks and graph triples."""

    MAX_CONTEXT_TOKENS = 3000  # rough token budget for the context section

    def build(self, chunks: list[dict], graph: list[dict]) -> str:
        context = []

        context.append("=== VECTOR CHUNKS ===")
        if chunks:
            for c in chunks:
                text = c.get("text", "")
                if len(text) > 2000:
                    text = text[:2000] + "... [truncated]"
                context.append(f"- {text}")
        else:
            context.append("(no relevant chunks found)")

        context.append("\n=== GRAPH KNOWLEDGE ===")
        if graph:
            for triple in graph:
                head = triple.get("head", "")
                relation = triple.get("relation", "")
                tail = triple.get("tail", "")
                context.append(f"- {head} --{relation}--> {tail}")
        else:
            context.append("(no related graph facts found)")

        result = "\n".join(context)

        max_chars = self.MAX_CONTEXT_TOKENS * 4
        if len(result) > max_chars:
            result = result[:max_chars] + "\n... [context truncated due to length]"

        return result