# Question Bank: Ola Bengaluru Rides Analysis

**Summary**
- Six groups: Descriptive DE (12), Diagnostic DG (11), Trend TR (10), Segment SG (9), Anomaly AN (9), Decision DC (9). **60 questions**, of which 59 are answerable (Yes or Partly) and 1 (TR-10) cannot be answered with this data.
- **Recommended dashboard set: 12 questions** (target in project.json), listed at the end. You decide the final set and may go beyond 12.
- Built from: Framing.md (SQ1 to SQ8 and metric definitions), Data Inspection.md, Data Quality.md, Relationships.md, Issues Requiring Decisions.md (Final), Prep Details.md and the cleaned data (27 columns, 103,024 rows, checked with pandas).

## Conventions used by every question
- **Grain:** one row = one booking, each counted once by Booking_ID.
- **Rates** use all bookings as the base unless stated. **Success rate** = completed / bookings, where completed = status Success (63,967), including the 3,926 flagged incomplete (DQ-05 B).
- **Revenue** = Revenue field (completed rides only). **Quoted value** = Booking_Value on non-completed bookings; never called revenue.
- **Driver Not Found** is its own status (DQ-06 A). **Turnaround** shown in minutes, source in seconds (tentative, DQ-11 B).
- **No** fare-vs-distance or revenue-per-km views (DQ-09 B). **Customer_ID** is never shown on a dashboard.
- Data is **July 2024 only** (31 days). Week of 29 July has 3 days. Dashboard filters can use date, vehicle type, pickup area, status and payment method.

## 1. Descriptive (DE)
| ID | Question | Columns | Calculation | Chart | Answerable | Limitation | Priority |
|---|---|---|---|---|---|---|---|
| DE-01 | How many bookings, completed rides, what success rate, revenue and average fare overall? | Booking_ID, Is_Completed, Revenue, Booking_Value | Count bookings; sum Is_Completed; success rate = completed / bookings; revenue = sum Revenue; avg fare = revenue / completed | KPI tiles | Yes | Fare caveat DQ-09 | High |
| DE-02 | What is the split of booking outcomes (completed, cancelled by customer, cancelled by driver, driver not found)? | Booking_Status | Count by status / total bookings | Donut or stacked bar | Yes | None | High |
| DE-03 | How do bookings and revenue split by vehicle type? | Vehicle_Type, Booking_ID, Revenue | Bookings and sum Revenue per vehicle type | Clustered bar | Yes | Revenue caveat DQ-09 | High |
| DE-04 | How do completed rides split by payment method? | Payment_Method, Is_Completed | Count completed rides by payment method | Bar | Yes | Payment known only for completed rides | Medium |
| DE-05 | Which 10 pickup areas have the most bookings? | Pickup_Location | Top 10 count of bookings | Horizontal bar | Yes | 50 areas, no zone grouping | High |
| DE-06 | Which 10 drop areas have the most bookings? | Drop_Location | Top 10 count of bookings | Horizontal bar | Yes | Same as DE-05 | Medium |
| DE-07 | What are the reasons customers cancel, and how often? | Canceled_Rides_by_Customer | Count by reason among customer-cancelled bookings | Bar | Yes | 5 reasons only | High |
| DE-08 | What are the reasons drivers cancel, and how often? | Canceled_Rides_by_Driver | Count by reason among driver-cancelled bookings | Bar | Yes | 4 reasons only | High |
| DE-09 | Why are rides left incomplete? | Incomplete_Rides, Incomplete_Rides_Reason | Count by reason where Incomplete_Rides = Yes | Bar | Yes | Only among completed-status rides (DQ-05) | Medium |
| DE-10 | What are the average ride distance and average fare of completed rides? | Ride_Distance, Revenue, Is_Completed | Mean distance and mean revenue over completed rides | KPI tiles | Yes | No fare-vs-distance view (DQ-09) | Medium |
| DE-11 | How are driver and customer ratings distributed? | Driver_Ratings, Customer_Rating | Count by rating value (3.0 to 5.0) | Histogram | Yes | Completed rides only | Low |
| DE-12 | How many bookings are same-area trips? | Same_Area_Trip | Count and share of Yes | KPI tile | Yes | None | Low |

## 2. Diagnostic (DG)
| ID | Question | Columns | Calculation | Chart | Answerable | Limitation | Priority |
|---|---|---|---|---|---|---|---|
| DG-01 | Does the success rate differ by vehicle type? | Vehicle_Type, Is_Completed | Completed / bookings per vehicle type | Bar | Yes | Cause not in data | High |
| DG-02 | How do customer cancellation, driver cancellation and driver-not-found rates differ by vehicle type? | Vehicle_Type, Booking_Status | Count by status / bookings per vehicle type | 100% stacked bar | Yes | None | High |
| DG-03 | Which pickup areas have the highest driver-not-found rate? | Pickup_Location, Booking_Status | Driver Not Found / bookings per area; top 10 | Bar | Yes | Small areas can swing; show volume | High |
| DG-04 | Which pickup areas have the lowest success rate? | Pickup_Location, Is_Completed | Completed / bookings per area; bottom 10 | Bar | Yes | Show volume alongside | High |
| DG-05 | Do driver cancellation reasons differ by vehicle type? | Vehicle_Type, Canceled_Rides_by_Driver | Count of reasons per vehicle type | Stacked bar | Yes | None | Medium |
| DG-06 | How does the success rate change by hour of day? | Booking_Hour, Is_Completed | Completed / bookings per hour | Line | Yes | None | High |
| DG-07 | Do vehicle and customer turnaround times differ by vehicle type? | Vehicle_Type, V_TAT_Min, C_TAT_Min | Mean of each per vehicle type (completed rides) | Clustered bar | Yes | Seconds unit tentative (DQ-11) | Medium |
| DG-08 | Do driver and customer ratings differ by vehicle type? | Vehicle_Type, Driver_Ratings, Customer_Rating | Mean rating per vehicle type | Bar | Yes | Completed rides only | Medium |
| DG-09 | Does the incomplete-ride rate differ by vehicle type? | Vehicle_Type, Incomplete_Rides | Incomplete = Yes / completed rides per type | Bar | Yes | None | Medium |
| DG-10 | Do ratings fall when turnaround times are longer? | V_TAT_Min, C_TAT_Min, ratings | Mean rating by turnaround-time band | Column | Yes (partly) | Association only, not cause | Low |
| DG-11 | Which customer cancellation reasons dominate in the highest-volume pickup areas? | Pickup_Location, Canceled_Rides_by_Customer | Reason counts for the top 10 areas | Stacked bar | Yes | Small counts per area | Low |

## 3. Trend (TR)
| ID | Question | Columns | Calculation | Chart | Answerable | Limitation | Priority |
|---|---|---|---|---|---|---|---|
| TR-01 | How do daily bookings and success rate move across July? | Booking_Date, Is_Completed | Bookings per day; completed / bookings per day | Combo line | Yes | One month only | High |
| TR-02 | How does daily revenue move? | Booking_Date, Revenue | Sum Revenue per day | Line | Yes | Revenue caveat DQ-09 | High |
| TR-03 | How do weekly bookings compare? | Week_Start | Bookings per week | Column | Yes (partly) | Last week has only 3 days (29 to 31 July) | Medium |
| TR-04 | What is the hourly demand profile? | Booking_Hour | Bookings per hour | Column | Yes | None | High |
| TR-05 | Which days of the week are busiest? | Weekday | Bookings per weekday (average per date) | Column | Yes | 4 to 5 occurrences per weekday | Medium |
| TR-06 | Where is demand highest across hour and weekday? | Booking_Hour, Weekday | Bookings per hour x weekday | Heatmap table | Yes | None | Medium |
| TR-07 | How does the cancellation rate trend daily (customer and driver)? | Booking_Date, Booking_Status | Cancelled / bookings per day, by type | Line | Yes | None | Medium |
| TR-08 | How do average turnaround times trend daily? | Booking_Date, V_TAT_Min, C_TAT_Min | Mean per day | Line | Yes | Unit tentative | Low |
| TR-09 | How do average ratings trend weekly? | Week_Start, ratings | Mean rating per week | Line | Yes | Last week partial | Low |
| TR-10 | How does July compare to previous months or the same month last year? | Booking_Date | n/a | n/a | No | Only July 2024 in the data | n/a |

## 4. Segment (SG)
| ID | Question | Columns | Calculation | Chart | Answerable | Limitation | Priority |
|---|---|---|---|---|---|---|---|
| SG-01 | How does the status mix look for each vehicle type? | Vehicle_Type, Booking_Status | Counts per vehicle type x status | Stacked bar | Yes | Same view as DG-02 | Medium |
| SG-02 | Which pickup areas contribute most revenue, split by vehicle type? | Pickup_Location, Vehicle_Type, Revenue | Sum Revenue per area (top 10) x vehicle | Stacked bar | Yes | Revenue caveat DQ-09 | Medium |
| SG-03 | How does the payment mix differ by vehicle type? | Vehicle_Type, Payment_Method | Completed rides per type x payment | 100% stacked bar | Yes | Completed rides only | Low |
| SG-04 | Which 10 routes (pickup to drop) have the most bookings? | Pickup_Location, Drop_Location | Count per pair; top 10 | Bar | Yes | 2,500 possible pairs, thin counts | Medium |
| SG-05 | How do the average fare and average distance differ by vehicle type? | Vehicle_Type, Revenue, Ride_Distance | Means per vehicle type | Bar | Yes (partly) | Fares do not follow vehicle class (DQ-09); caveat only | Low |
| SG-06 | What share of bookings come from repeat customers, and do they succeed more? | Customer_ID, Is_Completed | Customers with 2+ bookings; share of bookings; success rate by group | KPI tiles (aggregated only) | Yes (partly) | Customer_ID never shown; 86,590 single, 7,954 repeat | Low |
| SG-07 | How does the status mix differ by part of day (night, morning, afternoon, evening)? | Booking_Hour, Booking_Status | Group hours into day-parts; counts by status | Stacked bar | Yes | Day-part bands to be agreed | Medium |
| SG-08 | How do completed rides split by distance band? | Ride_Distance, Vehicle_Type | Bands (for example 1-10, 11-20, 21-30, 31-40, 41-49 km) | Column | Yes | Band edges are a choice | Low |
| SG-09 | Weekday versus weekend: bookings, success rate and revenue? | Weekday, Is_Completed, Revenue | Group Saturday and Sunday vs rest | Clustered column | Yes | 4 to 5 weekends only | Medium |

## 5. Anomaly (AN)
| ID | Question | Columns | Calculation | Chart | Answerable | Limitation | Priority |
|---|---|---|---|---|---|---|---|
| AN-01 | Which days have unusually low success rates? | Booking_Date, Is_Completed | Daily rate vs mean +/- 2 SD | Line with band | Yes | Range may be narrow | Medium |
| AN-02 | Which hours show spikes in cancellations or driver-not-found? | Booking_Hour, Booking_Status | Hourly rates vs overall | Column | Yes | None | Medium |
| AN-03 | Which pickup areas are outliers on cancellation rate? | Pickup_Location, Booking_Status | Area rate vs mean +/- 2 SD | Bar with threshold | Yes | Small-area noise | Medium |
| AN-04 | Do very high fares (above 1,758) cluster in a vehicle type or area? | Booking_Value, Vehicle_Type, Pickup_Location | Share above fence per group | Bar | Yes (partly) | 5,830 rows; fares unreliable (DQ-09) | Low |
| AN-05 | Which rides have extreme turnaround times (top 1%)? | V_TAT_Min, C_TAT_Min | Rows above the 99th percentile; counts by vehicle and area | Table | Yes | Unit tentative | Low |
| AN-06 | Do any customers book far more than others? | Customer_ID | Max 5 bookings per customer | None on dashboard | Partly | Privacy: not displayed; little spread | Low |
| AN-07 | How do same-area trips end compared with other trips? | Same_Area_Trip, Booking_Status | Status mix by flag | Bar | Yes | None | Low |
| AN-08 | Are low ratings (3.5 or below) concentrated in some vehicle types or areas? | ratings, Vehicle_Type, Pickup_Location | Share of rides rated 3.5 or below | Bar | Yes | Completed rides only | Medium |
| AN-09 | How often is vehicle turnaround shorter than customer turnaround? | V_TAT, C_TAT | Count where V_TAT < C_TAT (12,204 rides) | KPI | Yes (partly) | Meaning of the two fields unclear (DQ-11) | Low |

## 6. Decision (DC)
| ID | Question | Columns | Calculation | Chart | Answerable | Limitation | Priority |
|---|---|---|---|---|---|---|---|
| DC-01 | Where and when is supply short (driver-not-found by area and hour)? | Pickup_Location, Booking_Hour, Booking_Status | Driver Not Found counts by area x hour (top 10 areas) | Heatmap table | Yes | Cause of shortage not in data | High |
| DC-02 | How much quoted booking value is lost to cancellations and driver-not-found, by status? | Booking_Value, Booking_Status | Sum of Booking_Value where Is_Completed = 0, by status | Bar | Yes (partly) | Quoted value, not real revenue; DQ-09 caveat | High |
| DC-03 | Which vehicle types lose the most bookings to failure? | Vehicle_Type, Is_Completed | Non-completed bookings and share per vehicle type | Bar | Yes | None | High |
| DC-04 | Which peak hours need extra coverage (high volume and low success)? | Booking_Hour, Is_Completed | Bookings and success rate by hour | Combo | Yes | None | High |
| DC-05 | Which areas to prioritise (high volume and high failure)? | Pickup_Location, Is_Completed | Bookings vs failure rate per area; top 10 by failed bookings | Scatter or bar | Yes | None | High |
| DC-06 | Which customer cancellation reasons can operations act on? | Canceled_Rides_by_Customer | Share of 'Driver is not moving towards pickup' and 'Driver asked to cancel' | Bar | Yes | Cause not in data | Medium |
| DC-07 | Which driver cancellation reasons point to fleet or conduct issues? | Canceled_Rides_by_Driver | Share by reason | Bar | Yes | 4 reasons only | Medium |
| DC-08 | Which vehicle types to grow (volume, success rate, ratings together)? | Vehicle_Type, Is_Completed, ratings | Volume, success rate and mean ratings per type | Table | Yes | No cost or margin data | Medium |
| DC-09 | Is vehicle breakdown a material cause of incomplete rides? | Incomplete_Rides_Reason | Share of Vehicle Breakdown among incomplete rides | Bar | Yes | Completed-status rides only | Low |

## Questions the data cannot answer
| Question | Extra data needed |
|---|---|
| Is a ride profitable; what is the margin per vehicle type? | Driver pay, fuel, platform cost, commission |
| Why was no driver found? | Driver availability, supply logs, requests sent per booking |
| How long after booking did a cancellation happen? | Cancellation timestamp |
| Do prices depend on demand (surge)? | Surge multiplier, base fare rules |
| Month-on-month or seasonal trend | More months than July 2024 |
| Which individual drivers perform best or worst? | Driver ID |
| Who are our customers (age, city zone, loyalty)? | Customer attributes |
| How do ratings relate to specific trip events? | Trip event data, written feedback |
| Effect of weather, traffic or events on demand | External data |
| How do we compare with competitors? | Competitor data |

## Recommended dashboard set (12)
| # | Bank ID | Question | Why it matters |
|---|---|---|---|
| 1 | DE-01 | Headline KPIs: bookings, completed rides, success rate, revenue, average fare | Leaders' one-minute view |
| 2 | DE-02 | Booking outcome mix | Shows how much demand is lost |
| 3 | TR-01 | Daily bookings and success rate | Spots drops and stability over the month |
| 4 | TR-04 | Hourly demand profile | Drives driver scheduling |
| 5 | DG-06 | Success rate by hour of day | Shows when service breaks down |
| 6 | DE-03 | Bookings and revenue by vehicle type | Where volume and revenue sit |
| 7 | DG-02 | Customer cancel, driver cancel and driver-not-found rates by vehicle type | Which vehicle types fail and how |
| 8 | DC-05 | Pickup areas ranked by bookings and failure rate (top 10) | Where operations should focus |
| 9 | DE-07 | Customer cancellation reasons | What customers say is wrong |
| 10 | DE-08 | Driver cancellation reasons | What drivers say is wrong |
| 11 | DC-02 | Quoted value lost to non-completed bookings, by status | Size of the problem in money terms (caveat: quoted, not revenue) |
| 12 | DG-07 + DG-08 | Turnaround time and ratings by vehicle type | Service quality view |

**Strong alternates** if you want to swap or add: DC-01 (supply gaps by area and hour), DE-04 (payment mix), DE-09 (incomplete reasons), TR-06 (hour x weekday heatmap), SG-04 (top routes), SG-09 (weekday vs weekend).

## Selected Dashboard Questions (confirmed by user 2026-10-24)
The user accepted the recommended 12. All later steps use Q1 to Q12 only. Q12 combines DG-07 and DG-08. Rates use all bookings as the base; revenue means completed rides only; Q11 is quoted value, not revenue.

| # | Bank ID | Question | Chart | Responds to filters |
|---|---|---|---|---|
| Q1 | DE-01 | Headline KPIs: bookings, completed rides, success rate, revenue, average fare | KPI tiles | All filters |
| Q2 | DE-02 | Booking outcome mix (completed, customer cancelled, driver cancelled, driver not found) | Donut | Date, vehicle type, pickup area, payment method |
| Q3 | TR-01 | Daily bookings and success rate | Combo (columns + line) | Vehicle type, pickup area |
| Q4 | TR-04 | Hourly demand profile | Column | Date, vehicle type, pickup area |
| Q5 | DG-06 | Success rate by hour of day | Line | Date, vehicle type, pickup area |
| Q6 | DE-03 | Bookings and revenue by vehicle type | Clustered bar | Date, pickup area, payment method |
| Q7 | DG-02 | Customer cancel, driver cancel and driver-not-found rates by vehicle type | 100% stacked bar | Date, pickup area |
| Q8 | DC-05 | Top 10 pickup areas by bookings and failure rate | Bar (bookings) + failure rate | Date, vehicle type |
| Q9 | DE-07 | Customer cancellation reasons | Bar | Date, vehicle type, pickup area |
| Q10 | DE-08 | Driver cancellation reasons | Bar | Date, vehicle type, pickup area |
| Q11 | DC-02 | Quoted value lost to non-completed bookings, by status | Bar | Date, vehicle type, pickup area |
| Q12 | DG-07 + DG-08 | Average turnaround time (minutes) and ratings by vehicle type | Clustered bar | Date, pickup area, payment method |
