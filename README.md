# Automation--APIs

Automation scaffold for a CSV-uploaded report that combines data from Aha,
GitLab, QuickBooks, and later Claude, then saves the generated Excel workbook
to OneDrive through n8n.

## What is included

- `src/report_runner.py` - n8n-friendly Python entrypoint.
  - Accepts an uploaded CSV path.
  - Calls your existing report script when `REPORT_COMMAND` is set.
  - Creates a basic Excel workbook when `REPORT_COMMAND` is not set, so the
    workflow can be smoke-tested before the production script is copied in.
- `n8n/csv-to-excel-onedrive.workflow.json` - importable n8n workflow template.
- `scripts/example_report_script.py` - example interface for your existing
  Aha/GitLab/QuickBooks script.
- `Dockerfile.n8n` and `docker-compose.n8n.yml` - optional self-hosted n8n
  runtime with Python dependencies installed.
- `.env.example` - environment variable template for local/self-hosted runs.

## Expected flow

1. A CSV file is uploaded to the n8n webhook.
2. n8n writes the uploaded CSV to `/tmp`.
3. n8n runs:

   ```bash
   python3 /workspace/src/report_runner.py \
     --input-csv "/tmp/input-<execution-id>.csv" \
     --output-xlsx "/tmp/report-<execution-id>.xlsx"
   ```

4. `report_runner.py` runs your configured report command.
5. n8n reads the generated `.xlsx` file.
6. n8n uploads the workbook to OneDrive.
7. The webhook returns an upload result.

## Add your existing Python report script

Copy your current Aha/GitLab/QuickBooks script into `scripts/` or mount it into
the n8n container. The easiest integration is to make it accept:

```bash
--input-csv /path/to/uploaded.csv
--output-xlsx /path/to/report.xlsx
```

Then set `REPORT_COMMAND` in `.env`:

```bash
REPORT_COMMAND=python3 scripts/your_existing_report.py --input-csv {input_csv} --output-xlsx {output_xlsx}
REPORT_WORKDIR=/tmp/n8n-reports
```

The runner replaces these placeholders:

- `{input_csv}` - uploaded CSV file path from n8n
- `{output_xlsx}` - destination path for the Excel workbook
- `{workdir}` - working directory for temporary files

It also exports these environment variables for scripts that prefer env vars:

- `INPUT_CSV`
- `OUTPUT_XLSX`
- `REPORT_WORKDIR`

## Local smoke test

Install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run without `REPORT_COMMAND` to verify Excel generation:

```bash
printf 'name,amount\nexample,123\n' > /tmp/input.csv
python3 src/report_runner.py \
  --input-csv /tmp/input.csv \
  --output-xlsx /tmp/report.xlsx
```

Run with the example adapter:

```bash
REPORT_COMMAND='python3 scripts/example_report_script.py --input-csv {input_csv} --output-xlsx {output_xlsx}' \
python3 src/report_runner.py \
  --input-csv /tmp/input.csv \
  --output-xlsx /tmp/report.xlsx
```

## n8n setup

### Option A: Use the provided Docker Compose file

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Fill in your Aha, GitLab, and QuickBooks variables.
3. Start n8n:

   ```bash
   docker compose -f docker-compose.n8n.yml up --build
   ```

4. Open <http://localhost:5678>.
5. Import `n8n/csv-to-excel-onedrive.workflow.json`.

### Option B: Existing n8n instance

Make sure the n8n worker that runs the **Execute Command** node has:

- access to this repository at `/workspace`, or update the workflow command path
- Python 3
- dependencies from `requirements.txt`
- the environment variables from `.env.example`

## OneDrive setup in n8n

1. In n8n, create a Microsoft OneDrive OAuth credential.
2. Open the imported workflow.
3. Select your OneDrive credential on the **Upload to OneDrive** node.
4. Replace `REPLACE_WITH_ONEDRIVE_FOLDER_ID` with the target folder ID.
5. Run a test execution with a small CSV file.

The webhook expects the uploaded file to arrive as n8n binary property `data`.
For a curl test against a local n8n webhook URL:

```bash
curl -X POST \
  -F "data=@/tmp/input.csv" \
  http://localhost:5678/webhook-test/csv-to-excel-report
```

Use `/webhook/csv-to-excel-report` after the workflow is active.

## Future Claude API step

The workflow includes a sticky note showing where Claude should be inserted.
Recommended next step:

1. Have the Python report script emit a small JSON summary next to the workbook,
   for example row counts, exceptions, stale records, or billing/project deltas.
2. Add an Anthropic/Claude node or HTTP Request node after **Run Python Report**.
3. Send Claude the JSON summary and any small excerpts needed for analysis.
4. Save Claude's result as:
   - a new worksheet in the Excel file, or
   - a separate `.txt`/`.md` file uploaded alongside the workbook, or
   - an n8n notification/email message.

Avoid sending the entire workbook to Claude unless there is a specific reason.
Small structured summaries are faster, cheaper, and easier to audit.

## Secrets

Do not commit `.env`, API tokens, OAuth client secrets, OneDrive credentials, or
QuickBooks refresh tokens. Configure production credentials in n8n credentials
and environment variables.
