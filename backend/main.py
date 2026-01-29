"""
Real Estate Outreach Automation System - Main Application
FastAPI entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db

# Get settings
settings = get_settings()


# ============================================
# LIFESPAN - Startup & Shutdown Events
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.
    - Startup: Initialize database tables
    - Shutdown: Close database connections
    """
    # STARTUP
    print("🚀 Starting up...")
    print(f"📦 App: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"🌍 Environment: {settings.APP_ENV}")
    print(f"🐛 Debug: {settings.DEBUG}")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized!")
    
    # Check services
    print(f"📧 SendGrid: {'✅ Configured' if settings.sendgrid_configured else '⚠️ Not configured (demo mode)'}")
    print(f"🤖 OpenAI: {'✅ Configured' if settings.openai_configured else '⚠️ Not configured (demo mode)'}")
    print(f"📅 Calendly: {'✅ Configured' if settings.calendly_configured else '⚠️ Not configured (demo mode)'}")
    
    print("=" * 50)
    print(f"🌐 API running at: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 50)
    
    yield  # App runs here
    
    # SHUTDOWN
    print("👋 Shutting down...")
    await close_db()
    print("✅ Database connections closed!")


# ============================================
# FASTAPI APP
# ============================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Automated email outreach platform for real estate agents",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ============================================
# CORS MIDDLEWARE
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API info"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG
    }


@app.get("/config", tags=["Health"])
async def config_check():
    """Check configuration status (no secrets exposed)"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {
            "database": True,  # Always true if app is running
            "sendgrid": settings.sendgrid_configured,
            "openai": settings.openai_configured,
            "calendly": settings.calendly_configured
        },
        "cors_origins": settings.cors_origins_list
    }


# ============================================
# INCLUDE ROUTERS (will add as we build them)
# ============================================
# from app.routers import leads, campaigns, dashboard, templates, webhooks
# 
# app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
# app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
# app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
# app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
# app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


# ============================================
# RUN SERVER
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # Auto-reload in debug mode
    )
