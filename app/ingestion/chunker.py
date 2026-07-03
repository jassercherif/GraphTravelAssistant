# chunker.py
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=4000,         # was 1000 — much fewer chunks per page
    chunk_overlap=400,       # proportional overlap
    separators=[
        "\n## ",            # Wikipedia uses ## for sections
        "\n### ",
        "\n#### ",
        "\n\n",
        "\n",
        ". ",
        " ",
        "",
    ],
)

def chunk_text(text: str, metadata: dict | None = None):
    """
    Split Firecrawl markdown into semantically coherent chunks.
    Each chunk keeps metadata for traceability.
    """

    if not text or not text.strip():
        return []

    document = Document(
        page_content=text,
        metadata=metadata or {},
    )

    chunks = splitter.split_documents([document])

    # Ensure no empty chunks
    return [
        c for c in chunks
        if c.page_content and c.page_content.strip()
    ]