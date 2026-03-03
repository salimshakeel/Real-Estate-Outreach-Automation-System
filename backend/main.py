"""
Real Estate Outreach Automation System - Main Application
FastAPI entry point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db

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
    print(
        f"📧 SendGrid:         {'✅ Configured' if settings.sendgrid_configured else '⚠️  Not configured (demo mode)'}"
    )
    print(
        f"🔒 Webhook Secret:   {'✅ Set' if settings.webhook_secret_configured else '⚠️  Not set (webhook unprotected in dev)'}"
    )
    print(
        f"📬 Daily Send Limit: {settings.SENDGRID_DAILY_SEND_LIMIT if settings.SENDGRID_DAILY_SEND_LIMIT > 0 else 'Unlimited'}"
    )
    print(f"🤖 OpenAI: {'✅ Configured' if settings.openai_configured else '⚠️ Not configured (demo mode)'}")
    print(f"📱 Twilio SMS: {'✅ Configured' if settings.twilio_configured else '⚠️ Not configured (demo mode)'}")
    print(f"🎙️ Voice (Retell): {'✅ Configured' if settings.retell_configured else '⚠️ Not configured (demo mode)'}")
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
# Always allow Render frontend; merge with any env CORS_ORIGINS
FRONTEND_ORIGIN_RENDER = "https://real-estate-outreach-frontend.onrender.com"
_cors_origins = list(settings.cors_origins_list)
if FRONTEND_ORIGIN_RENDER not in _cors_origins:
    _cors_origins.append(FRONTEND_ORIGIN_RENDER)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.APP_ENV, "debug": settings.DEBUG}


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
            "twilio_sms": settings.twilio_configured,
            "retell_voice": settings.retell_configured,
            "openai": settings.openai_configured,
            "calendly": settings.calendly_configured,
        },
        "cors_origins": settings.cors_origins_list,
    }


# ============================================
# INCLUDE ROUTERS
# ============================================
from app.routers.campaigns import router as campaigns_router
from app.routers.chatbot import router as chatbot_router
from app.routers.dashboard import router as dashboard_router
from app.routers.demo import router as demo_router
from app.routers.leads import router as leads_router
from app.routers.sendgrid_webhook import router as sendgrid_webhook_router
from app.routers.sms import router as sms_router
from app.routers.templates import router as templates_router
from app.routers.voice import router as voice_router

app.include_router(leads_router, prefix="/api/leads", tags=["Leads"])
app.include_router(templates_router, prefix="/api/templates", tags=["Templates"])
app.include_router(campaigns_router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(demo_router, prefix="/api/demo", tags=["Demo"])
app.include_router(chatbot_router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(sms_router, prefix="/api/sms", tags=["SMS"])
app.include_router(voice_router, prefix="/api/voice", tags=["Voice"])
app.include_router(sendgrid_webhook_router, prefix="/webhooks", tags=["Webhooks"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # Auto-reload in debug mode
    )
