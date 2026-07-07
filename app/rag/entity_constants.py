# Entities that are valid but too broad to expand on their own — they show
# up in almost every chunk, so alone (as chunk noise) they add no signal.
# If the USER explicitly asks about one (query entity), it's not noise.
GENERIC_ENTITIES = {
    "Paris", "France", "Italy", "Tokyo", "Japan", "Rome",
}