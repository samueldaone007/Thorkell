from fastapi import APIRouter

from app.api.routes import (
    action_items,
    conversations,
    health,
    search,
    segments,
    speakers,
    tags,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(tags.router)
api_router.include_router(search.router)
api_router.include_router(conversations.router)
api_router.include_router(segments.router)
api_router.include_router(speakers.router)
api_router.include_router(action_items.router)
