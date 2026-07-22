from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    AUTO_FIX = "auto_fix"
    CREATE_TICKET = "create_ticket"
    CLARIFY = "clarify"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    user_email: str | None = None
    user_name: str | None = None
    project_hint: str | None = Field(
        default=None,
        description="Optional project name/key from Ociana context (e.g. SLUMS).",
    )
    conversation_id: str | None = None
    force_ticket: bool = Field(
        default=False,
        description="Skip auto-fix and always create a Jira ticket.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class TicketInfo(BaseModel):
    key: str
    url: str | None = None
    project_key: str
    summary: str
    dry_run: bool = False


class ChatResponse(BaseModel):
    action: ActionType
    reply: str
    intent: str | None = None
    playbook_id: str | None = None
    steps: list[str] = Field(default_factory=list)
    ticket: TicketInfo | None = None
    conversation_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    jira_configured: bool
    jira_dry_run: bool
    version: str
