from __future__ import annotations

import logging
import uuid

from .classifier import classify_message
from .jira_client import JiraClient, build_ticket_description, build_ticket_summary
from .models_config import PlaybookCatalog, ProjectMap
from .schemas import ActionType, ChatRequest, ChatResponse, TicketInfo

logger = logging.getLogger(__name__)


class ChatEngine:
    def __init__(
        self,
        *,
        playbooks: PlaybookCatalog,
        project_map: ProjectMap,
        jira: JiraClient,
        default_project_key: str,
    ) -> None:
        self.playbooks = playbooks
        self.project_map = project_map
        self.jira = jira
        self.default_project_key = default_project_key

    def handle(self, request: ChatRequest) -> ChatResponse:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        classification = classify_message(
            request.message,
            self.playbooks,
            force_ticket=request.force_ticket,
        )

        if classification.action == "clarify":
            return ChatResponse(
                action=ActionType.CLARIFY,
                reply=(
                    "I can help with common Ociana issues (password reset, account unlock, MFA) "
                    "or create a Jira ticket for your project team. "
                    "Please share a short description and the project name if you know it "
                    "(for example SLUMS), or say \"create a ticket\"."
                ),
                intent=classification.intent,
                conversation_id=conversation_id,
            )

        if classification.action == "auto_fix" and classification.playbook:
            playbook = classification.playbook
            steps_text = "\n".join(f"{i}. {step}" for i, step in enumerate(playbook.steps, 1))
            reply = (
                f"This looks like a **{playbook.title}** issue — try these steps first:\n\n"
                f"{steps_text}\n\n"
                f"{playbook.escalation_hint}\n"
                'If you still need help, reply with "create a ticket".'
            )
            return ChatResponse(
                action=ActionType.AUTO_FIX,
                reply=reply,
                intent=classification.intent,
                playbook_id=playbook.id,
                steps=list(playbook.steps),
                conversation_id=conversation_id,
            )

        return self._create_ticket(request, conversation_id, classification.intent)

    def _create_ticket(
        self,
        request: ChatRequest,
        conversation_id: str,
        intent: str | None,
    ) -> ChatResponse:
        route_text = " ".join(
            part for part in [request.project_hint or "", request.message] if part
        )
        project = self.project_map.resolve(route_text, fallback=self.default_project_key)
        project_key = project.key if project else self.default_project_key
        project_name = project.name if project else project_key

        summary = build_ticket_summary(request.message, project_name=project_name)
        description = build_ticket_description(
            message=request.message,
            user_email=request.user_email,
            user_name=request.user_name,
            conversation_id=conversation_id,
            intent=intent,
            metadata=request.metadata or None,
        )

        created = self.jira.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            labels=["ociana", intent or "general_issue"],
        )

        ticket = TicketInfo(
            key=created.key,
            url=created.url,
            project_key=created.project_key,
            summary=created.summary,
            dry_run=created.dry_run,
        )

        dry = " (dry-run — Jira not called)" if created.dry_run else ""
        link = f"\nOpen it here: {created.url}" if created.url else ""
        reply = (
            f"I created Jira ticket **{created.key}** in project **{project_name}**{dry}."
            f"{link}\n"
            "Your manager/team will see it in Jira. Reply here if you need to add more detail."
        )
        logger.info(
            "Created ticket %s for conversation=%s project=%s dry_run=%s",
            created.key,
            conversation_id,
            project_key,
            created.dry_run,
        )
        return ChatResponse(
            action=ActionType.CREATE_TICKET,
            reply=reply,
            intent=intent,
            ticket=ticket,
            conversation_id=conversation_id,
        )
