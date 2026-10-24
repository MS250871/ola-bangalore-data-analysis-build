# Step Prompts (paste one at a time; reply "approved" at each gate)

Replace the parts in [brackets]. Each prompt maps to a skill, so you can also type the skill name, e.g. "use da-inspect".

## 00 + 02 Setup (da-new-project)
Read the rules first. This folder is the main folder for [PROJECT NAME]. The Raw Data folder already exists with my source files: do not create it and do not change it. Create the numbered folders 01 to 10, the Analysis Log and Setup.md. Project name: "[PROJECT NAME]". Purpose: "[ONE-SENTENCE PURPOSE]". Audience: [AUDIENCE]. File prefix: [PREFIX]. Do not touch any data yet. Log this step, then stop and ask for my approval.

## 01 Framing (da-frame)
Help me frame this project. Source data: [FILE NAME], [SHEETS/TABLES, approx rows and columns, date range]. Audience: [AUDIENCE AND DECISIONS]. Write Framing.md in 01 Framing covering: project objective; audience and the decisions they need to make; scope (in and out); a short starter set of 5 to 8 business questions; main metrics, each with a plain-language definition; final deliverables; an overall plan that follows the project's step sequence. Do not analyze the data in this step. Log it, then stop and ask for my approval.

## 03 Data Inspection (da-inspect)
Inspect the structure of every file and sheet in Raw Data. Do not calculate insights yet. For each sheet report: row count, column count, column names, inferred data types, likely keys, date fields, measures, dimensions, and grain. Also check and report: header row position, merged cells, hidden sheets or columns, formulas versus typed values, multiple tables on one sheet, and mixed units or currencies. Add a data dictionary section (column, inferred meaning, type, example values). Save as Data Inspection.md in 03 Data Inspection. Markdown only. Log it, then stop and ask for my approval.

## 04a Data Quality (da-audit)
Run a data quality audit on [TABLES] using completeness, uniqueness, consistency, timeliness, validity, and accuracy signals. For each issue give: an ID (DQ-01, DQ-02, ...), affected columns, example records, possible impact, recommended handling, and a class (Class 1 formatting fix, Class 2 decision required, Class 3 data transformation). Put observations that need no action in a Notes section. Do not clean or modify anything. Save as Data Quality.md in 04 Quality Audit. Log it, then stop and ask for my approval.

## 04b Relationships (da-audit)
Identify the relationships between [TABLES]. Show: likely primary keys, foreign keys, join type, join risks, and validation checks (orphan keys, duplicate keys, many-to-many matches). Warn me clearly about any join that could duplicate rows, and say how to avoid it. Number any new issues REL-01, REL-02, ..., each with a class. Do not modify anything. Save as Relationships.md in 04 Quality Audit. Log it, then stop and ask for my approval.

## 05a Cleaning Plan (da-clean)
Using Data Inspection.md, Data Quality.md, and Relationships.md, create Cleaning Plan.md in 05 Cleaning and Prep. Separate three sections: 1. Safe formatting fixes (Class 1) 2. Issues requiring my review (Class 2) 3. Transformations needed for analysis (Class 3). For each item give the ID, what will change, the expected row-count and total impact, and the verification check. Do not modify any data until I approve. Log it, then stop and ask for my approval.

## 05b Decisions (da-clean)
The formatting fixes (Class 1) in Cleaning Plan.md are approved. Now take the issues requiring my review (Class 2). For each one write: the question, the options (A, B, C and more if needed) with a one-line consequence each, and your recommendation with the reason. Leave "My choice" blank. Save as Issues Requiring Decisions.md in 04 Quality Audit. Then ask me the questions one at a time. I may also answer all of them at once by ID.

## 05c Approvals (da-clean)
All transformations (Class 3) in Cleaning Plan.md are approved [EXCEPT: list IDs, or delete this part]. Record the approvals in the plan. Also add that the cleaned file will be an Excel workbook with one Excel Table per sheet and minimal formatting, plus a CSV copy of each table. Show me a one-page summary of the combined plan: number of formatting fixes, decisions, and transformations, and the expected final row count of each table. Log it, then stop and wait for my go-ahead to execute.

## 05d Execute (da-clean)
Go ahead and execute the approved Cleaning Plan.md and the final decisions. Do ONLY data cleaning and preparation. No pivot tables, summaries, charts, or dashboards in this step. Never edit Raw Data. Write the cleaned data to 05 Cleaning and Prep as [PREFIX]_Clean_final.xlsx (one Excel Table per sheet, minimal formatting) plus a CSV copy of each table. Write Prep Details.md with what was applied, before and after row counts and totals, and the result of every verification check in the plan. Run the File Integrity Check and report exactly what you checked. Log it, then stop and ask for my approval.

## 06 Question Bank (da-questions)
Using Framing.md, Data Inspection.md, Relationships.md, Data Quality.md, the final decisions, and the cleaned data, build an exhaustive Question Bank.md in 06 Question Bank. Group the questions as descriptive, diagnostic, trend, segment, anomaly, and decision questions. For each give: ID, question, required columns, calculation method, chart type, answerable status (Yes, Partly, No) with the reason, limitation, and suggested priority. Add a section on valuable questions the data CANNOT answer and what extra data would be needed. Recommend a first set of [N] questions for the dashboard. Log it, then stop and ask for my approval.
Then: Confirmed. Add a "Selected Dashboard Questions" section numbered Q1 to Qn with the chosen chart for each. Log it, then stop and ask for my approval.

## 07a Analysis base (da-analyze)
Copy the final cleaned workbook into 07 Analysis as [PREFIX]_analysis_base_v1.xlsx. Never modify the cleaned file in 05. Add compact sheets with the summary tables needed to answer every selected question, labelled with the question ID. Build NATIVE PivotTables with slicers; do not start with formula summaries. Follow the ladder (v1 slicers, v2 report filters, v3 formulas with dropdowns); do not patch a failed attempt. Do NOT build the dashboard yet. Before saying it is ready: list the sheets, PivotTables and slicers you will create; save, reopen and report sheets, row counts, formula errors, and the number of PivotTables and slicers; check each PivotTable's grand total ties to the cleaned data; say plainly you could not open it in desktop Excel and ask me to check for a repair prompt. Log it, then stop and ask for my approval.

## 07b Findings (da-analyze)
Using the analysis base, answer every selected question with the actual numbers. Validate before reporting: reconcile totals back to the cleaned data, run sanity checks, and list the checks. Write Findings.md in 07 Analysis with key insights, supporting numbers, business recommendations, caveats, and limitations, linked to each question ID. Log it, then stop and ask for my approval.

## 08 Excel Dashboard (da-excel-dashboard)
Copy the analysis base into 08 Excel Dashboard and build the dashboard in the copy: one or two dashboard sheets only; answer ALL selected questions and end with a coverage table; interactive (slicers if reliable, otherwise dropdowns driving formulas); minimal formatting; numbers must match Findings.md; keep the PivotTables and slicers and report their counts. Run the File Integrity Check, report what you could not check, and ask me to open the file in desktop Excel. Log it, then stop and ask for my approval.

## 09 Web Dashboard (da-web-dashboard)
Build an interactive web dashboard in 09 Web Dashboard. Export only aggregated data as JSON. Build an HTML dashboard that loads it, answers ALL selected questions, and has live filters. Minimal styling, a coverage table, numbers matching Findings.md. Test that the JSON parses, the page loads, and the filters work. Do NOT publish yet. Log it, then stop and ask for my approval.

## 10 Publish and Handoff (da-handoff)
Publish the web dashboard as [a Claude artifact / ChatGPT canvas or Site / HTML file only]. Then write Handoff.md in 10 Dash Handoff: what was built, file inventory, how to use, refresh and share, links, decisions summary, known limitations, and open items. Log it, then stop and ask for my approval.
