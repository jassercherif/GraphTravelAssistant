import os
from dotenv import load_dotenv
load_dotenv()



COUNTRIES = {
    "France": ["Paris"],
    "Italy": ["Rome"],
    "Japan": ["Tokyo"]
}

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")