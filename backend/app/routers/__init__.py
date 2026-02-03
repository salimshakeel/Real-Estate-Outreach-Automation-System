"""
API Routers
"""

from app.routers.leads import router as leads_router
from app.routers.templates import router as templates_router
from app.routers.campaigns import router as campaigns_router
from app.routers.dashboard import router as dashboard_router
from app.routers.demo import router as demo_router

__all__ = ["leads_router", "templates_router", "campaigns_router", "dashboard_router", "demo_router"]
