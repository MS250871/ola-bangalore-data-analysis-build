# Framing: Ola Bengaluru Rides Analysis

**Summary:** One source file (`Raw Data/ola.csv`) of ride bookings. Goal: a leadership dashboard (Excel and web) that shows how bookings, completions, cancellations, revenue and customer experience are performing, and where operations can improve. This step does not open the data; the metric and question lists below are a seed and get confirmed in steps 03 to 06.

## 1. Objective
Understand how Ola's Bengaluru ride bookings perform and why bookings fail, then deliver an interactive dashboard in Excel and on the web for operating managers and leaders. The dashboard should help them see volume, success, revenue and service quality at a glance and drill down by time, vehicle type, location and payment method.

## 2. Audience and decisions
| Audience | Decisions they make | What they need from this analysis |
|---|---|---|
| Leadership team | Where to invest, which vehicle types and areas to grow, targets for success rate and revenue | Headline KPIs, trends over time, top and bottom segments |
| Operating managers | Driver and fleet allocation, peak-hour coverage, reducing cancellations and incomplete rides | Cancellation and incomplete-ride reasons, hourly and area patterns, response-time (TAT) views |

## 3. Scope
**In scope**
- All bookings in `ola.csv`, whatever their status (completed, cancelled by customer, cancelled by driver, incomplete, and any others found).
- Volume, status mix, revenue, distance, turnaround times, ratings, payment method, vehicle type, pickup and drop areas, time patterns.
- Excel dashboard (with PivotTables and slicers) and a web dashboard published as a Claude artifact.

**Out of scope**
- Forecasting or predictive models.
- Driver-level or customer-level profiling; no personal IDs are shown in any dashboard.
- Pricing or surge analysis (no fare-rule data), competitor comparison, external data.
- Anything needing data not in the file (cost per ride, driver earnings, weather, traffic).

## 4. Starter questions (seed only; full list in 06)
- SQ1. How many bookings are there, and what share is completed, cancelled (by customer or driver) or incomplete?
- SQ2. How do bookings and revenue trend over time (day, week, month)?
- SQ3. Which vehicle types drive the most bookings and revenue, and how do their success rates compare?
- SQ4. Which pickup and drop areas have the most demand, and the worst cancellation rates?
- SQ5. What are the main reasons for customer cancellations, driver cancellations and incomplete rides?
- SQ6. At what hours and days is demand highest, and does success rate drop at peaks?
- SQ7. How do payment methods split, and does the split differ by vehicle type?
- SQ8. How do driver and customer ratings vary by vehicle type, and how do turnaround times relate to outcomes?

## 5. Metrics (plain definitions)
| Metric | Definition | Formula in words |
|---|---|---|
| Total bookings | Every booking record | Count of bookings |
| Completed rides | Bookings with a successful outcome | Count where status is success |
| Success rate | Share of bookings completed | Completed rides / Total bookings |
| Cancellation rate (customer / driver) | Share cancelled by each side | Cancelled by customer (or driver) / Total bookings |
| Incomplete ride rate | Share of started rides that did not finish | Incomplete rides / Total bookings |
| Booking value (revenue) | Fare amount recorded per booking | Sum of booking value |
| Average booking value | Typical fare | Revenue / number of rides in the revenue base |
| Average ride distance | Typical trip length | Sum of distance / number of rides in the distance base |
| Vehicle TAT / Customer TAT | Response and wait times as recorded in the file | Average of each, by segment |
| Average driver / customer rating | Mean of the ratings given | Sum of ratings / number of rated rides |

## 6. Deliverables by folder
- `01 Framing`: this file.
- `03 Data Inspection`: Data Inspection.md with data dictionary.
- `04 Quality Audit`: Data Quality.md, Relationships.md, Issues Requiring Decisions.md.
- `05 Cleaning and Prep`: Cleaning Plan.md, Prep Details.md, clean_data.py, cleaned Excel and CSV.
- `06 Question Bank`: Question Bank.md (recommends 12 questions; you choose the final set).
- `07 Analysis`: analysis base workbook with PivotTables, Findings.md.
- `08 Excel Dashboard`: interactive Excel dashboard.
- `09 Web Dashboard`: interactive web dashboard (self-contained HTML).
- `10 Dash Handoff`: Handoff.md, published Claude artifact link (only with your approval).

## 7. Plan and gates
1. 01 Framing (this step), gate: you approve.
2. 03 Data Inspection, gate: you approve.
3. 04 Quality Audit, gate: you approve.
4. 05 Cleaning and Prep: plan, your decisions on Class 2 issues, then execution; each part gated.
5. 06 Question Bank, gate: you select the final dashboard questions.
6. 07 Analysis and Findings, gate: you approve.
7. 08 Excel Dashboard, gate: you approve and confirm Excel opens cleanly.
8. 09 Web Dashboard, gate: you approve.
9. 10 Handoff and publish, gate: you approve publishing.

## 8. Success criteria
- Every selected dashboard question is answered with numbers that match Findings.md in both dashboards.
- All data issues are logged and every issue that could change results is decided by you.
- Excel dashboard opens in desktop Excel without a repair prompt; PivotTables and slicers work.
- Web dashboard opens offline, filters work, and no row-level or personal data appears in it.
- Leaders can read the headline KPIs in under a minute.

## 9. Decisions on open points (user, 2026-10-24: all recommendations accepted)
1. **Revenue base:** booking value counts completed rides only.
2. **Currency:** INR (Rs).
3. **Time window:** all dates in the file; flag any partial month after inspection.
4. **Success definition:** only "Success" status counts as completed; incomplete rides do not.
5. **Number of dashboard questions:** target 12; Question Bank recommends 12 and the final set is chosen by the user (may exceed 12).
