# Cleaning Plan: Ola Bengaluru Rides Analysis

**Status: APPROVED 2026-10-24, executing.**
Inputs used: Data Inspection.md, Data Quality.md, Relationships.md, Issues Requiring Decisions.md (Final), Framing.md.

## Baseline control totals (raw data, computed with pandas)
| Item | Value |
|---|---|
| Rows / columns | 103,024 / 21 |
| Booking_Value sum | 56,534,614 (103,024 rows) |
| Ride_Distance sum | 1,461,903 km (103,024 rows; 39,057 are 0) |
| V_TAT sum / non-null | 10,930,486 / 63,967 |
| C_TAT sum / non-null | 5,429,095 / 63,967 |
| Driver_Ratings sum / non-null | 255,705.3 / 63,967 |
| Customer_Rating sum / non-null | 255,760.1 / 63,967 |
| Booking_Status | Success 63,967; Canceled by Driver 18,434; Canceled by Customer 10,499; Driver Not Found 10,124 |
| Cells holding text "null" | 510,555 |
| Success with Incomplete_Rides = Yes | 3,926 |
| Same pickup and drop | 2,121 |

## 1. Safe formatting fixes (Class 1)
None. (No Class 1 issues were found.)

## 2. Issues requiring the user's review (Class 2): decided, applied as below
| ID | Decision | How it is applied | Row impact | Check |
|---|---|---|---|---|
| DQ-05 | B | `Is_Completed` = 1 where status is Success (63,967), else 0. `Incomplete_Rides` kept as a separate flag. | 0 rows removed | Is_Completed sum = 63,967; Success and Incomplete = Yes count = 3,926 |
| DQ-06 | A | `Booking_Status` kept as 4 values; "Driver Not Found" stays its own status. | 0 | 4 status values, counts equal baseline |
| DQ-09 | B | `Booking_Value` kept exactly as recorded; no rows removed; no revenue-per-km field created. | 0 | Booking_Value sum = 56,534,614 |
| DQ-10 | A | New flag `Same_Area_Trip` = Yes where pickup equals drop. | 0 | Yes count = 2,121 |
| DQ-11 | B | Original `V_TAT`, `C_TAT` kept (seconds); new `V_TAT_Min`, `C_TAT_Min` = seconds / 60. | 0 | V_TAT_Min sum = 182,174.77 (rounded 2 dp); non-null 63,967 |

## 3. Transformations for analysis (Class 3)
| ID | What changes | Row impact | Verification |
|---|---|---|---|
| DQ-01 | Text "null" in 9 columns (V_TAT, C_TAT, Canceled_Rides_by_Customer, Canceled_Rides_by_Driver, Incomplete_Rides, Incomplete_Rides_Reason, Payment_Method, Driver_Ratings, Customer_Rating) becomes a true blank. No value is invented. | 0 | Text "null" cells = 0 after; blanks per column equal the raw "null" counts (39,057 x 6; 92,525; 84,590; 99,098) |
| DQ-02 | Drop empty column `Unnamed: 20`. | 0 | Column absent; 20 original columns remain before other changes |
| DQ-03 | `Date` converted to a true date-time and renamed `Booking_Datetime`. Added: `Booking_Date`, `Booking_Hour` (0 to 23), `Weekday` (name), `Week_Start` (Monday date). `Time` dropped (duplicate of the time part). | 0 | 103,024 valid datetimes; min 2024-07-01, max 2024-07-31 23:58; hour matches the raw Time on all rows |
| DQ-04 / REL-01 | Drop `Vehicle Images` (one-to-one with Vehicle_Type). | 0 | Column absent; Vehicle_Type has 7 values |
| DQ-07 | New `Revenue` = `Booking_Value` where `Is_Completed` = 1, else blank. `Booking_Value` stays as the quoted value on all rows. Applies Framing decision 1 with the DQ-05 B definition. | 0 | Revenue sum = **35,080,467** over 63,967 rows; quoted value on non-completed = 21,454,147; the two add to 56,534,614 |
| DQ-08 | `Ride_Distance` = 0 becomes blank (no ride). | 0 | Blank count = 39,057; remaining sum = 1,461,903; min = 1 |

## Other planned handling
- `Customer_ID` is kept in the clean data (needed for analysis such as repeat bookings) but must not appear on any dashboard.
- Booking_ID stays the key; no join is used anywhere (Relationships.md).

## Expected result
| Item | Expected |
|---|---|
| Table | `ola` (one Excel Table) |
| Rows | 103,024 (no rows removed) |
| Columns | 27: 18 kept from raw (Booking_Datetime, Booking_ID, Booking_Status, Customer_ID, Vehicle_Type, Pickup_Location, Drop_Location, V_TAT, C_TAT, Canceled_Rides_by_Customer, Canceled_Rides_by_Driver, Incomplete_Rides, Incomplete_Rides_Reason, Booking_Value, Payment_Method, Ride_Distance, Driver_Ratings, Customer_Rating) + 9 new (Booking_Date, Booking_Hour, Weekday, Week_Start, Is_Completed, Revenue, Same_Area_Trip, V_TAT_Min, C_TAT_Min) |
| Files | `Ola_Rides_Analysis_Clean_final.xlsx` (one Excel Table, minimal formatting) and `ola_final.csv`; intermediates end `_draft`; script `clean_data.py`; `Prep Details.md` |

## Approvals
| Item | Approved by user | Date |
|---|---|---|
| Class 1 fixes | None needed | n/a |
| Class 2 decisions (DQ-05, 06, 09, 10, 11) | Yes, by choices in Issues Requiring Decisions.md | 2026-10-24 |
| Class 3 transformations (DQ-01, 02, 03, 04, 07, 08) | Yes ("approved, execute"). No exceptions. | 2026-10-24 |
| Go-ahead to execute | Yes | 2026-10-24 |
