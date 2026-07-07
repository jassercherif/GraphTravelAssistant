from app.rag.retriever import HybridRetriever
from app.rag.context_builder import ContextBuilder
from app.brains import glm_5p1 as g


PROMPT_TEMPLATE = """You are a travel assistant.

IMPORTANT RULES:
    - Use ONLY the provided context.
    - Do NOT use external knowledge.
    - If the information is missing, say "I don't know".

    CONTEXT:
        {context}

        QUESTION:
            {query}

            Answer clearly using ONLY facts from the context."""


class RAGPipeline:

    def __init__(self):
        self.retriever = HybridRetriever()
        self.builder = ContextBuilder()
        self.llm = g

    def ask(self, query: str) -> str:
        print("🚀 RAG pipeline started")

        data = self.retriever.retrieve(query)
        context = self.builder.build(data["chunks"], data["graph"])
        prompt = PROMPT_TEMPLATE.format(context=context, query=query)

        # LLM calls can time out independently of retrieval quality (network,
        # backend load, etc.). One retry, then a clear message instead of a
        # raw traceback reaching the CLI.
        for attempt in range(2):
            try:
                response = self.llm.invoke(prompt)
                return getattr(response, "content", str(response))
            except Exception as e:
                print(f"LLM call failed (attempt {attempt + 1}/2): {type(e).__name__}: {e}")
                if attempt == 1:
                    return (
                        "Sorry, the assistant is taking too long to respond right now. "
                        "Please try again in a moment."
                    )