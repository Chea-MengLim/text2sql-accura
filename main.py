from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.database import router as database_router
from api.nl2sql import router as nl2sql_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NL2SQL API",
    description="Natural Language to SQL API with LangChain and HuggingFace",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(database_router)
app.include_router(nl2sql_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NL2SQL API is running",
        "version": "1.0.0",
        "endpoints": {
            "database": "/api/database/",
            "nl2sql": "/api/nl2sql/",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "nl2sql-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)