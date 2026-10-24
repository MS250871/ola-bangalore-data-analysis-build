# Handoff: Ola Bengaluru Rides Analysis (July 2024)

Date: 2026-10-24. Raw Data check at close: **RAW DATA UNCHANGED** (SHA-256 guard).

## 1. What was built
- **Cleaned data:** 103,024 bookings x 27 columns, one row per booking (`05 Cleaning and Prep/Ola_Rides_Analysis_Clean_final.xlsx`, `ola_final.csv`).
- **Findings** (`07 Analysis/Findings.md`): 63,967 completed (62.09%); revenue INR 35,080,467; average fare INR 548.42; quoted value lost INR 21,454,147; failed bookings 39,057 (driver cancelled 18,434, customer cancelled 10,499, driver not found 10,124). Segment differences are within chance.
- **Excel dashboard v2:** KPI cards, 4 slicers, 14 charts, 12 PivotTables, coverage table. Numbers equal Findings.
- **Web dashboard:** 12 sections (Q1 to Q12), 4 filters plus Reset, works offline. 16 browser tests passed; 358 values match pandas and Findings.

## 2. File inventory
| Folder | File | Status |
|---|---|---|
| 01 Framing | Framing.md | final |
| 03 Data Inspection | Data Inspection.md, profile.json | final |
| 04 Quality Audit | Data Quality.md, Relationships.md, Issues Requiring Decisions.md, quality_signals.json, relationships.json | final |
| 05 Cleaning and Prep | Cleaning Plan.md, clean_data.py, Ola_Rides_Analysis_Clean_final.xlsx, ola_final.csv, Prep Details.md | final |
| 06 Question Bank | Question Bank.md (60 questions, Q1 to Q12 selected) | final |
| 07 Analysis | helpers.py, analysis_spec.json, Ola_Rides_Analysis_analysis_base_v1.xlsx, expected_values.json, Findings.md | final |
| 08 Excel Dashboard | Ola_Rides_Analysis_Dashboard_v2.xlsx, expected_values.json | final (v2) |
| 08 Excel Dashboard | Ola_Rides_Analysis_Dashboard_v1.xlsx | superseded (layout rejected) |
| 09 Web Dashboard | Ola_Rides_Analysis_Web_Dashboard_v1.html (standalone), index.html + data/*.json, build_web.py, page_template.html, tests/ | final |
| 02 Setup and Log | Analysis Log.md, project.json, kit/ (incl. pivot_builder_dash2.py used for v2) | final |

## 3. How to use
- **Excel (v2):** open, click Enable Editing, then Data > Refresh All (PivotTables are empty until refreshed). Click slicer buttons (Week, Vehicle, Pickup area, Payment); Ctrl+click for several; the funnel icon clears. KPI cards and charts update. `Dashboard_Data` feeds the charts; `Q01..Q12` sheets hold the PivotTables; `ola` is the data table.
- **Web:** use the dropdowns; Reset clears them. Payment applies only to Q6 and Q12. Open the standalone .html by double-click (works offline), or the artifact link below.

## 4. Refresh with new data
1. Put the new raw file in `Raw Data` (keep the old one) and update `project.json`.
2. Re-run `05 Cleaning and Prep/clean_data.py` (it stops if any check fails).
3. Excel: `python "02 Setup and Log/kit/scripts/pivot_builder_dash2.py" --spec "07 Analysis/analysis_spec.json" --mode v1 --dashboard --out "08 Excel Dashboard/<new name>.xlsx"`, then `integrity_check.py --min-pivots 12 --min-slicers 4`.
4. Web: `python "09 Web Dashboard/build_web.py"`, regenerate `tests/expected_*.json` with `--expect`, run `python tests/test_web.py --dir .`.
5. Compare to a fresh Findings.md; ask the data owner whether the extract is complete.

## 5. Links
- Web dashboard (Claude artifact): https://claude.ai/artifact/MKyamT8PrddxZea31esYUp, published 2026-10-24. **Private: shared with nobody.** Share from the artifact's Share menu.

## 6. Decisions summary (from the log)
- Revenue = completed rides only; INR; distance in km.
- DQ-05 B: Success includes 3,926 flagged-incomplete rides; incomplete is a separate flag.
- DQ-06 A: Driver Not Found is its own status.
- DQ-09 B: fares used as recorded; no fare-vs-distance or revenue-per-km views.
- DQ-10 A: same-area trips kept and flagged.
- DQ-11 B: turnaround source unit seconds (tentative), shown in minutes.
- One row per booking; Customer_ID not used. 12 dashboard questions approved. Findings, Excel and web dashboards approved by user; publishing approved 2026-10-24.

## 7. Known limitations and open items
- Excel repair-prompt (yes/no) never confirmed for the step 05 workbook, analysis base, Dashboard v1 or Dashboard v2. LibreOffice recalculation timed out on the large workbook, so Excel formulas were checked against pandas values, not recalculated.
- Web dashboard not yet tested by the user on their own browser and phone.
- One month of data only; week of 29 July has 3 days. Segment patterns are unusually flat: confirm the extract is complete and unsampled.
- Turnaround unit is tentative. Same-area trips and 3,926 flagged-incomplete rides are kept as decided.
