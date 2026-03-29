"""
Main FastAPI application for the simplified chat agent example.
"""

import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.routers.chat import router as chatrouter
from app.routers.sql_chat import router as sqlrouter
from app.agents.simple_agent import SimpleAgent
from app.agents.sql_agent import SimpleSQLAgent
from app.services.db_service import DatabaseService

logger = logging.getLogger("default-logger")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes shared runtime dependencies for the chat app.
    """
    logger.info("=" * 50)
    logger.info("Starting Simple Chat Agent API")
    logger.info("=" * 50)

    try:
        logger.info("Initializing simple chat agent...")
        app.state.chat_agent = SimpleAgent()
        logger.info("✓ Simple chat agent initialized")

        logger.info("Initializing SQL agent...")
        db_service = DatabaseService()
        if db_service.test_connection():
            logger.info("✓ Database connection verified")
        else:
            logger.warning("⚠ Database connection failed — SQL agent will start but queries may fail")
        app.state.sql_agent = SimpleSQLAgent(db_service=db_service)
        logger.info("✓ SQL agent initialized")

        app.state.metrics = {
            "chat_agent_access_count": 0,
            "sql_agent_access_count": 0,
            "startup_time_seconds": 0,
        }

        logger.info("=" * 50)
        logger.info("Application startup complete! Services ready.")
        logger.info("=" * 50)

        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    finally:
        logger.info("=" * 50)
        logger.info("Shutting down Simple Chat Agent API")
        logger.info("=" * 50)

        logger.info("Application shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Simple Chat Agent API",
    version="1.0.0",
    description="Minimal API for a tool-calling chat agent built with OpenAI API",
    lifespan=lifespan,
    redirect_slashes=False
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Cache-Control", "Content-Type", "Connection"]
)

app.include_router(chatrouter)
app.include_router(sqlrouter)

@app.get("/", tags=["home"])
def message():
    """
    Root endpoint.
    Returns welcome message with API information.
    """
    return HTMLResponse("""
    <html>
        <head>
            <title>Simple Chat Agent API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #2c3e50; }
                .info { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
                a { color: #3498db; text-decoration: none; }
            </style>
        </head>
        <body>
            <h1>Simple Chat Agent API</h1>
            <div class="info">
                <p><strong>Version:</strong> 1.0.0</p>
                <p><strong>Status:</strong> ✅ Running</p>
                <p><strong>Architecture:</strong> FastAPI + SimpleRAGAgent + SimpleSQLAgent</p>
                <p><strong>Purpose:</strong> Minimal example of tool-calling chat agents (RAG + Text-to-SQL)</p>
            </div>
            <h2>📚 Documentation</h2>
            <ul>
                <li><a href="/docs">Interactive API Documentation (Swagger UI)</a></li>
                <li><a href="/redoc">Alternative Documentation (ReDoc)</a></li>
            </ul>
            <h2>Core Features</h2>
            <ul>
                <li><strong>/chat/agent</strong> - Query the simple chat agent</li>
                <li><strong>/sql/agent</strong> - Query the database with natural language (Text-to-SQL)</li>
            </ul>
        </body>
    </html>
    """)

if __name__ == "__main__":
    # Configure uvicorn with optimized settings
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        workers=1,  # Single worker for development (can increase for production)
        timeout_keep_alive=120,  # Increased timeout for long-running operations
        limit_concurrency=100,  # Maximum number of concurrent connections
        backlog=2048,  # Maximum number of connections to queue
        log_level="info"
    )
