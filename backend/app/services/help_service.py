import os
from pathlib import Path
from typing import List, Dict

HELP_DIR = Path(__file__).parent.parent / "static" / "help"

class HelpService:
    def __init__(self):
        # Path resolution strategies (prioritized):
        # 1. backend/docs – alltid tilgjengelig når app kjører fra backend (Render, lokal)
        # 2. Project root docs/ – docs/BRUKERHJELP.md i repo
        # 3. Container /app/docs – Docker-deploy
        backend_docs = Path(__file__).resolve().parent.parent.parent / "docs"
        project_root_docs = Path(__file__).resolve().parent.parent.parent.parent / "docs"
        container_docs = Path("/app/docs")

        for candidate in (backend_docs, project_root_docs, container_docs):
            help_file = candidate / "BRUKERHJELP.md"
            if help_file.exists():
                self.help_dir = candidate
                break
        else:
            self.help_dir = Path("docs").resolve()
             
        # print(f"Help Service using docs path: {self.help_dir}")

    def get_structured_help(self) -> List[Dict[str, str]]:
        """Parses BRUKERHJELP.md into structured sections."""
        help_file = self.help_dir / "BRUKERHJELP.md"
        if not help_file.exists():
            return []

        content = help_file.read_text(encoding="utf-8")
        sections = []
        
        # Split by H2 headers (## )
        # Using a simple regex split or line processing
        import re
        parts = re.split(r'^##\s+(.+)$', content, flags=re.MULTILINE)
        
        # parts[0] is the preamble/title before the first ##
        # parts[1] is the first title, parts[2] is first content
        # parts[3] is second title, parts[4] is second content, etc.
        
        for i in range(1, len(parts), 2):
            title = parts[i].strip()
            body = parts[i+1].strip()
            
            # Create an ID from title
            section_id = title.lower().replace(" ", "-").replace("æ", "ae").replace("ø", "o").replace("å", "a").replace(",", "")
            
            # Determine category based on title
            category = "User"
            if title in ["Technical", "Admin", "Systemarkitektur"]:
                category = "Technical"
            
            sections.append({
                "id": section_id,
                "title": title,
                "content": body,
                "category": category
            })
            
        return sections

    def list_articles(self) -> List[Dict[str, str]]:
        """List all available markdown help articles with categorization."""
        # STRICTLY return only the structured pedagogical content from BRUKERHJELP.md
        # This filters out all loose technical files to ensure a clean, pedagogical user experience.
        return self.get_structured_help()

    def get_article(self, article_id: str) -> str:
        """Get the content of a help article."""
        # First check if it's a section in BRUKERHJELP.md
        sections = self.get_structured_help()
        for sec in sections:
            if sec["id"] == article_id:
                return sec["content"]
        
        # Then check file
        file_path = self.help_dir / f"{article_id}.md"
        if not file_path.exists():
            return None
        return file_path.read_text(encoding="utf-8")

    def save_article(self, filename: str, content: str):
        """Helper to save/update an article (useful for integration)."""
        file_path = self.help_dir / filename
        file_path.write_text(content, encoding="utf-8")

help_service = HelpService()
