# Ociana chatbot + Jira routing

## Problem

- Managers receive issues from multiple projects (e.g. SLUMS) through informal channels.
- Many requests are repeatable (password reset, unlock, MFA, browser/session).
- The team wants help **inside Ociana**: AI handles the unified fixes; anything else becomes a **Jira ticket** for the right project.

## Decision

Ship a small FastAPI chatbot service under `ociana_chatbot/`:

1. Classify the message against playbooks.
2. Auto-fix when matched.
3. Otherwise create a Jira issue using project keyword mapping (`project_hint` + message text).

n8n is optional glue so Ociana can call a webhook without hosting custom network rules immediately.

## Out of scope for v1

- Live identity-provider password reset API (guidance only until IAM webhook exists).
- Claude-based classifier (settings reserved; rule-based classifier is default).
- Bidirectional Jira ↔ Ociana comment sync.
