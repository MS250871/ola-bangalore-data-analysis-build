# Issues Requiring Decisions: Ola Bengaluru Rides Analysis

**Status: FINAL (2026-10-24).** All 5 Class 2 issues answered by the user; each answer is the recommendation shown. Source: Data Quality.md (approved). Answers given by the user on 2026-10-24: "going ahead with your recommendations for the DQ questions".

| ID | Title | Choice | Date |
|---|---|---|---|
| DQ-05 | Success bookings also flagged incomplete | **B** | 2026-10-24 |
| DQ-06 | Driver Not Found status | **A** | 2026-10-24 |
| DQ-09 | Booking value unrelated to distance or vehicle type | **B** | 2026-10-24 |
| DQ-10 | Pickup equals drop | **A** | 2026-10-24 |
| DQ-11 | Turnaround time unit and logic | **B** | 2026-10-24 |

## DQ-05 "Success" bookings also flagged as incomplete
- **Question:** do the 3,926 "Success" bookings with `Incomplete_Rides = Yes` count as completed rides?
- **Found:** 3,926 of 63,967 Success bookings (reasons: Customer Demand 1,601; Vehicle Breakdown 1,591; Other Issue 734). They carry distance, payment, TAT and ratings.
- **Why a decision:** changes completed count, success rate, revenue and averages; Framing decision 4 said incomplete rides do not count as completed.
- **Options:** A) not completed (60,041 completed). B) completed (63,967), incomplete kept as a separate flag. C) completed for volume, excluded from revenue.
- **Recommendation:** B. Status is Success, with distance, payment and ratings; the incomplete share stays visible separately.
- **My choice: B** (2026-10-24). This **replaces Framing decision 4** for these 3,926 rows: Success = completed, and `Incomplete_Rides` is a separate flag.

## DQ-06 "Driver Not Found" status
- **Question:** how is the status "Driver Not Found" grouped?
- **Found:** 10,124 bookings, no cancellation reason, no TAT, no payment.
- **Why a decision:** changes cancellation and success rates.
- **Options:** A) own status, shown separately. B) fold into driver cancellations. C) fold into "all unsuccessful".
- **Recommendation:** A. It is a supply gap, not a cancellation decision.
- **My choice: A** (2026-10-24).

## DQ-09 Booking value unrelated to distance or vehicle type
- **Question:** how should the unusual fare values be treated?
- **Found:** range 100 to 2,999; correlation with distance 0.002 on Success; median fare almost equal for all vehicle types; 5,830 values above the 1,758 outlier fence.
- **Why a decision:** revenue and fare views could mislead.
- **Options:** A) use as recorded with a caveat. B) use as recorded but do not show revenue-per-km or fare-vs-distance views. C) exclude the 5,830 high-value rows from revenue.
- **Recommendation:** B. No row is provably wrong; views implying a fare-to-distance link would mislead.
- **My choice: B** (2026-10-24). No rows removed; no revenue-per-km field will be created.

## DQ-10 Pickup and drop location are the same
- **Question:** what to do with the 2,121 same-area bookings?
- **Found:** 2,121 (1,306 Success, 231 customer-cancelled, 372 driver-cancelled, 212 driver-not-found).
- **Why a decision:** may be genuine short trips or errors; affects route views.
- **Options:** A) keep all, label as same-area trips. B) keep in totals, exclude from route analysis. C) exclude entirely.
- **Recommendation:** A. They have valid distances and fares.
- **My choice: A** (2026-10-24).

## DQ-11 Turnaround times: unit and logic
- **Question:** what unit are V_TAT and C_TAT shown in?
- **Found:** V_TAT 35 to 308, C_TAT 25 to 145, only on Success; in 12,204 Success bookings V_TAT is below C_TAT. User believes the unit is seconds (tentative).
- **Why a decision:** decides display unit and wording.
- **Options:** A) seconds, shown in seconds. B) seconds, shown in minutes. C) minutes.
- **Recommendation:** B, once seconds is confirmed.
- **My choice: B** (2026-10-24). Original seconds columns are kept; minute columns are added. Unit remains tentative and is to be noted in Findings.

## Linked-issues check (done 2026-10-24)
- DQ-05 B changes the revenue base: completed = Success including incomplete; revenue total becomes **35,080,467** (not 32,829,985). Framing decision 1 (completed only) is applied with this definition.
- DQ-06 A and DQ-05 B together define status groups: Completed (Success), Customer cancelled, Driver cancelled, Driver not found. Incomplete is a flag within Completed.
- DQ-09 B is consistent with DQ-07: no rows removed, so row count and Booking_Value total do not change.
- DQ-10 A adds a flag column only; no row counts change.
- DQ-11 B adds minute columns only; original seconds values stay.
- No conflicts found. No row counts change from any Class 2 decision.
