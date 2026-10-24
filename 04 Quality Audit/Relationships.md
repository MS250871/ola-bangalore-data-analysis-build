# Relationships: Ola Bengaluru Rides Analysis

**Summary**
- Only **one table** (`ola`, 103,024 rows) exists, so there are **no joins between tables** and no foreign keys to validate.
- **No join duplicates rows** because no join is needed. No warning applies.
- 1 relationship issue (REL-01, Class 3, linked to DQ-04). 4 notes.
- Raw data unchanged. Earlier outputs used: Data Inspection.md, Data Quality.md (approved, Class 2 answers recorded), relationships.json (script output), Analysis Log.

## Likely primary keys
| Table | Key | Check |
|---|---|---|
| ola | `Booking_ID` | Unique (103,024 distinct), no nulls, always `CNR` + 10 digits |

`Customer_ID` is not a key: 94,544 distinct values over 103,024 bookings (7,954 customers book more than once, at most 5 times). It is an attribute of a booking, not a table.

## Foreign keys and joins
- **None found.** The script found no column pairs linking tables, because there is only one table.
- Recommended join type: **not applicable**. All analysis runs on the single table.

## Validation checks
| Check | Result |
|---|---|
| Duplicate keys (`Booking_ID`) | 0 |
| Orphan keys (either direction) | Not applicable (single table) |
| Many-to-many matches | Not applicable |
| Joins that would duplicate rows | None |

## Issues
### REL-01 Vehicle image link is a one-to-one lookup of Vehicle_Type
- **Class 3.** Linked to **DQ-04**.
- Each of the 7 `Vehicle_Type` values has exactly one `Vehicle Images` URL, so the image link is a lookup attribute repeated on every row.
- **Handling:** drop it from the clean data. If icons are wanted later, keep a small 7-row lookup (Vehicle_Type to URL) and use a map, not a merge. No risk of row duplication either way.

## Notes (no action needed)
- **N1.** `Pickup_Location` and `Drop_Location` use the same list of 50 areas. No location master table exists, and none is needed; both columns can be analysed on the same area names.
- **N2.** `Date` plus `Time` describe one timestamp (see DQ-03); not a relationship between tables.
- **N3.** No hierarchy columns (for example city, zone or region) exist, so area-level grouping is limited to the 50 area names unless you supply a zone mapping.
- **N4.** Customer repeat behaviour can be measured through `Customer_ID`, but it must not be shown on dashboards (see Data Quality N5).
