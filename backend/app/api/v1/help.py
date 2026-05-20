
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.services.help_service import help_service

router = APIRouter()

@router.get("/", response_model=List[Dict[str, str]])
async def list_help_articles():
    """List all available help articles."""
    return help_service.list_articles()

@router.get("/{article_id}", response_model=Dict[str, str])
async def get_help_article(article_id: str):
    """Get the content of a specific help article."""
    content = help_service.get_article(article_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return {
        "id": article_id,
        "title": article_id.replace("_", " ").title(),
        "content": content
    }
