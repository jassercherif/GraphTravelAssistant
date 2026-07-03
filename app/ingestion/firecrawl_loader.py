from firecrawl import FirecrawlApp
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

#from config import FIRECRAWL_API_KEY
from app.core.config import FIRECRAWL_API_KEY

app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

def load_page(url: str) -> str:
    """
    Fetch clean markdown text from Firecrawl
    """

    try:
        result = app.scrape(url, formats=["markdown"])
    except Exception as e:
        print(f"❌ Firecrawl error for {url}: {e}")
        return ""

    if not result:
        return ""

    if hasattr(result, "markdown") and result.markdown:
        return result.markdown

    if hasattr(result, "data") and result.data:
        return result.data.get("markdown", "")

    return ""