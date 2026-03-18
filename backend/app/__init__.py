import os

from flask import Flask
from flask_cors import CORS

from app.agent.graph import JobMatchAgent
from app.config import Settings
from app.routes import api_bp
from app.services.sqlite_service import SQLiteService
from app.tools.db_tool import DBTool
from app.tools.jd_scorer import JDScorerTool
from app.tools.web_search import WebSearchTool


def create_app() -> Flask:
    app = Flask(__name__)
    settings = Settings()

    app.config["DEBUG"] = settings.DEBUG
    app.config["FLASK_PORT"] = settings.FLASK_PORT

    # Allow configured frontend origin, local dev, and Vercel preview URLs.
    extra_origins_env = os.getenv("FRONTEND_ORIGINS", "")
    extra_origins = [item.strip() for item in extra_origins_env.split(",") if item.strip()]
    allowed_origins = [
        settings.FRONTEND_ORIGIN,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        r"https://.*\.vercel\.app",
        *extra_origins,
    ]

    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": allowed_origins}},
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    sqlite_service = SQLiteService(str(settings.resolved_db_path))
    db_tool = DBTool(sqlite_service=sqlite_service)
    web_search_tool = WebSearchTool(api_key=settings.TAVILY_API_KEY)
    jd_scorer_tool = JDScorerTool(
        model=settings.GEMINI_MODEL,
        api_key=settings.GOOGLE_API_KEY,
        temperature=settings.GEMINI_TEMPERATURE,
    )

    agent = JobMatchAgent(
        google_api_key=settings.GOOGLE_API_KEY,
        gemini_model=settings.GEMINI_MODEL,
        gemini_temp=settings.GEMINI_TEMPERATURE,
        max_iterations=settings.MAX_AGENT_ITERATIONS,
        web_search_tool=web_search_tool,
        jd_scorer_tool=jd_scorer_tool,
        db_tool=db_tool,
    )

    app.config["JOBMATCH_AGENT"] = agent
    app.config["DB_TOOL"] = db_tool

    app.register_blueprint(api_bp)
    return app
