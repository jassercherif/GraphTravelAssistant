import re

from app.rag.vector_search import VectorSearch
from app.rag.graph_search import GraphSearch
from app.rag.entity_constants import GENERIC_ENTITIES


_STOPWORDS = {
    "The", "This", "That", "These", "Those",
    "What", "When", "Where", "Who", "Why", "How",
    "Is", "Are", "Was", "Were",
    "A", "An", "In", "On", "At", "For", "To", "From",
    "Of", "And", "Or", "But",
    "Le", "La", "Les", "Un", "Une", "Des", "Du", "De",
    "Ce", "Cet", "Cette", "Ces",
    "Mon", "Ton", "Son", "Ma", "Ta", "Sa",
    "Mes", "Tes", "Ses", "Nos", "Vos", "Leurs",
    "Best", "Worst", "Most", "Least", "Top", "Great", "Good", "Bad",
    "File", "Image", "Category", "References", "Contents", "External Links",
    "Capital", "Capital City", "City", "Country", "Region",
    "Department", "Departments", "Arrondissement", "Arrondissements",
    "Communes", "Municipality",
}

_BAD_ENTITY_PATTERNS = [
    "Capital city", "Communes of", "Departments of",
    "Arrondissements of", "History of", "Geography of",
    "Politics of", "Economy of", "File",
]

_BAD_FIRST_WORDS = {
    "Examples", "Example", "Introduction", "Contents", "History",
    "References", "See", "Note", "Notes", "List", "Overview", "Summary",
    "Best", "Food", "Guide", "Michelin",
}

_CONNECTOR_WORDS = {
    "de", "du", "des", "la", "le", "les", "of", "the", "and", "et",
    "in", "al", "da", "di", "von", "van", "sur", "en",
    "alla", "della", "au", "aux",
}

_MAX_ENTITY_WORDS = 4
_MAX_ENTITIES_PER_CHUNK = 3
_MAX_QUERY_ENTITIES = 3
_MAX_CHUNK_ENTITIES = 2

_ACCENTED_UPPER = r"A-ZÉÈÊËÔÛÙÎÏÇŒÀÂÄÆ"
_ACCENTED_LOWER = r"a-zéèêëôûùîïçœàâäæ"
_TRUNCATION_SUFFIXES = ("-", "–", "'", "’")

_WORD_TOKEN = re.compile(
    rf"[{_ACCENTED_UPPER}][{_ACCENTED_LOWER}{_ACCENTED_UPPER}'’\-]*"
    rf"|[{_ACCENTED_LOWER}]+"
)

# English/French possessive suffix ("Tokyo's" -> "Tokyo")
_POSSESSIVE_RE = re.compile(r"['’]s\b", re.IGNORECASE)


def clean_entity(entity: str) -> str:
    entity = entity.strip().strip("'’")

    question_prefixes = [
        "What is ", "What are ", "Where is ", "Where are ",
        "Who is ", "Who are ", "Tell me about ",
    ]
    for prefix in question_prefixes:
        if entity.startswith(prefix):
            entity = entity[len(prefix):]

    entity = re.sub(r"\s+", " ", entity.strip())
    entity = _POSSESSIVE_RE.sub("", entity).strip()

    while entity and entity[-1] in _TRUNCATION_SUFFIXES:
        entity = entity[:-1].strip()

    return entity


def is_bad_entity(entity: str) -> bool:
    return any(bad.lower() in entity.lower() for bad in _BAD_ENTITY_PATTERNS)


def _is_truncated(entity: str) -> bool:
    return len(entity) < 3


def _has_mojibake_fragment(entity: str) -> bool:
    """
    Catches artifacts like 'Mus C A' — a broken accented word split into
    single-letter tokens by the tokenizer. Any span containing a lone
    1-character word is almost certainly corrupted text, not a real entity.
    """
    return any(len(word) == 1 for word in entity.split(" "))


def _dedupe_substrings(entities: list[str]) -> list[str]:
    sorted_entities = sorted(entities, key=len, reverse=True)
    kept: list[str] = []
    for entity in sorted_entities:
        el = entity.lower()
        if not any(
            el != other.lower() and re.search(rf"\b{re.escape(el)}\b", other.lower())
            for other in kept
        ):
            kept.append(entity)
    order = {e: i for i, e in enumerate(entities)}
    kept.sort(key=lambda e: order[e])
    return kept


def extract_entity_candidates(text: str, limit: int = 10) -> list[str]:
    tokens = _WORD_TOKEN.findall(text)
    entities: list[str] = []
    i, n = 0, len(tokens)

    while i < n:
        tok = tokens[i]
        if not tok[0].isupper():
            i += 1
            continue

        span = [tok]
        j = i + 1
        while j < n and len(span) < _MAX_ENTITY_WORDS:
            nxt = tokens[j]
            if nxt[0].isupper():
                span.append(nxt)
                j += 1
            elif nxt.lower() in _CONNECTOR_WORDS and j + 1 < n and tokens[j + 1][0].isupper():
                span.append(nxt)
                span.append(tokens[j + 1])
                j += 2
            else:
                break

        candidate = clean_entity(" ".join(span))
        first_word = candidate.split(" ")[0] if candidate else ""

        if (
            candidate
            and candidate not in _STOPWORDS
            and not _is_truncated(candidate)
            and not is_bad_entity(candidate)
            and not _has_mojibake_fragment(candidate)
            and first_word not in _BAD_FIRST_WORDS
            and candidate not in entities
        ):
            entities.append(candidate)

        i = j if j > i else i + 1

    entities = _dedupe_substrings(entities)
    return entities[:limit]


def extract_query_entities(query: str) -> list[str]:
    entities = extract_entity_candidates(query)

    known_patterns = [
        "eiffel tower", "arc de triomphe", "louvre", "notre dame",
        "seine", "colosseum", "pantheon", "tokyo tower",
        "italy", "france", "japan", "rome", "paris", "tokyo", "milan",
    ]
    query_lower = query.lower()
    for item in known_patterns:
        if item in query_lower:
            formatted = item.title()
            if formatted not in entities:
                entities.insert(0, formatted)

    return entities


class HybridRetriever:

    def __init__(self):
        self.vector = VectorSearch()
        self.graph = GraphSearch()

    def retrieve(self, query: str):
        print("🔍 Vector search...")
        chunks = self.vector.search(query)

        print("🧠 Extracting entities...")

        query_entities = extract_query_entities(query)
        db_entities = self.graph.find_known_entities_in_text(query)
        for e in db_entities:
            if e not in query_entities:
                query_entities.append(e)
        query_entities = query_entities[:_MAX_QUERY_ENTITIES]
        print("QUERY ENTITIES:", query_entities)

        # Collect raw chunk candidates first, uncapped
        raw_chunk_candidates: list[str] = []
        for c in chunks:
            candidates = extract_entity_candidates(c["text"])[:_MAX_ENTITIES_PER_CHUNK]
            for cand in candidates:
                if cand not in query_entities and cand not in raw_chunk_candidates:
                    raw_chunk_candidates.append(cand)

        # Verify against the real graph before spending a slot on a candidate.
        # This is what catches 'Mus C A' / 'Food In November Michelin' style
        # noise that survives regex filtering but doesn't exist as a node —
        # far more reliable than adding more pattern rules one at a time.
        verified = set(self.graph.verify_entities_exist(raw_chunk_candidates))
        chunk_entities = [c for c in raw_chunk_candidates if c in verified]

        chunk_entities = _dedupe_substrings(query_entities + chunk_entities)
        chunk_entities = [e for e in chunk_entities if e not in query_entities]
        chunk_entities = chunk_entities[:_MAX_CHUNK_ENTITIES]

        entity_names = list(dict.fromkeys(query_entities + chunk_entities))
        entity_names.sort(key=lambda x: x in GENERIC_ENTITIES)

        entity_names = [
            e for e in entity_names
            if e in query_entities or e not in GENERIC_ENTITIES
        ]

        print("FINAL GRAPH ENTITIES:", entity_names)

        if entity_names:
            print(f"🧠 Graph expansion ({len(entity_names)} entities)")
            graph_data = self.graph.expand_entities(entity_names)
            print("GRAPH RESULT:", graph_data)
        else:
            print("🧠 Graph expansion skipped")
            graph_data = []

        return {"chunks": chunks, "graph": graph_data}