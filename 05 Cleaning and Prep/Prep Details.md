# Prep Details: Ola Bengaluru Rides Analysis

**Summary:** Cleaning executed on 2026-10-24 exactly as the approved Cleaning Plan and the Final Issues Requiring Decisions. **103,024 rows in, 103,024 rows out. 27 columns. All 28 script checks passed; integrity check 7 passed, 0 failed.** Raw data unchanged (hash verified before and after).

## Files
- `05 Cleaning and Prep/Ola_Rides_Analysis_Clean_final.xlsx`: 1 sheet / Excel Table `tblola`, 103,024 rows, minimal formatting.
- `05 Cleaning and Prep/ola_final.csv`: same data, 103,024 rows x 27 columns.
- `05 Cleaning and Prep/clean_data.py`: the cleaning script (reads `Raw Data/ola.csv` read-only, asserts the raw SHA-256).
- Earlier outputs used: Cleaning Plan.md (approved), Issues Requiring Decisions.md (Final), Data Quality.md, Relationships.md, Data Inspection.md, Framing.md.
- Note: one run was stopped by the script's own checks (the text "null" had not been converted in text columns because of a data-type detail). The final file was not written then. The script was fixed and rerun; the files above come from the passing rerun.

## Applied (by ID)
| ID | Applied |
|---|---|
| DQ-01 | Text "null" in 9 columns converted to true blanks; no values invented |
| DQ-02 | Empty column `Unnamed: 20` dropped |
| DQ-03 | `Date` converted to a date-time and renamed `Booking_Datetime`; added `Booking_Date`, `Booking_Hour`, `Weekday`, `Week_Start` (Monday); `Time` dropped |
| DQ-04 / REL-01 | `Vehicle Images` dropped |
| DQ-05 (B) | `Is_Completed` = 1 for Success (63,967); `Incomplete_Rides` kept as a separate flag |
| DQ-06 (A) | `Booking_Status` kept with 4 values |
| DQ-07 | `Revenue` = `Booking_Value` for completed rides only; `Booking_Value` kept as quoted value on all rows |
| DQ-08 | `Ride_Distance` 0 converted to blank (39,057) |
| DQ-09 (B) | `Booking_Value` unchanged; no rows removed; no revenue-per-km field |
| DQ-10 (A) | `Same_Area_Trip` flag added (Yes = 2,121) |
| DQ-11 (B) | `V_TAT` and `C_TAT` kept in seconds; `V_TAT_Min` and `C_TAT_Min` added (seconds / 60, 4 decimals) |

## Before and after
| Item | Before | After |
|---|---|---|
| Rows | 103,024 | 103,024 |
| Columns | 21 | 27 |
| Booking_Value sum | 56,534,614 | 56,534,614 |
| Ride_Distance sum | 1,461,903 (39,057 zeros) | 1,461,903 (39,057 blanks, min 1) |
| V_TAT sum / C_TAT sum | 10,930,486 / 5,429,095 | unchanged |
| Driver_Ratings / Customer_Rating sum | 255,705.3 / 255,760.1 | unchanged |
| Revenue (new) | n/a | 35,080,467 over 63,967 completed rides |
| Quoted value on non-completed | n/a | 21,454,147 (ties: 35,080,467 + 21,454,147 = 56,534,614) |
| V_TAT_Min sum | n/a | 182,174.71 (plan estimate 182,174.77; difference is rounding to 4 dp) |
| Text "null" cells | 510,555 | 0 |

## Verification checks (from clean_data.py)
- PASS DQ-06 four status values
- PASS DQ-05 Is_Completed sum = 63,967 [63967]
- PASS DQ-05 Success & Incomplete=Yes = 3,926
- PASS DQ-10 same-area Yes = 2,121
- PASS DQ-11 V_TAT_Min non-null 63,967
- PASS DQ-11 V_TAT_Min sum ~182,174.77 [182,174.71]
- PASS DQ-01 no text 'null' left
- PASS DQ-01 blanks in Canceled_Rides_by_Customer = raw null count [92525]
- PASS DQ-01 blanks in Canceled_Rides_by_Driver = raw null count [84590]
- PASS DQ-01 blanks in Incomplete_Rides_Reason = raw null count [99098]
- PASS DQ-01 blanks in Payment_Method = raw null count [39057]
- PASS DQ-01 blanks in Incomplete_Rides = raw null count [39057]
- PASS DQ-01 blanks in V_TAT = 39,057
- PASS DQ-01 blanks in C_TAT = 39,057
- PASS DQ-01 blanks in Driver_Ratings = 39,057
- PASS DQ-01 blanks in Customer_Rating = 39,057
- PASS DQ-03 all 103,024 dates valid
- PASS DQ-03 range [2024-07-01 00:00:00 to 2024-07-31 23:58:00]
- PASS DQ-03 hour matches raw Time
- PASS DQ-02/04 dropped columns absent
- PASS DQ-08 zero distances before = 39,057
- PASS DQ-08 distance blanks = 39,057, sum unchanged, min 1
- PASS DQ-07 Revenue sum = 35,080,467 over 63,967 rows [35,080,467]
- PASS DQ-07 quoted non-completed = 21,454,147 and total ties
- PASS DQ-09 Booking_Value sum unchanged
- PASS column set = 27 expected [27]
- PASS rows unchanged 103,024
- PASS draft ola rows = 103024

## Integrity check (integrity_check.py)
- Final xlsx: zip package valid; opens with openpyxl (1 sheet: ola); 103,024 data rows; no formula error values; 1 Excel Table (tblola); 0 PivotTables, 0 slicers, 0 charts (none expected at this step).
- CSV: parses (103,024 rows x 27 columns); rows = 103,024; Booking_Value total = 56,534,614.
- Summary: 7 passed, 0 failed. raw_guard: RAW DATA UNCHANGED.
- **Not checked:** opening the workbook in desktop Excel (repair prompt or not). Needs the user.

## Column list (27)
Booking_Datetime, Booking_Date, Booking_Hour, Weekday, Week_Start, Booking_ID, Booking_Status, Is_Completed, Customer_ID, Vehicle_Type, Pickup_Location, Drop_Location, Same_Area_Trip, V_TAT, C_TAT, V_TAT_Min, C_TAT_Min, Canceled_Rides_by_Customer, Canceled_Rides_by_Driver, Incomplete_Rides, Incomplete_Rides_Reason, Booking_Value, Revenue, Payment_Method, Ride_Distance, Driver_Ratings, Customer_Rating.

## Reminders for later steps
- `Customer_ID` must not appear on any dashboard.
- Turnaround unit is seconds per the user (tentative); show minutes.
- Fares do not track distance or vehicle type (DQ-09): no revenue-per-km or fare-vs-distance views.
- Data covers July 2024 only.
