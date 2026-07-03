from app.rag.retriever import HybridRetriever
from app.rag.context_builder import ContextBuilder
from app.brains import glm_5p1 as g  # your LLM wrapper


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

        # 1. Retrieve
        data = self.retriever.retrieve(query)

        # 2. Build context
        context = self.builder.build(data["chunks"], data["graph"])

        # 3. Generate
        prompt = PROMPT_TEMPLATE.format(context=context, query=query)
        response = self.llm.invoke(prompt)

        # Normalize LangChain message -> plain string
        return getattr(response, "content", str(response))