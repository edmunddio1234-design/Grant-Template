"""
FOAM Grant Alignment Engine - API Routers

Exports all application routers for modular endpoint organization.
"""

from .boilerplate import router as boilerplate_router
from .rfp import router as rfp_router
from .crosswalk import router as crosswalk_router
from .plans import router as plans_router
from .dashboard import router as dashboard_router
from .ai_draft import router as ai_draft_router

__all__ = [
    "boilerplate_router",
    "rfp_router",
    "crosswalk_router",
    "plans_router",
    "dashboard_router",
    "ai_draft_router",
]
