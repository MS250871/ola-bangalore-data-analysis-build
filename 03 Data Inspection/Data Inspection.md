# Data Inspection: Ola Bengaluru Rides Analysis

**Summary**
- 1 file: `Raw Data/ola.csv` (21,445,921 bytes), UTF-8 with a byte-order mark, comma-separated, 1 table.
- 103,024 rows x 21 columns (20 named columns plus one empty unnamed trailing column).
- **Grain:** one row = one ride booking request, identified by `Booking_ID` (103,024 distinct, no duplicates).
- Date range of `Date`: 2024-07-01 00:00 to 2024-07-31 23:58 (one calendar month).
- Missing values are stored as the literal text `null` (not blank cells) in 10 columns.
- Not an Excel file, so merged cells, hidden sheets, formulas and multi-table layout checks do not apply (stated below).
- Earlier outputs used: PROJECT_RULES.md, Setup.md, project.json, Framing.md (approved, open points decided), Analysis Log. Script output: `03 Data Inspection/profile.json`.
- No insights, totals, trends or rankings in this step.

## 1. Table `ola`
| Item | Value |
|---|---|
| Rows / columns | 103,024 / 21 |
| Likely key | `Booking_ID` (single column, unique, no nulls) |
| Date field | `Date` (text `YYYY-MM-DD H:MM:SS`; also contains the time) |
| Measures | `V_TAT`, `C_TAT`, `Booking_Value`, `Ride_Distance`, `Driver_Ratings`, `Customer_Rating` |
| Dimensions | `Time`, `Booking_Status`, `Vehicle_Type`, `Pickup_Location`, `Drop_Location`, `Payment_Method`, `Canceled_Rides_by_Customer`, `Canceled_Rides_by_Driver`, `Incomplete_Rides`, `Incomplete_Rides_Reason` |
| Identifiers | `Booking_ID`, `Customer_ID` (94,544 distinct) |
| Exact duplicate rows | 0 |
| Script role overrides | `Customer_ID` kept as identifier (not a dimension for charts). `Vehicle Images` is a lookup attribute, not a dimension. `Canceled_Rides_by_*` and `Incomplete_Rides_Reason` are reason text columns, not flags. `Unnamed: 20` is empty. |

## 2. Layout checks (file level)
- Header row: row 1, one header row. No title rows or notes above it.
- Merged cells, hidden sheets, hidden rows or columns, formulas vs typed values, multiple tables per sheet, Excel Tables: **none found / not applicable** (plain CSV).
- Currency or unit mix: `Booking_Value` has no currency symbol (assumed INR per Framing decision); `Ride_Distance` has no unit in the file (user confirmed kilometres); `V_TAT` and `C_TAT` have no unit in the file (user believes seconds, tentative; check the ranges in the audit).
- Trailing comma on every line creates the 21st empty column (`Unnamed: 20`, 103,024 empty values).
- Column name `Vehicle Images` contains a space; all other names use underscores.
- Leading or trailing spaces in any cell: none found.

## 3. Data dictionary
| Column | Inferred meaning | Type | Example values | Notes |
|---|---|---|---|---|
| Date | Booking date and time | Text datetime | 2024-07-26 14:00:00 | All parse as dates. Hour is not zero-padded (18 or 19 characters). Time part equals `Time` on every row. |
| Time | Booking time of day | Text time (HH:MM:SS) | 14:00:00, 22:20:00 | 1,440 distinct values (minute precision). Duplicates the time part of `Date`. |
| Booking_ID | Unique booking reference | Text | CNR7153255142 | Unique, no nulls. |
| Booking_Status | Final outcome of the booking | Text, 4 values | Success; Canceled by Customer; Canceled by Driver; Driver Not Found | No nulls. |
| Customer_ID | Customer reference | Text | CID713523 | 94,544 distinct; 7,954 customers appear more than once. Personal-type field: not for dashboards. |
| Vehicle_Type | Vehicle category booked | Text, 7 values | Auto, Bike, Mini, Prime Plus, Prime SUV, Prime Sedan, eBike | No nulls. |
| Pickup_Location | Pickup area | Text, 50 values | Tumkur Road, Magadi Road | No nulls. |
| Drop_Location | Drop area | Text, 50 values | RT Nagar, Varthur | No nulls. |
| V_TAT | Vehicle turnaround time; unit seconds (user's belief, tentative) | Integer stored as decimal | 203, 238 | Range 35 to 308. 39,057 `null`. |
| C_TAT | Customer turnaround time; unit seconds (user's belief, tentative) | Integer stored as decimal | 30, 130 | Range 25 to 145. 39,057 `null`. |
| Canceled_Rides_by_Customer | Reason a customer cancelled | Text, 5 reasons | Wrong Address, Change of plans, AC is Not working, Driver asked to cancel, Driver is not moving towards pickup location | 92,525 `null`. |
| Canceled_Rides_by_Driver | Reason a driver cancelled | Text, 4 reasons | Personal & Car related issue, Customer related issue, Customer was coughing/sick, More than permitted people in there | 84,590 `null`. |
| Incomplete_Rides | Whether a ride was left incomplete | Text, Yes/No | Yes, No | 39,057 `null`. |
| Incomplete_Rides_Reason | Reason a ride was incomplete | Text, 3 reasons | Customer Demand, Vehicle Breakdown, Other Issue | 99,098 `null`. |
| Booking_Value | Fare amount of the booking | Integer | 444, 158, 386 | Range 100 to 2999. No nulls, populated on every row. |
| Payment_Method | How the ride was paid | Text, 4 values | Cash, UPI, Credit Card, Debit Card | 39,057 `null`. |
| Ride_Distance | Trip distance in kilometres (confirmed by user) | Integer | 0, 13, 40 | Range 0 to 49. No nulls. 39,057 rows hold 0. |
| Driver_Ratings | Rating given to the driver | Decimal | 4.1, 4.2 | Range 3.0 to 5.0, steps of 0.1. 39,057 `null`. |
| Customer_Rating | Rating the customer gave for the ride (confirmed by user) | Decimal | 4.0, 4.8 | Range 3.0 to 5.0, steps of 0.1. 39,057 `null`. |
| Vehicle Images | Icon URL for the vehicle type | Text URL | https://cdn-icons-png.flaticon.com/128/... | 7 distinct, exactly one per `Vehicle_Type`. Not analytical. |
| Unnamed: 20 | Artifact of trailing commas | Empty | (none) | 100% empty. |

## 4. Flags for 04 Quality Audit (flagged, not judged)
- **F1. `null` as text:** 10 columns use the text `null` for missing values; they need one consistent missing-value treatment.
- **F2. Empty column:** `Unnamed: 20` is completely empty.
- **F3. Date format:** `Date` is text with a non-zero-padded hour; `Time` repeats its time part. Only one month (July 2024) is present, which limits trend questions to day, week and hour views.
- **F4. Same-count null pattern:** `V_TAT`, `C_TAT`, `Incomplete_Rides`, `Payment_Method`, `Driver_Ratings` and `Customer_Rating` each have 39,057 `null`, and `Ride_Distance` has 39,057 zeros. These counts appear to match the non-completed bookings. To confirm in the audit that nulls are structural, not errors.
- **F5. Status vs reason consistency:** reason columns look mutually exclusive by status (customer reasons only with customer cancellations, driver reasons only with driver cancellations, neither for Driver Not Found). `Incomplete_Rides = Yes` appears on some `Success` rows (3,926), so "Success" and "completed" may not be the same thing; this affects Framing decision 4.
- **F6. Booking_Value on non-completed rides:** populated on every row including cancelled ones; Framing decision 1 (completed rides only) applies, to be confirmed against the status flag in F5.
- **F7. Ride_Distance zeros:** 39,057 zero distances, plausibly placeholders for rides that did not happen.
- **F8. Pickup equals drop:** 2,121 bookings have the same pickup and drop location.
- **F9. Units:** `V_TAT` and `C_TAT` are vehicle and customer turnaround time, in seconds per the user (tentative; ranges 35 to 308 and 25 to 145). `Ride_Distance` is in kilometres (user confirmed).
- **F10. Rating meaning:** `Customer_Rating` is the rating given by the customer for the ride (user confirmed). Grain confirmed as one row per booking.
- **F11. Outliers and ranges:** booking value up to 2,999 and distance up to 49 look plausible but need a distribution check; no values outside stated ranges were seen in this step.
- **F12. Repeat customers and ID privacy:** `Customer_ID` is personal-type data; dashboards must not show it.
- **F13. Location lists:** 50 pickup and 50 drop locations; check for spelling variants and near-duplicates in the audit.
- **F14. Vehicle Images:** redundant lookup column; likely dropped from the clean data.
