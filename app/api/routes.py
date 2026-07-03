# app/api/routes.py

from fastapi import FastAPI
from pydantic import BaseModel

from app.graph.neo4j_client import Neo4jClient
from app.retriever.graph_retriever import GraphRetriever
from app.rag.rag_chain import RAGChain

app = FastAPI()

# INIT SYSTEM
db = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

retriever = GraphRetriever(db)

# dummy LLM (replace with Fireworks/OpenAI)
class DummyLLM:
    def invoke(self, prompt):
        return "LLM ANSWER BASED ON CONTEXT:\n" + prompt[:300]

llm = DummyLLM()

rag = RAGChain(retriever, llm)


# REQUEST MODEL
class Query(BaseModel):
    question: str


@app.post("/ask")
def ask(query: Query):
    return {
        "answer": rag.ask(query.question)
    }