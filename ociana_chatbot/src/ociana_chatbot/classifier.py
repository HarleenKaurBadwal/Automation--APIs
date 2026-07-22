from __future__ import annotations

import re
from dataclasses import dataclass

from .models_config import Playbook, PlaybookCatalog


TICKET_PHRASES = (
    "create a ticket",
    "create ticket",
    "open a ticket",
    "open ticket",
    "file a ticket",
    "raise a ticket",
    "jira",
    "escalate",
    "talk to a human",
    "speak to someone",
    "need support",
)

CLARIFY_TOO_SHORT = 12


@dataclass
class Classification:
    intent: str
    action: str  # auto_fix | create_ticket | clarify
    playbook: Playbook | None = None
    confidence: float = 0.0
    reason: str = ""


def _wants_ticket(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in TICKET_PHRASES)


def classify_message(
    message: str,
    catalog: PlaybookCatalog,
    *,
    force_ticket: bool = False,
) -> Classification:
    text = message.strip()
    if force_ticket or _wants_ticket(text):
        playbook = catalog.match(text)
        return Classification(
            intent=playbook.id if playbook else "manual_escalation",
            action="create_ticket",
            playbook=playbook,
            confidence=0.95 if force_ticket else 0.9,
            reason="User requested a ticket or escalation.",
        )

    playbook = catalog.match(text)
    if playbook and playbook.auto_fixable:
        return Classification(
            intent=playbook.id,
            action="auto_fix",
            playbook=playbook,
            confidence=0.85,
            reason=f"Matched playbook {playbook.id}.",
        )

    # Very short / vague messages — ask for project + symptom before ticket spam
    compact = re.sub(r"\s+", " ", text)
    if len(compact) < CLARIFY_TOO_SHORT and not playbook:
        return Classification(
            intent="unclear",
            action="clarify",
            confidence=0.4,
            reason="Message too short to route safely.",
        )

    return Classification(
        intent="general_issue",
        action="create_ticket",
        playbook=playbook,
        confidence=0.7,
        reason="No auto-fix playbook matched; create a Jira ticket for the project team.",
    )
