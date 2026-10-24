# Data Quality: Ola Bengaluru Rides Analysis

**Summary**
- Table audited: `ola` (103,024 rows x 21 columns, key `Booking_ID`). Raw data unchanged (raw_guard OK). Nothing was cleaned.
- 11 issues: **6 Class 3** (transformations), **5 Class 2** (your decisions), 0 Class 1. Plus 8 notes that need no action.
- Good news: no duplicate bookings, no impossible dates, no spelling variants in categories or locations, all 31 days of July covered, status and reason columns are consistent with each other.
- Main concern: **fares (`Booking_Value`) do not move with distance or vehicle type** (DQ-09). This could change how the revenue numbers should be read.
- Earlier outputs used: PROJECT_RULES.md, Framing.md (decisions 1 to 5), Data Inspection.md (flags F1 to F14, user's answers on units and rating), profile.json, `quality_signals.json` (script output), Analysis Log.

| ID | Title | Dimension | Columns | Count | Class |
|---|---|---|---|---|---|
| DQ-01 | Missing values stored as text "null" | Completeness | 9 columns (see below) | 39,057 to 99,098 per column | 3 |
| DQ-02 | Empty unnamed column | Validity | Unnamed: 20 | 103,024 | 3 |
| DQ-03 | Date is text with unpadded hour; Time repeats it | Consistency | Date, Time | 103,024 | 3 |
| DQ-04 | Redundant image link column | Validity | Vehicle Images | 103,024 | 3 |
| DQ-05 | "Success" bookings also flagged as incomplete | Consistency | Booking_Status, Incomplete_Rides | 3,926 | 2 |
| DQ-06 | "Driver Not Found" status is neither a customer nor a driver cancellation | Validity | Booking_Status | 10,124 | 2 |
| DQ-07 | Booking value present on bookings with no ride | Consistency | Booking_Value, Booking_Status | 39,057 | 3 (per Framing decision 1) |
| DQ-08 | Ride distance is 0 for bookings with no ride | Validity | Ride_Distance | 39,057 | 3 |
| DQ-09 | Booking value unrelated to distance or vehicle type; very wide range | Accuracy | Booking_Value, Ride_Distance, Vehicle_Type | 5,830 above fence; all rows affected | 2 |
| DQ-10 | Pickup and drop location are the same | Validity | Pickup_Location, Drop_Location | 2,121 | 2 |
| DQ-11 | Turnaround times: unit and logic | Accuracy | V_TAT, C_TAT | 12,204 | 2 |

## DQ-01 Missing values stored as text "null"
- **Dimension:** completeness. **Class 3.**
- **Columns and counts:** V_TAT 39,057; C_TAT 39,057; Incomplete_Rides 39,057; Payment_Method 39,057; Driver_Ratings 39,057; Customer_Rating 39,057; Canceled_Rides_by_Customer 92,525; Canceled_Rides_by_Driver 84,590; Incomplete_Rides_Reason 99,098.
- **Finding:** the nulls are **structural, not random**. The six columns with 39,057 nulls are null on exactly the 39,057 bookings that are not "Success" (10,499 customer cancelled + 18,434 driver cancelled + 10,124 driver not found) and filled on all 63,967 "Success" bookings. Customer-cancel reasons are filled only on customer-cancelled bookings, driver reasons only on driver-cancelled ones, and the incomplete reason only when Incomplete_Rides = Yes.
- **Example:** `CNR7153255142`, Canceled by Driver: V_TAT, C_TAT, Payment_Method, ratings all `null`; driver reason filled.
- **Impact:** left as text, "null" becomes a fake category in charts and blocks numeric averages.
- **Handling:** convert to true blanks; for reason and payment columns, add a clear label only where a chart needs it. No values are invented.

## DQ-02 Empty unnamed column
- **Dimension:** validity. **Class 3.** `Unnamed: 20` is 100% empty, created by a trailing comma on every line. Drop it in the clean data.

## DQ-03 Date is text; Time repeats it
- **Dimension:** consistency. **Class 3.**
- `Date` holds the date and time as text (e.g. `2024-07-22 3:15:00`; 42,976 rows have a single-digit hour, 60,048 have two). All 103,024 parse as valid dates between 2024-07-01 and 2024-07-31. `Time` equals the time part of `Date` on every row.
- **Handling:** convert to a true date-time; derive date, day of week, hour, week; keep one time field.

## DQ-04 Redundant image link column
- **Dimension:** validity. **Class 3.** `Vehicle Images` has exactly one URL per vehicle type (7 values), so it adds no information beyond `Vehicle_Type`. Drop it from the clean data (it can be kept in a lookup if you want icons later).

## DQ-05 "Success" bookings also flagged as incomplete
- **Dimension:** consistency. **Class 2.**
- **Found:** 3,926 of 63,967 "Success" bookings have `Incomplete_Rides = Yes` and a reason (Customer Demand 1,601; Vehicle Breakdown 1,591; Other Issue 734). They still carry distance, payment method, TAT and both ratings, so they look like rides that started and ended early.
- **Why it needs a decision:** your Framing decision 4 says only "Success" counts as completed and incomplete rides do not, but these rows are both. The choice changes the success rate, completed ride count, revenue and averages.
- **Options:** A) count them as **not completed** (completed = Success and not incomplete: 60,041); B) count them as completed (63,967) and show incomplete rides as a separate flag; C) count them as completed for volume but exclude from revenue.
- **Recommendation:** B. The booking status is "Success", they have distance, payment and ratings, and leaders can still see the incomplete share separately. Revenue question remains tied to DQ-07 and DQ-09.

## DQ-06 "Driver Not Found" status
- **Dimension:** validity. **Class 2.**
- **Found:** 10,124 bookings with status "Driver Not Found": no customer reason, no driver reason, no TAT, no payment.
- **Why a decision:** it is not a customer or driver cancellation, but it is a failed booking. How it is grouped changes the cancellation rates and success rate shown to leadership.
- **Options:** A) keep as its own status ("unfulfilled, no driver") shown separately; B) fold into driver cancellations; C) fold into "all unsuccessful".
- **Recommendation:** A. It is a supply gap, not a cancellation decision, and operating managers need it visible on its own.

## DQ-07 Booking value present on bookings with no ride
- **Dimension:** consistency. **Class 3** (follows Framing decision 1: revenue counts completed rides only).
- **Found:** `Booking_Value` is filled on every row, including the 39,057 that were cancelled or had no driver.
- **Handling:** keep the original field and add a derived revenue field that is set only for rides counted as completed (exact definition depends on DQ-05). Cancelled bookings keep their value as "quoted value".

## DQ-08 Ride distance is 0 for bookings with no ride
- **Dimension:** validity. **Class 3.** `Ride_Distance` is 0 on exactly the 39,057 non-Success bookings; the smallest distance on a Success booking is 1 km. Treat these zeros as "no ride" (blank) so average distance is not dragged down.

## DQ-09 Booking value unrelated to distance or vehicle type
- **Dimension:** accuracy. **Class 2.**
- **Found:**
  - Range 100 to 2,999; median 386; on Success bookings the correlation between value and distance is 0.002 (essentially none).
  - Median value is almost the same for every vehicle type (382 to 391, including Bike, Auto, Mini and Prime SUV).
  - Value per km on Success bookings runs from about 2 to 2,981 (median about 20).
  - 5,830 bookings (5.66%) are above the extreme-outlier fence of 1,758; no negative or zero values.
- **Why it needs a decision:** fares normally track distance and vehicle class. These do not, so revenue, average fare and revenue-per-km views may be misleading, and the "outliers" may just be part of a wide spread rather than errors.
- **Options:** A) use values as recorded and add a caveat in Findings and on the dashboards; B) use as recorded but do not show revenue-per-km or fare-vs-distance views; C) exclude the 5,830 high-value rows from revenue figures.
- **Recommendation:** B. No row is provably wrong, so nothing should be removed, but views that imply a distance-to-fare relationship would mislead.

## DQ-10 Pickup and drop location are the same
- **Dimension:** validity. **Class 2.**
- **Found:** 2,121 bookings (1,306 of them Success) have identical pickup and drop areas; 231 customer-cancelled, 372 driver-cancelled, 212 driver-not-found.
- **Why a decision:** may be genuine short trips within one area, or data errors; affects route and area views.
- **Options:** A) keep all and label them "same-area trips"; B) keep in totals but exclude from route (pickup to drop) analysis; C) exclude entirely.
- **Recommendation:** A. They have valid distances and fares; only route views need to handle them.

## DQ-11 Turnaround times: unit and logic
- **Dimension:** accuracy. **Class 2.**
- **Found:** V_TAT ranges 35 to 308 and C_TAT 25 to 145, filled only on Success bookings. You told us the unit is seconds (tentative). In 12,204 Success bookings V_TAT is smaller than C_TAT, so the two are not simply "arrival" and "wait" in sequence.
- **Why a decision:** the unit decides how times are displayed (seconds or minutes) and whether they are described as wait times.
- **Options:** A) treat as seconds and show in seconds; B) treat as seconds and show in minutes; C) treat as minutes.
- **Recommendation:** B if you confirm seconds. Please confirm the unit with whoever owns the data if possible.

## Notes (no action needed)
- **N1. Coverage:** all 31 days of July 2024 present, 3,072 to 3,432 bookings per day, every hour populated. No partial first or last month. Only one month of data, so trends are daily, weekly and hourly.
- **N2. Keys:** `Booking_ID` is unique and always matches `CNR` plus 10 digits; `Customer_ID` always matches `CID` plus 6 digits. No duplicate rows, even ignoring the ID, and no customer with two bookings at the same minute.
- **N3. Ratings:** all between 3.0 and 5.0 in steps of 0.1; filled on every Success booking, blank otherwise (see DQ-01).
- **N4. Locations:** 50 pickup and 50 drop areas, the same list in both; no case, spacing or spelling variants. Jayanagar and Vijayanagar are two different areas, not a typo.
- **N5. Customer privacy:** `Customer_ID` has 94,544 distinct values; 7,954 customers booked more than once (max 5). It will be excluded from both dashboards.
- **N6. Embedded instructions:** none found in any text column.
- **N7. Status vs reason:** reason columns match the booking status on 100% of rows.
- **N8. Currency and units:** booking value taken as INR and distance as km per your confirmation.

## Linked issues
- DQ-05 drives DQ-07 (what counts as revenue) and the Framing success definition.
- DQ-06 affects the cancellation and success rates together with DQ-05.
- DQ-09 qualifies DQ-07: even decided revenue should carry the plausibility caveat.
