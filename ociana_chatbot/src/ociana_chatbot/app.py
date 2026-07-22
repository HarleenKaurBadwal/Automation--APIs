from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status

from . import __version__
from .engine import ChatEngine
from .jira_client import JiraClient
from .models_config import load_playbooks, load_project_map
from .schemas import ChatRequest, ChatResponse, HealthResponse
from .settings import Settings, get_settings

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    playbooks = load_playbooks(settings.playbooks_path)
    project_map = load_project_map(settings.project_map_path)
    jira = JiraClient(
        base_url=settings.jira_base_url,
        email=settings.jira_email,
        api_token=settings.jira_api_token,
        issue_type=settings.jira_issue_type,
        dry_run=settings.jira_dry_run,
    )
    engine = ChatEngine(
        playbooks=playbooks,
        project_map=project_map,
        jira=jira,
        default_project_key=settings.jira_default_project_key,
    )

    app = FastAPI(
        title="Ociana Support Chatbot",
        description=(
            "AI-assisted Ociana helper that auto-resolves common issues "
            "(password, unlock, MFA) and creates Jira tickets for project teams."
        ),
        version=__version__,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.jira = jira

    def require_api_key(
        x_api_key: Annotated[str | None, Header()] = None,
    ) -> None:
        expected = settings.api_key
        if not expected or expected == "change-me":
            # Allow local/demo without forcing auth when default key is unchanged,
            # but still accept a matching key if sent.
            return
        if x_api_key != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-Api-Key",
            )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            jira_configured=jira.configured,
            jira_dry_run=jira.dry_run,
            version=__version__,
        )

    @app.post("/v1/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
    def chat(body: ChatRequest) -> ChatResponse:
        return engine.handle(body)

    @app.post(
        "/v1/tickets",
        response_model=ChatResponse,
        dependencies=[Depends(require_api_key)],
    )
    def create_ticket(body: ChatRequest) -> ChatResponse:
        forced = body.model_copy(update={"force_ticket": True})
        return engine.handle(forced)

    return app


app = create_app()
