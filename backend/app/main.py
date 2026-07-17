"""
Lead Qualification & Outreach Agent - FastAPI Application Entry Point.
Initializes the database, configures CORS, and registers all API routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.routes import router

# Initialize the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Automated lead qualification and outreach agent with human approval gate. "
                "Processes leads through enrichment, identity-blind scoring, classification, "
                "routing, email drafting, and human approval workflow.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS - allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router, prefix="/api/v1", tags=["Leads"])


@app.on_event("startup")
async def startup_event():
    """Initialize the database on application startup."""
    init_db()
    print(f"[OK] {settings.APP_NAME} v{settings.APP_VERSION} initialized")
    print(f"   Database: {settings.DATABASE_URL}")
    print(f"   LLM Model: {settings.LLM_MODEL}")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )