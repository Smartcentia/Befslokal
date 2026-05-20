from fastapi import APIRouter
from app.domains.innsikt.routers.agent import chat_endpoint, ChatRequest, ChatResponse

# Legacy Bridge for Frontend Compatibility
# The frontend calls /api/v1/ai/assistant/chat
# We map this to the modern Agent implementation

router = APIRouter()

# Register the endpoint using the new implementation
router.add_api_route(
    "/chat", 
    chat_endpoint, 
    methods=["POST"], 
    response_model=ChatResponse, 
    name="Legacy AI Chat"
)
