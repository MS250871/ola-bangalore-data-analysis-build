# Findings: Ola Bengaluru Rides Analysis (July 2024)

**Rating: Share with caveats.** Numbers are validated and tie to the cleaned data. Caveats: one month only, fares do not track distance or vehicle type (DQ-09), turnaround unit is tentative seconds (DQ-11), and the patterns across segments are unusually flat (see "Read this first").

## Summary
- **103,024 bookings, 63,967 completed: success rate 62.09%.** 37.91% (39,057) of bookings did not become a ride.
- **Revenue INR 35,080,467** from completed rides; average fare INR 548.42. A further **INR 21,454,147** was quoted on bookings that never completed (quoted value, not revenue).
- The 39,057 failed bookings split into: driver cancelled 18,434 (17.89% of bookings), customer cancelled 10,499 (10.19%), driver not found 10,124 (9.83%).
- **Driver-side behaviour drives most failures:** drivers cancelled 47.2% of failed bookings; and 55.7% of customer cancellations cite the driver ("Driver is not moving towards pickup location" 30.2%, "Driver asked to cancel" 25.4%).
- **No segment stands out.** Success rate sits between 60% and 64% for every vehicle type, hour, day and area; the differences are within what chance alone produces (tests below).

## Read this first
- Success rate is 61.4% to 63.0% across the 7 vehicle types, 60.4% to 63.6% across the 24 hours, 60.3% to 63.6% across the 31 days and 59.8% to 64.0% across the 50 pickup areas. Statistical tests (chi-square on completed vs not) give p = 0.12 for vehicle type, 0.07 for hour, 0.73 for pickup area, 0.87 for date and 0.75 for weekday, none below the usual 0.05. In the area test, only 1 of 50 areas (Vijayanagar) is beyond 2 standard errors, about what chance gives.
- So **rankings below (best/worst vehicle, hour, area) are real arithmetic but not reliable signals**. Do not make area or vehicle-level decisions on them. The strong, usable signals are the overall failure rate and the cancellation reasons.
- The uniformity is unusual for real ride data. Worth confirming with the data owner that this file is a full, unsampled extract.

## Q1 Headline KPIs
- **Answer:** bookings 103,024; completed rides 63,967; success rate 62.09%; revenue INR 35,080,467; average fare INR 548.42.
- **Insight:** 3,926 completed rides (6.14%) are flagged incomplete but counted as completed (DQ-05 B).
- **Recommendation:** treat 62% as the baseline; the target to move is the 38% failure rate.
- **Caveat:** revenue is the recorded fare on completed rides; fares are not tied to distance (DQ-09).

## Q2 Booking outcome mix
| Outcome | Bookings | Share |
|---|---|---|
| Completed (Success) | 63,967 | 62.09% |
| Cancelled by driver | 18,434 | 17.89% |
| Cancelled by customer | 10,499 | 10.19% |
| Driver not found | 10,124 | 9.83% |
- **Insight:** cancellations by drivers are the largest single loss (47.2% of the 39,057 failed bookings); customer cancellations are 26.9% and no-driver 25.9%.
- **Recommendation:** make driver cancellations the first operational target.

## Q3 Daily bookings and success rate
- **Answer:** daily bookings average 3,323 (low 3,072 on 31 July, high 3,432 on 30 July). Daily success rate ranges 60.29% (12 July) to 63.60% (19 July); standard deviation 0.71 points.
- **Insight:** very stable month, no spikes or drops. Weekly bookings are 23,181; 23,386; 23,236; 23,347 and 9,874 (week of 29 July has 3 days only).
- **Recommendation:** use the 62% line as the daily reference; investigate only days outside about 60% to 64%.
- **Caveat:** one month; no trend over time can be shown. Mon to Wed have 5 occurrences in July, so raw weekday totals are higher; per-day averages are equal.

## Q4 Hourly demand profile
- **Answer:** demand is flat across the day: 4,176 (18:00) to 4,408 (12:00) bookings per hour, average 4,293.
- **Insight:** there is no clear peak or off-peak; night hours (00:00 to 05:00) carry as many bookings as daytime.
- **Recommendation:** driver supply needs to be planned for round-the-clock, even demand rather than a morning/evening peak.
- **Caveat:** hours are booking time, not pickup time.

## Q5 Success rate by hour
- **Answer:** lowest 60.36% at 10:00; highest 63.58% at 11:00 (also 63.6% at 05:00). Range 3.2 points.
- **Insight:** the spread is within chance (p = 0.07). No hour stands out as a service breakdown.
- **Recommendation:** no hour-specific intervention is supported by the data.

## Q6 Bookings and revenue by vehicle type
| Vehicle | Bookings | Completed | Revenue (INR) | Avg fare (INR) | Success rate |
|---|---|---|---|---|---|
| Auto | 14,755 | 9,167 | 5,051,846 | 551.09 | 62.13% |
| Bike | 14,662 | 9,134 | 4,971,968 | 544.34 | 62.30% |
| Mini | 14,552 | 9,036 | 4,885,961 | 540.72 | 62.09% |
| Prime Plus | 14,707 | 9,075 | 5,015,165 | 552.64 | 61.71% |
| Prime SUV | 14,655 | 8,996 | 4,876,815 | 542.11 | 61.39% |
| Prime Sedan | 14,877 | 9,379 | 5,224,050 | 556.99 | 63.04% |
| eBike | 14,816 | 9,180 | 5,054,662 | 550.62 | 61.96% |
- **Insight:** each type holds 14.1% to 14.4% of bookings and 13.9% to 14.9% of revenue. Prime Sedan is highest on revenue (14.89%) but the gap is small.
- **Recommendation:** no vehicle type is clearly stronger; do not shift fleet on this evidence.
- **Caveat:** average fares are almost identical across Bike, Auto and Prime types, which is not credible for real pricing (DQ-09). Treat revenue by type as indicative.

## Q7 Failure mix by vehicle type
| Vehicle | Customer cancel | Driver cancel | Driver not found | Success |
|---|---|---|---|---|
| Auto | 10.19% | 18.13% | 9.56% | 62.13% |
| Bike | 10.48% | 17.45% | 9.77% | 62.30% |
| Mini | 10.34% | 17.76% | 9.81% | 62.09% |
| Prime Plus | 10.02% | 18.24% | 10.03% | 61.71% |
| Prime SUV | 10.22% | 18.07% | 10.32% | 61.39% |
| Prime Sedan | 9.88% | 17.42% | 9.66% | 63.04% |
| eBike | 10.21% | 18.18% | 9.65% | 61.96% |
- **Insight:** driver cancellation is 17.4% to 18.2% and customer cancellation 9.9% to 10.5% for every type. Prime SUV has the highest no-driver rate (10.32%) and lowest success (61.39%), but not significantly (p = 0.35 for the full status mix).
- **Recommendation:** address driver cancellations fleet-wide, not per vehicle type.

## Q8 Pickup areas by bookings and failure rate
- **Answer:** 50 areas, each with 1,952 to 2,201 bookings. Failure rate ranges 36.03% (Koramangala) to 40.18% (Vijayanagar), against 37.91% overall.
- **Top 10 by bookings:** Banashankari 2,201 (37.98% failed); Yeshwanthpur 2,139 (36.75%); RT Nagar 2,135 (38.13%); Indiranagar 2,133 (37.41%); Sahakar Nagar 2,126 (38.48%); Basavanagudi 2,120 (37.64%); Ramamurthy Nagar 2,116 (36.77%); Vijayanagar 2,113 (40.18%); Tumkur Road 2,105 (39.71%); Cox Town 2,100 (36.43%).
- **Top 10 by failed bookings:** Vijayanagar 849; Banashankari 836; Tumkur Road 836; Langford Town 829; Kengeri 826; Hosur Road 826; Sahakar Nagar 818; RT Nagar 814; Peenya 801; BTM Layout 800.
- **Insight:** areas are almost equal in volume and failure; only Vijayanagar is slightly beyond chance (z = 2.15), and with 50 areas one such value is expected.
- **Recommendation:** no area needs special action on this data; if a pilot is wanted, Vijayanagar, Tumkur Road, Langford Town, Hosur Road and Kengeri (failure rates 39.6% to 40.2%) are the lowest-risk places to test a driver-reliability measure.
- **Caveat:** no zone or region mapping exists, so areas cannot be grouped.

## Q9 Customer cancellation reasons (10,499)
| Reason | Cancellations | Share |
|---|---|---|
| Driver is not moving towards pickup location | 3,175 | 30.2% |
| Driver asked to cancel | 2,670 | 25.4% |
| Change of plans | 2,081 | 19.8% |
| AC is not working | 1,568 | 14.9% |
| Wrong address | 1,005 | 9.6% |
- **Insight:** 5,845 cancellations (55.7%) are driver-driven; that is 5.67% of all bookings. AC not working (14.9%) is a fleet quality issue.
- **Recommendation:** alert or intervene when a driver is not moving toward pickup; stop drivers asking customers to cancel; check AC on cars before shifts.

## Q10 Driver cancellation reasons (18,434)
| Reason | Cancellations | Share |
|---|---|---|
| Personal & car related issue | 6,542 | 35.5% |
| Customer related issue | 5,413 | 29.4% |
| Customer was coughing/sick | 3,654 | 19.8% |
| More than permitted people in there | 2,825 | 15.3% |
- **Insight:** the reasons are driver-reported; 35.5% are the driver's own personal or car problem (6.35% of all bookings). "Customer related issue" is vague and large.
- **Recommendation:** add a pre-shift vehicle and availability check; replace the vague "customer related issue" with specific reasons to find out what is behind it.
- **Caveat:** reasons are self-reported by drivers.

## Q11 Quoted value lost to non-completed bookings
| Status | Bookings | Quoted value (INR) | Avg quoted (INR) |
|---|---|---|---|
| Cancelled by driver | 18,434 | 10,183,427 | 552.4 |
| Cancelled by customer | 10,499 | 5,770,901 | 549.7 |
| Driver not found | 10,124 | 5,499,819 | 543.2 |
| **Total** | 39,057 | **21,454,147** | |
- **Insight:** the quoted value on failed bookings is 37.95% of the total quoted value (56,534,614); it equals about 61% of the INR 35,080,467 actually earned. Driver cancellations alone account for INR 10.2 million.
- **Recommendation:** use this figure as the upper bound of the opportunity; a 10% cut in driver cancellations would protect roughly INR 1.0 million of quoted value for the month.
- **Caveat:** quoted value is not revenue and not all lost bookings would complete; fares are unreliable (DQ-09).

## Q12 Turnaround time and ratings by vehicle type (completed rides)
| Vehicle | Avg vehicle TAT (min) | Avg customer TAT (min) | Avg driver rating | Avg customer rating |
|---|---|---|---|---|
| Auto | 2.86 | 1.42 | 4.00 | 4.00 |
| Bike | 2.85 | 1.42 | 3.99 | 3.99 |
| Mini | 2.88 | 1.41 | 3.99 | 4.00 |
| Prime Plus | 2.85 | 1.41 | 4.00 | 4.01 |
| Prime SUV | 2.81 | 1.40 | 4.01 | 4.00 |
| Prime Sedan | 2.84 | 1.42 | 3.99 | 4.00 |
| eBike | 2.83 | 1.42 | 4.01 | 3.99 |
| **All** | 2.85 | 1.42 | 4.00 | 4.00 |
- **Insight:** no meaningful difference by vehicle type (ANOVA p = 0.06 for vehicle TAT, 0.07 for driver rating). Ratings average 4.0 everywhere.
- **Recommendation:** no vehicle-type action; ratings are a weak differentiator here.
- **Caveat:** the TAT source unit is seconds (user's belief, tentative) shown in minutes; if the unit is actually minutes, all TAT values are 60 times larger.

## Validation checks
| # | Check | Result |
|---|---|---|
| 1 | Rows = 103,024 and equal the cleaned CSV | PASS |
| 2 | Status counts add to total (63,967 + 10,499 + 18,434 + 10,124) | PASS |
| 3 | Completed = 63,967; success rate = 63,967 / 103,024 = 62.09% | PASS |
| 4 | Revenue = 35,080,467 over 63,967 rides; average fare 548.42 | PASS |
| 5 | Revenue + quoted value on non-completed = Booking_Value total (35,080,467 + 21,454,147 = 56,534,614) | PASS |
| 6 | Bookings by vehicle type add to 103,024 | PASS |
| 7 | Revenue by vehicle type adds to 35,080,467 | PASS |
| 8 | Bookings by hour add to 103,024 (24 hours) | PASS |
| 9 | Bookings by day add to 103,024 (31 days) | PASS |
| 10 | Bookings by pickup area add to 103,024 (50 areas) | PASS |
| 11 | Customer cancel reasons add to 10,499 | PASS |
| 12 | Driver cancel reasons add to 18,434 | PASS |
| 13 | Quoted value lost by status adds to 21,454,147 | PASS |
| 14 | All percentages between 0 and 100 | PASS |
| 15 | Counts are whole numbers | PASS |
| 16 | Rates use sums of parts (completed / bookings), not averages of averages; same denominator (all bookings) for Q1 to Q8 | PASS |
| 17 | Q12 averages use completed rides only (63,967) with the same base for TAT and ratings | PASS |
| 18 | Partial period flagged: week of 29 July has 3 days (9,874 bookings) | PASS |
| 19 | Analysis base control totals equal the cleaned data (Booking_Value, Revenue, Bookings, Is_Completed) | PASS |
| 20 | No join used, so no join explosion | PASS |

All 20 checks passed. Not checked here: desktop Excel recalculation of every PivotTable cell (LibreOffice timed out on this file size); the user confirmed in Excel that the tables and data appear after Refresh All. Numbers in the dashboards must equal this document.

## Assumptions
- Currency INR; distance in km; turnaround source unit seconds, shown in minutes (tentative).
- Success = status Success, including 3,926 flagged incomplete (DQ-05 B). Revenue = completed rides only. Driver Not Found is its own status (DQ-06 A).
- Same-area trips (2,121) kept in all figures (DQ-10 A). Fares used as recorded (DQ-09 B).
- Significance tests are chi-square (rates) and one-way ANOVA (means) at the 0.05 level.

## Pre-delivery review
- Conclusions supported by numbers: yes; where differences are within chance the text says so and recommends no action.
- Alternative explanations: uniform patterns may reflect sampled or synthetic data; reasons are self-reported; single month.
- Recommendations follow from findings: cancellation-reason actions rest on the reason counts; the Q11 opportunity is flagged as an upper bound.
- Rating: **Share with caveats**.
