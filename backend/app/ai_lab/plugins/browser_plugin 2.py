from semantic_kernel.functions import kernel_function
from typing import Annotated, Dict, Any, List
import requests
import time
from bs4 import BeautifulSoup

class BrowserPlugin:
    """
    A plugin for browsing web pages, extracting content, and performing basic QA checks.
    Designed for Environment-Aware Execution (can reach internal or public URLs).
    """

    @kernel_function(
        name="fetch_page",
        description="Fetches the HTML content and metadata of a URL."
    )
    def fetch_page(
        self, 
        url: Annotated[str, "The URL to fetch"]
    ) -> Annotated[Dict[str, Any], "Dictionary containing status, time, and html"]:
        start_time = time.time()
        try:
            response = requests.get(url, timeout=10)
            duration = time.time() - start_time
            
            return {
                "status": response.status_code,
                "url": response.url,
                "load_time_ms": int(duration * 1000),
                "html": response.text[:50000], # Limit size for AI context
                "size_bytes": len(response.content)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "load_time_ms": 0
            }

    @kernel_function(
        name="check_accessibility",
        description="Analyzes HTML for basic accessibility issues (Missing Alt, Empty Buttons)."
    )
    def check_accessibility(
        self, 
        html: Annotated[str, "The HTML content to analyze"]
    ) -> Annotated[Dict[str, Any], "Report of accessibility issues"]:
        soup = BeautifulSoup(html, 'html.parser')
        issues = []
        
        # 1. Images without alt
        images = soup.find_all('img')
        missing_alt = [img.get('src', 'unknown') for img in images if not img.get('alt')]
        if missing_alt:
            issues.append(f"Found {len(missing_alt)} images missing 'alt' text.")

        # 2. Empty Buttons
        buttons = soup.find_all('button')
        empty_buttons = [str(btn)[:50] for btn in buttons if not btn.get_text(strip=True) and not btn.get('aria-label')]
        if empty_buttons:
            issues.append(f"Found {len(empty_buttons)} buttons with no text or aria-label.")

        # 3. Form Inputs without labels
        # Simple heuristic
        inputs = soup.find_all('input')
        # This is harder to check robustly with just BS4, skipping for MVP.

        score = 100 - (len(issues) * 10)
        return {
            "score": max(0, score),
            "issues": issues,
            "checked_elements": len(images) + len(buttons)
        }

    @kernel_function(
        name="extract_text",
        description="Extracts clean, readable text from HTML for AI analysis."
    )
    def extract_text(
        self, 
        html: Annotated[str, "The HTML content"]
    ) -> Annotated[str, "Clean text content"]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "noscript"]):
            script.decompose()

        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
