import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


def ChatModel(model, max_tokens=2048, timeout=None):
    return ChatOpenAI(
        model=model,  #qwen/Qwen3-4B:free,  # nex-agi/deepseek-v3.1-nex-n1:free
        temperature=0,
        openai_api_key=os.getenv("OPENROUTER_KEY"),  # Change environment variable name
        openai_api_base="https://openrouter.ai/api/v1",  # This is the key change
        max_tokens=max_tokens,
        timeout=timeout,
        max_retries=2,
    )
def GraphModel(model, max_tokens=2048, timeout=None):
    return ChatGroq(
    model=model,
    temperature=0,
    max_tokens=max_tokens,   # or 4096 depending on model
    max_retries=2,
    api_key=os.getenv("GROQ_KEY")
)

def EmbeddingModel(model, timeout=None):
    return CohereEmbeddings(
    model=model, 
    cohere_api_key=os.getenv("COHERE_KEY"), 
    #dimensions=Embedding_DIM
    )



FIREWORKS_BASE = "https://api.fireworks.ai/inference/v1"


def fireworks(model, max_tokens=8192, timeout=45):
    return ChatOpenAI(
        model=model,
        openai_api_key=os.getenv("FIREWORKS_KEY"),
        openai_api_base=FIREWORKS_BASE,
        temperature=0.1,
        timeout=timeout,
        max_tokens=max_tokens,
        max_retries=2,
    )

def embedding_fireworks(model):
    return OpenAIEmbeddings(
        model=model,
        openai_api_key=os.getenv("FIREWORKS_KEY"),
        openai_api_base=FIREWORKS_BASE,
        check_embedding_ctx_length=False,
    )

embedding_model = EmbeddingModel("embed-v4.0")
   


gpt_oss_med = fireworks("accounts/fireworks/models/gpt-oss-120b")

nomic_embedding = embedding_fireworks("nomic-ai/nomic-embed-text-v1.5")

deepseek_r1 = fireworks("accounts/fireworks/models/deepseek-v3p2")

glm_5p1 = fireworks(
    "accounts/fireworks/models/glm-5p2",
    max_tokens=4096,
    timeout=20,
)