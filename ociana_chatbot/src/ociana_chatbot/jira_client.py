from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CreatedIssue:
    key: str
    url: str | None
    project_key: str
    summary: str
    dry_run: bool = False
    raw: dict[str, Any] | None = None


class JiraClient:
    """Minimal Jira Cloud REST client for creating support tickets."""

    def __init__(
        self,
        *,
        base_url: str,
        email: str,
        api_token: str,
        issue_type: str = "Task",
        dry_run: bool = True,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.issue_type = issue_type
        self.dry_run = dry_run
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.email and self.api_token)

    def create_issue(
        self,
        *,
        project_key: str,
        summary: str,
        description: str,
        labels: list[str] | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> CreatedIssue:
        summary = summary.strip()[:255] or "Ociana support request"
        labels = labels or []

        if self.dry_run or not self.configured:
            fake_key = f"{project_key.upper()}-DRY"
            url = f"{self.base_url}/browse/{fake_key}" if self.base_url else None
            logger.info(
                "Jira dry-run create_issue project=%s summary=%r",
                project_key,
                summary,
            )
            return CreatedIssue(
                key=fake_key,
                url=url,
                project_key=project_key.upper(),
                summary=summary,
                dry_run=True,
                raw={"dry_run": True, "description": description},
            )

        payload: dict[str, Any] = {
            "fields": {
                "project": {"key": project_key.upper()},
                "summary": summary,
                "issuetype": {"name": self.issue_type},
                "description": self._adf_doc(description),
                "labels": ["ociana-chatbot", *labels],
            }
        }
        if extra_fields:
            payload["fields"].update(extra_fields)

        url = f"{self.base_url}/rest/api/3/issue"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                url,
                json=payload,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        key = data["key"]
        browse = f"{self.base_url}/browse/{key}"
        return CreatedIssue(
            key=key,
            url=browse,
            project_key=project_key.upper(),
            summary=summary,
            dry_run=False,
            raw=data,
        )

    @staticmethod
    def _adf_doc(text: str) -> dict[str, Any]:
        """Atlassian Document Format paragraph for Jira Cloud description."""
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        if not paragraphs:
            paragraphs = ["(no description)"]
        content = [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": paragraph}],
            }
            for paragraph in paragraphs
        ]
        return {"type": "doc", "version": 1, "content": content}


def build_ticket_summary(message: str, project_name: str | None = None) -> str:
    prefix = f"[{project_name}] " if project_name else "[Ociana] "
    cleaned = " ".join(message.strip().split())
    body = cleaned[: 255 - len(prefix)]
    return f"{prefix}{body}"


def build_ticket_description(
    *,
    message: str,
    user_email: str | None,
    user_name: str | None,
    conversation_id: str | None,
    intent: str | None,
    metadata: dict[str, Any] | None = None,
) -> str:
    lines = [
        "Ticket created automatically by the Ociana support chatbot.",
        "",
        f"Reporter name: {user_name or 'unknown'}",
        f"Reporter email: {user_email or 'unknown'}",
        f"Conversation id: {conversation_id or 'n/a'}",
        f"Detected intent: {intent or 'n/a'}",
        "",
        "User message:",
        message.strip(),
    ]
    if metadata:
        lines.extend(["", "Metadata:"])
        for key, value in metadata.items():
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)
