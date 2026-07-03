import re
from app.rag.vector_search import VectorSearch
from app.rag.graph_search import GraphSearch

_STOPWORDS = {
    "The", "This", "That", "These", "Those", "What", "When", "Where",
    "Who", "Why", "How", "Is", "Are", "Was", "Were", "A", "An", "In",
    "On", "At", "For", "To", "From", "Of", "And", "Or", "But",
    "Le", "La", "Les", "Un", "Une", "Des", "Du", "De", "Ce",
    "Cet", "Cette", "Ces", "Mon", "Ton", "Son", "Ma", "Ta", "Sa",
    "Mes", "Tes", "Ses", "Nos", "Vos", "Leurs", "Notre", "Votre",
    "Best", "Worst", "Most", "Least", "Top", "Great", "Good", "Bad",
}

# Match named entities: any sequence starting with an uppercase letter (with French
# accents) followed by any mix of letters, spaces, hyphens, en-dashes, and apostrophes.
# This captures: "Arc de Triomphe", "Champs-Élysées", "Palais De Tokyo",
# "Coulée Verte René-Dumont", "Bichat–Claude Bernard Hospital", "France", "Paris", etc.
_ACCENTED_UPPER = r"A-ZÉÈÊËÔÛÙÎÏÇŒÀÂÄÆ"
_ACCENTED_LOWER = r"a-zéèêëôûùîïçœàâäæ"
_ENTITY_PATTERN = re.compile(
    rf"\b[{_ACCENTED_UPPER}][{_ACCENTED_LOWER}{_ACCENTED_UPPER}'’\-–\s]+\b"
)


def extract_entity_candidates(text: str, limit: int = 10) -> list[str]:
    seen = []
    for match in _ENTITY_PATTERN.findall(text):
        candidate = match.strip().strip("'’").strip()
        if not candidate or candidate in _STOPWORDS:
            continue
        if candidate not in seen:
            seen.append(candidate)
    return seen[:limit]


class HybridRetriever:

    def __init__(self):
        self.vector = VectorSearch()
        self.graph = GraphSearch()

    def retrieve(self, query: str) -> dict:
        print("🔍 Vector search...")
        chunks = self.vector.search(query)

        # Extract entities from BOTH the retrieved chunks AND the user's query
        entity_names = []
        for c in chunks:
            entity_names.extend(extract_entity_candidates(c["text"]))
        entity_names.extend(extract_entity_candidates(query))
        entity_names = list(dict.fromkeys(entity_names))[:10]

        if entity_names:
            print(f"🧠 Graph expansion... ({len(entity_names)} candidate entities)")
            graph_data = self.graph.expand_entities(entity_names)
            print("ENTITY NAMES:", entity_names)
            print("GRAPH RESULT:", graph_data)
        else:
            print("🧠 Graph expansion skipped (no entities found in chunks)")
            graph_data = []

        return {
            "chunks": chunks,
            "graph": graph_data,
        }