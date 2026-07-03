#app\ingestion\graph_transformer.py
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.prompts import ChatPromptTemplate
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.brains import gpt_oss_med


ALLOWED_NODES = [
    "Country",
    "City",
    "Attraction",
    "Restaurant",
    "Hotel",
    "Activity",
    "Food"
]

ALLOWED_RELATIONSHIPS = [
    "HAS_CITY",
    "HAS_ATTRACTION",
    "HAS_RESTAURANT",
    "HAS_HOTEL",
    "LOCATED_IN",
    "NEAR",
    "HAS_ACTIVITY",
    "HAS_FOOD"
]

def _load_prompt(name: str) -> str:
    """Load a prompt from the prompts/ folder adjacent to this module."""
    from pathlib import Path
    p = Path(__file__).resolve().parent / "prompts" / name
    if not p.exists():
        print(f"Prompt file not found: {p}")
        return ""
    return p.read_text(encoding="utf-8")

TRAVEL_SYSTEM_INSTRUCTIONS = _load_prompt("Travel_Graph_Prompt.md")

# {input} is the actual chunk text (chunk.page_content), injected here by
# LLMGraphTransformer at call time via format_messages(input=...).
# Without this placeholder, no chunk content is ever sent to the model.
TRAVEL_GRAPH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TRAVEL_SYSTEM_INSTRUCTIONS),
    ("human", "Extract the knowledge graph from the following text:\n\n{input}")
])


def get_transformer():
    llm = gpt_oss_med  # Use GPT-OSS Medium

    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=ALLOWED_NODES,
        allowed_relationships=ALLOWED_RELATIONSHIPS,
        strict_mode=True,
        prompt=TRAVEL_GRAPH_PROMPT,
        ignore_tool_usage=False,  
    )

    return transformer