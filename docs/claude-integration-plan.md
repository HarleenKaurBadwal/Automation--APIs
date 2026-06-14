# Claude integration plan

The first automation milestone is CSV upload -> Python report -> Excel workbook
-> OneDrive. Claude can be added after that path is stable.

## Recommended Claude placement

Insert Claude after **Run Python Report** and before **Read Excel Report** in the
n8n workflow.

At that point the workflow knows whether the Python job succeeded and can pass
Claude a compact summary instead of the full workbook.

## Python output contract to add next

Update the report script to write a JSON sidecar file:

```json
{
  "generated_at_utc": "2026-06-14T01:21:00+00:00",
  "source_csv_rows": 25,
  "aha_records": 40,
  "gitlab_records": 18,
  "quickbooks_records": 12,
  "warnings": [],
  "exceptions": []
}
```

Suggested output path:

```bash
/tmp/report-<execution-id>.summary.json
```

Then update the n8n command to pass a summary path:

```bash
python3 /workspace/src/report_runner.py \
  --input-csv "/tmp/input-{{$execution.id}}.csv" \
  --output-xlsx "/tmp/report-{{$execution.id}}.xlsx"
```

If the existing report script needs an explicit flag, include it in
`REPORT_COMMAND`, for example:

```bash
REPORT_COMMAND=python3 scripts/your_existing_report.py --input-csv {input_csv} --output-xlsx {output_xlsx} --summary-json /tmp/report-summary.json
```

## Claude prompt shape

Use Claude for audit-style output:

```text
You are reviewing an automated report generated from Aha, GitLab, QuickBooks,
and an uploaded CSV. Identify anomalies, missing data, stale records, and
high-priority follow-ups. Return concise bullets grouped by system.

Report summary JSON:
{{ $json }}
```

## Output options

Choose one:

- append a "Claude Summary" worksheet to the Excel workbook
- upload a separate Markdown summary to OneDrive
- send the summary in Slack/email while keeping the workbook unchanged

For auditability, store Claude's prompt input and output with the execution
metadata when the workflow moves into production.
