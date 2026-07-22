from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ociana_chatbot.app import create_app
from ociana_chatbot.classifier import classify_message
from ociana_chatbot.engine import ChatEngine
from ociana_chatbot.jira_client import JiraClient, build_ticket_summary
from ociana_chatbot.models_config import load_playbooks, load_project_map
from ociana_chatbot.schemas import ActionType, ChatRequest
from ociana_chatbot.settings import Settings


CONFIG = ROOT / "config"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        OCIANA_CHATBOT_API_KEY="test-key",
        JIRA_DRY_RUN=True,
        JIRA_DEFAULT_PROJECT_KEY="SUP",
        PROJECT_MAP_PATH=str(CONFIG / "project_map.json"),
        PLAYBOOKS_PATH=str(CONFIG / "playbooks.json"),
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    return TestClient(app)


@pytest.fixture
def engine(settings: Settings) -> ChatEngine:
    return ChatEngine(
        playbooks=load_playbooks(settings.playbooks_path),
        project_map=load_project_map(settings.project_map_path),
        jira=JiraClient(
            base_url="https://example.atlassian.net",
            email="bot@example.com",
            api_token="token",
            dry_run=True,
        ),
        default_project_key=settings.jira_default_project_key,
    )


def test_password_is_auto_fix(engine: ChatEngine) -> None:
    response = engine.handle(
        ChatRequest(message="I forgot my password and can't log into Ociana")
    )
    assert response.action == ActionType.AUTO_FIX
    assert response.playbook_id == "password_reset"
    assert response.steps
    assert response.ticket is None


def test_slums_issue_creates_ticket_in_slums(engine: ChatEngine) -> None:
    response = engine.handle(
        ChatRequest(
            message="Map layer is missing for the SLUMS project dashboard",
            user_email="user@gsts.ca",
            user_name="Alex",
        )
    )
    assert response.action == ActionType.CREATE_TICKET
    assert response.ticket is not None
    assert response.ticket.project_key == "SLUMS"
    assert response.ticket.dry_run is True
    assert "SLUMS-DRY" in response.ticket.key


def test_force_ticket_skips_playbook(engine: ChatEngine) -> None:
    response = engine.handle(
        ChatRequest(
            message="password reset still failing after email",
            force_ticket=True,
            project_hint="AUTH",
        )
    )
    assert response.action == ActionType.CREATE_TICKET
    assert response.ticket is not None
    assert response.ticket.project_key == "AUTH"


def test_clarify_short_message(engine: ChatEngine) -> None:
    response = engine.handle(ChatRequest(message="help"))
    assert response.action == ActionType.CLARIFY


def test_explicit_create_ticket_phrase(engine: ChatEngine) -> None:
    catalog = load_playbooks(CONFIG / "playbooks.json")
    result = classify_message("please create a ticket for this", catalog)
    assert result.action == "create_ticket"


def test_project_alias_resolution() -> None:
    project_map = load_project_map(CONFIG / "project_map.json")
    project = project_map.resolve("vessel AIS feed is stale")
    assert project is not None
    assert project.key == "VES"


def test_ticket_summary_truncation() -> None:
    summary = build_ticket_summary("x" * 500, project_name="SLUMS")
    assert summary.startswith("[SLUMS] ")
    assert len(summary) <= 255


def test_health_and_chat_api(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    denied = client.post("/v1/chat", json={"message": "forgot password"})
    # default settings fixture uses api key; missing header should 401
    assert denied.status_code == 401

    ok = client.post(
        "/v1/chat",
        json={"message": "forgot password for ociana"},
        headers={"X-Api-Key": "test-key"},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["action"] == "auto_fix"
    assert body["playbook_id"] == "password_reset"


def test_tickets_endpoint_forces_jira(client: TestClient) -> None:
    response = client.post(
        "/v1/tickets",
        json={
            "message": "forgot password but still broken",
            "project_hint": "slums",
            "user_email": "mgr@gsts.ca",
        },
        headers={"X-Api-Key": "test-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "create_ticket"
    assert body["ticket"]["project_key"] == "SLUMS"
