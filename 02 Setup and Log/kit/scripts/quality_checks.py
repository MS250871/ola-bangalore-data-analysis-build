"""Data quality signals for step 04 (completeness, uniqueness, consistency, timeliness, validity, accuracy).

Usage: python quality_checks.py [files...] [--key "Table:Col1,Col2"]... [--out "04 Quality Audit/quality_signals.json"]
       (no files = every file in Raw Data; use the files that 03 Data Inspection described)

Produces CANDIDATE findings with counts, example rows and a suggested class. The assistant must review
each one, write it up in Data Quality.md with a DQ-nn ID, and decide the class using PROJECT_RULES.md
(any judgment call that could change results is Class 2). Never modifies inputs."""
import os, sys, re, argparse, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dakit import find_root, raw_files, write_json, read_tables
import pandas as pd
is_text = lambda s: s.dtype == object or pd.api.types.is_string_dtype(s)

warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="*")
ap.add_argument("--key", action="append", default=[], help='declared key, e.g. "Orders:Row ID" or "Orders:Order ID,Product ID"')
ap.add_argument("--out")
ap.add_argument("--root")
A = ap.parse_args()
root = find_root(A.root)
files = [os.path.abspath(f) for f in A.files] or raw_files(root)
out = A.out or os.path.join(root, "04 Quality Audit", "quality_signals.json")
keys = {}
for k in A.key:
    t, cs = k.split(":", 1)
    keys.setdefault(t, []).append([c.strip() for c in cs.split(",")])

findings = []


def add(table, dimension, check, columns, count, total, examples, suggested_class, note):
    findings.append({"table": table, "dimension": dimension, "check": check, "columns": columns, "count": int(count),
                     "pct": round(100 * count / total, 3) if total else 0, "examples": examples[:5],
                     "suggested_class": suggested_class, "note": note})


def ex(df, mask, cols, n=3):
    sub = df.loc[mask, cols].head(n)
    return [{str(k): (None if pd.isna(v) else str(v)) for k, v in r.items()} for r in sub.to_dict("records")]


for f in files:
    for tname, df in read_tables(f).items():
        n = len(df)
        if n == 0:
            add(tname, "completeness", "empty table", [], 0, 0, [], 2, "Table has no rows"); continue
        # completeness
        for c in df.columns:
            m = df[c].isna()
            if is_text(df[c]):
                m = m | df[c].astype(str).str.strip().isin(["", "NA", "N/A", "null", "NULL", "None", "-", "?"])
            if m.any():
                add(tname, "completeness", "missing or placeholder values", [str(c)], m.sum(), n, ex(df, m, list(df.columns[:6])),
                    2, "Decide: keep as missing, fill (with what), or exclude. Check if missingness is structural (e.g. a field only used in one country)")
        # uniqueness
        d = df.duplicated(keep=False)
        if d.any():
            add(tname, "uniqueness", "fully identical rows", list(map(str, df.columns)), df.duplicated().sum(), n,
                ex(df, d, list(df.columns[:6])), 2, "Decide whether repeats are genuine (two identical transactions) or double-loaded")
        for kc in keys.get(tname, []):
            kc = [c for c in kc if c in df.columns]
            if kc:
                dk = df.duplicated(kc, keep=False)
                if dk.any():
                    add(tname, "uniqueness", f"duplicate key {kc}", kc, df.duplicated(kc).sum(), n, ex(df, dk, list(df.columns[:6])),
                        2, "Declared key is not unique. Compare the duplicates column by column before deciding")
        # consistency / validity per column
        for c in df.columns:
            s = df[c]
            if is_text(s):
                sv = s.dropna().astype(str)
                ws = sv != sv.str.replace("\xa0", " ").str.replace(r"\s+", " ", regex=True).str.strip()
                if ws.any():
                    add(tname, "consistency", "leading, trailing, double or non-breaking spaces", [str(c)], ws.sum(), n,
                        [{"value": repr(v)} for v in sv[ws].unique()[:3]], 1, "Trim and collapse spaces")
                low = sv.str.strip().str.lower()
                grp = sv.groupby(low).nunique()
                var = grp[grp > 1]
                if len(var):
                    exs = [{"variants": list(sv[low == k].unique()[:4])} for k in var.index[:3]]
                    add(tname, "consistency", "same value with different capitalisation", [str(c)], int(sv[low.isin(var.index)].shape[0]), n,
                        exs, 1, "Standardise case (check that the variants really mean the same thing)")
                types = s.dropna().map(lambda v: type(v).__name__)
                if types.nunique() > 1:
                    add(tname, "validity", "mixed data types in one column", [str(c)], int((types != types.mode()[0]).sum()), n,
                        [{"types": dict(types.value_counts().head(4))}], 3, "Convert to one type; check the minority values first")
                if sv.str.fullmatch(r"-?\d+(\.\d+)?").mean() > 0.95 and len(sv) > 0:
                    lead0 = sv.str.match(r"0\d")
                    add(tname, "validity", "numbers stored as text" + (" (some with leading zeros)" if lead0.any() else ""), [str(c)],
                        len(sv), n, [{"value": v} for v in sv.unique()[:3]], 3,
                        "Convert to a number, or keep as text if it is a code (postal code, ID) where leading zeros matter")
            elif pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
                nn = s.dropna()
                if nn.empty:
                    continue
                if pd.api.types.is_float_dtype(s):
                    noisy = (nn.round(6) != nn) & ((nn * 1000).round() == (nn * 1000).round(6))
                    tails = (nn.round(4) != nn)
                    if noisy.any() or tails.mean() > 0.5:
                        add(tname, "accuracy", "floating-point tails (values not stored at their natural precision)", [str(c)],
                            int(max(noisy.sum(), tails.sum())), n, [{"value": repr(v)} for v in nn[tails].head(3)], 1,
                            "Round to the natural precision for display or grouping; keep stored totals unless the user decides otherwise")
                if (nn < 0).any():
                    add(tname, "validity", "negative values", [str(c)], (nn < 0).sum(), n, ex(df, s < 0, list(df.columns[:6])),
                        2 if not re.search(r"profit|margin|change|diff|balance|delta", str(c).lower()) else 0,
                        "Negative values may be valid (losses, refunds) or errors. Class 0 means likely valid: put in Notes if confirmed")
                if (nn == 0).mean() > 0.5 and nn.nunique() > 1:
                    add(tname, "accuracy", "more than half the values are zero", [str(c)], (nn == 0).sum(), n, [], 0, "Check whether zero means 'none' or 'missing'")
                q1, q3 = nn.quantile(0.25), nn.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    m = (s < q1 - 3 * iqr) | (s > q3 + 3 * iqr)
                    if m.any():
                        add(tname, "accuracy", "extreme outliers (beyond 3 x IQR)", [str(c)], m.sum(), n,
                            ex(df, m, [c] + [x for x in df.columns[:5] if x != c]), 2,
                            f"Range {nn.min()} to {nn.max()}; IQR fences {q1 - 3 * iqr:.4g} to {q3 + 3 * iqr:.4g}. Decide keep, cap, or exclude")
            elif pd.api.types.is_datetime64_any_dtype(s):
                nn = s.dropna()
                if nn.empty:
                    continue
                fut = nn > pd.Timestamp.now()
                if fut.any():
                    add(tname, "timeliness", "dates in the future", [str(c)], fut.sum(), n, ex(df, s > pd.Timestamp.now(), list(df.columns[:6])), 2, "")
                old = nn < pd.Timestamp("1990-01-01")
                if old.any():
                    add(tname, "validity", "dates before 1990 (possible defaults like 1900-01-01)", [str(c)], old.sum(), n, [], 2, "")
                per = nn.dt.to_period("M").value_counts().sort_index()
                if len(per) > 2:
                    gaps = pd.period_range(per.index.min(), per.index.max(), freq="M").difference(per.index)
                    if len(gaps):
                        add(tname, "timeliness", "months with no records inside the date range", [str(c)], len(gaps), len(per) + len(gaps),
                            [{"month": str(g)} for g in gaps[:5]], 0, "Possible missing loads; confirm with the source owner")
                    edge = per.iloc[-1] < 0.5 * per.iloc[-4:-1].mean() if len(per) > 4 else False
                    if edge:
                        add(tname, "timeliness", "last month looks incomplete", [str(c)], int(per.iloc[-1]), int(per.iloc[-4:-1].mean()),
                            [{"month": str(per.index[-1]), "rows": int(per.iloc[-1])}], 2, "Partial period: decide whether to exclude it from trends")
                        findings[-1]["pct"] = None
        # cross-column: pairs of date columns where end < start
        dcols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        for a in dcols:
            for b in dcols:
                if a != b and re.search(r"order|start|open|create", str(a).lower()) and re.search(r"ship|end|close|deliver", str(b).lower()):
                    m = df[b] < df[a]
                    if m.any():
                        add(tname, "validity", f"'{b}' before '{a}'", [str(a), str(b)], m.sum(), n, ex(df, m, [a, b]), 2, "")
        # constant columns
        for c in df.columns:
            if df[c].nunique(dropna=False) == 1:
                add(tname, "accuracy", "constant column (one value everywhere)", [str(c)], n, n, [{"value": str(df[c].iloc[0])}], 0,
                    "Carries no information; note it")

write_json(out, {"files": [os.path.relpath(f, root) for f in files], "findings": findings})
print(f"{len(findings)} candidate findings")
for i, x in enumerate(findings, 1):
    print(f"{i:>3}. [{x['table']}] {x['dimension']}: {x['check']} {x['columns']} -> {x['count']:,} ({x['pct']}%) suggested class {x['suggested_class']}")
print("WROTE", os.path.relpath(out, root))
print("Next: review each candidate, add anything the script cannot see (business-rule checks), assign DQ IDs and classes in Data Quality.md.")
