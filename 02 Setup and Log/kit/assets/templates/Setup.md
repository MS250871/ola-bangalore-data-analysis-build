# Setup: {{PROJECT_NAME}}

**Summary:** Folder structure created, tools recorded, conventions set, raw files fingerprinted. No data has been opened or changed.

## Project
- **Name:** {{PROJECT_NAME}}
- **Purpose:** {{PURPOSE}}
- **Audience:** {{AUDIENCE}}
- **Root folder:** `{{ROOT}}`
- **Rules file:** `PROJECT_RULES.md` (single source of rules; `CLAUDE.md` and `AGENTS.md` point to it)
- **Settings:** `02 Setup and Log/project.json` (file prefix `{{PREFIX}}`, outputs, publish target, question target {{QUESTION_TARGET}})

## Folder Structure
| # | Folder | Purpose | Main output(s) |
|---|--------|---------|----------------|
| 0 | `Raw Data` | Original source files. Read-only | source files |
| 1 | `01 Framing` | Objective, audience, scope, plan, metrics, starter questions | `Framing.md` |
| 2 | `02 Setup and Log` | Tools, conventions, settings, running log, kit scripts | `Setup.md`, `Analysis Log.md`, `project.json`, `kit/` |
| 3 | `03 Data Inspection` | Structure per sheet and data dictionary | `Data Inspection.md` |
| 4 | `04 Quality Audit` | Quality issues, relationships, Class 2 decisions | `Data Quality.md`, `Relationships.md`, `Issues Requiring Decisions.md` |
| 5 | `05 Cleaning and Prep` | Cleaning plan, applied steps, cleaned data | `Cleaning Plan.md`, `Prep Details.md`, `clean_data.py`, `{{PREFIX}}_Clean_final.xlsx` + CSVs |
| 6 | `06 Question Bank` | Full question list and selected dashboard questions | `Question Bank.md` |
| 7 | `07 Analysis` | Analysis base workbook and findings | `analysis_spec.json`, `{{PREFIX}}_analysis_base_vN.xlsx`, `Findings.md` |
| 8 | `08 Excel Dashboard` | Interactive Excel dashboard | `{{PREFIX}}_Dashboard_vN.xlsx` |
| 9 | `09 Web Dashboard` | Aggregated JSON and HTML dashboard | `dashboard_spec.json`, `data/*.json`, `.html`, `tests/` |
| 10 | `10 Dash Handoff` | Handoff notes and file inventory | `Handoff.md` |

## Source Files (Raw Data)
{{RAW_TABLE}}

- Contents not yet opened. Inspection happens in `03 Data Inspection`.

## Tools in Use
{{TOOLS}}

## Conventions
- One step at a time; stop at each gate for approval. An approval closes the gate only; the next step starts on the user's own request.
- Reports are Markdown only. Excel and HTML only for data and dashboards.
- Exact file names from `PROJECT_RULES.md`. Update existing files in place; no renamed duplicates.
- Data and dashboard files are versioned (`_v1`, `_v2`); intermediates `_draft`, final `_final`. Never overwrite a known-good file.
- `Raw Data` is read-only; `raw_guard.py` proves it at every step.
- Issue IDs: `DQ-01...`, `REL-01...`. Question IDs: `Q1...Qn` once selected.
- Issues classed as Class 1 (formatting), Class 2 (user decision), Class 3 (transformation).
- Log is append-only, one line per row, no `|` inside cells, `<br>` for line breaks.
- Dates: `YYYY-MM-DD`.
- Data over about 10,000 rows is processed with scripts.

## Assumptions (non-result-changing only)
- A-01: Dates in the log and documents use `YYYY-MM-DD`.
- A-02: The folder table above mirrors `PROJECT_RULES.md`; the rules file wins if they differ.
- A-03: Raw file checksums are recorded so later steps can prove `Raw Data` was not modified.
- No assumptions about the data have been made. Anything that could change numbers, rows, definitions or conclusions will be raised as a Class 2 decision.
