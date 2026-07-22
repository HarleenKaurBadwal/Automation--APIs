# Ociana support chatbot → Jira tickets

Managers were getting scattered issues across projects (for example **SLUMS**). The team wants users to ask for help inside **Ociana**, have the bot fix common / unified problems (password, unlock, MFA, session glitches), and otherwise **create a Jira ticket** in the right project.

## What this does

```text
Ociana user message
        │
        ▼
  Chatbot API (/v1/chat)
        │
        ├── password / unlock / MFA / cache  → guided auto-fix steps
        ├── unclear short message            → ask for project + detail
        └── everything else / "create ticket" → Jira issue in mapped project
```

## Layout

| Path | Purpose |
|------|---------|
| `src/ociana_chatbot/` | FastAPI service |
| `config/playbooks.json` | Auto-fix playbooks (password, unlock, …) |
| `config/project_map.json` | Project keyword → Jira project key (SLUMS, PORT, …) |
| `n8n/ociana-chatbot-jira.workflow.json` | Optional webhook bridge into the API |
| `tests/test_chatbot.py` | Unit/API tests (Jira dry-run) |

## Quick start

```bash
cd ociana_chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env — leave JIRA_DRY_RUN=true until credentials are ready

PYTHONPATH=src python -m ociana_chatbot
```

Health check:

```bash
curl -s http://127.0.0.1:8080/health
```

Chat examples:

```bash
# Auto-fix password guidance
curl -s http://127.0.0.1:8080/v1/chat \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Key: change-me' \
  -d '{"message":"I forgot my Ociana password"}'

# Create a ticket for a project issue (routes to SLUMS)
curl -s http://127.0.0.1:8080/v1/chat \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Key: change-me' \
  -d '{
    "message":"SLUMS dashboard map layer is blank for vessel XYZ",
    "user_email":"user@gsts.ca",
    "user_name":"Alex"
  }'

# Force a ticket even if a playbook matches
curl -s http://127.0.0.1:8080/v1/tickets \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Key: change-me' \
  -d '{"message":"password reset email never arrives","project_hint":"AUTH"}'
```

## Configure Jira

1. Create an Atlassian API token for a bot user.
2. Set in `.env`:

```bash
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_EMAIL=bot@your-org.com
JIRA_API_TOKEN=...
JIRA_DEFAULT_PROJECT_KEY=SUP
JIRA_ISSUE_TYPE=Task
JIRA_DRY_RUN=false
```

3. Update `config/project_map.json` so aliases match real Jira project keys your managers use.

## Wire into Ociana

Options:

1. **Direct** — Ociana chat widget / backend POSTs to `/v1/chat` with `X-Api-Key`.
2. **n8n** — Import `n8n/ociana-chatbot-jira.workflow.json`, set `OCIANA_CHATBOT_URL` and `OCIANA_CHATBOT_API_KEY`, point Ociana at the n8n webhook.

Suggested request body from Ociana:

```json
{
  "message": "user text",
  "user_email": "user@gsts.ca",
  "user_name": "Display Name",
  "project_hint": "SLUMS",
  "conversation_id": "ociana-thread-id",
  "metadata": { "ociana_org_id": "..." }
}
```

Response `action` is one of:

- `auto_fix` — show `reply` + `steps` in the chat UI
- `create_ticket` — show `reply`; `ticket.key` / `ticket.url` for deep link
- `clarify` — ask the user for more detail

## Tests

```bash
cd ociana_chatbot
PYTHONPATH=src pytest -q
```

## Next steps (optional)

- Turn on `USE_CLAUDE_CLASSIFIER` once Anthropic routing is approved (hook already reserved in settings).
- Add real password-reset / unlock automation webhooks per playbook instead of guidance-only steps.
- Sync Jira comment threads back into the Ociana conversation id.
