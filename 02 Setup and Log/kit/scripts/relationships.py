"""Find keys and relationships between tables (step 04, Relationships.md). Read-only.

Usage: python relationships.py [files...] [--out "04 Quality Audit/relationships.json"]
       (no files = every file in Raw Data)

For every table: single-column primary-key candidates (unique, no nulls).
For every pair of tables: columns with the same name (case/space-insensitive) or strong value overlap,
with: distinct values each side, overlap, orphans each way (with examples), cardinality (1:1, 1:many,
many:1, many:many), and the row count a LEFT JOIN would produce versus the left table (duplication risk)."""
import os, sys, re, argparse, itertools, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dakit import find_root, raw_files, write_json, read_tables
import pandas as pd
is_text = lambda s: s.dtype == object or pd.api.types.is_string_dtype(s)

warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="*")
ap.add_argument("--out")
ap.add_argument("--root")
A = ap.parse_args()
root = find_root(A.root)
files = [os.path.abspath(f) for f in A.files] or raw_files(root)
out = A.out or os.path.join(root, "04 Quality Audit", "relationships.json")

tables = {}
for f in files:
    for t, df in read_tables(f).items():
        tables[t] = df
norm = lambda c: re.sub(r"[\s_\-]+", "", str(c).lower())

pk = {t: [str(c) for c in df.columns if df[c].notna().all() and df[c].is_unique and len(df) > 0] for t, df in tables.items()}
rels = []
for (ta, a), (tb, b) in itertools.combinations(tables.items(), 2):
    pairs = [(ca, cb) for ca in a.columns for cb in b.columns if norm(ca) == norm(cb)]
    if not pairs:   # value-overlap fallback for differently named keys
        for ca in a.columns:
            if not is_text(a[ca]):
                continue
            va = set(a[ca].dropna().astype(str).unique())
            if not (10 <= len(va) <= 200000):
                continue
            for cb in b.columns:
                if not is_text(b[cb]):
                    continue
                vb = set(b[cb].dropna().astype(str).unique())
                if vb and len(va & vb) / min(len(va), len(vb)) > 0.8:
                    pairs.append((ca, cb))
    for ca, cb in pairs:
        sa, sb = a[ca].dropna().astype(str), b[cb].dropna().astype(str)
        va, vb = set(sa.unique()), set(sb.unique())
        ua, ub = a[ca].is_unique, b[cb].is_unique
        card = {(True, True): "1:1", (True, False): "1:many", (False, True): "many:1", (False, False): "many:many"}[(ua, ub)]
        cnt_b = sb.value_counts()
        joined_rows = int(sa.map(cnt_b).fillna(1).sum()) + int(a[ca].isna().sum())
        rels.append({"left": ta, "left_col": str(ca), "right": tb, "right_col": str(cb), "cardinality": card,
                     "left_distinct": len(va), "right_distinct": len(vb), "overlap": len(va & vb),
                     "orphans_left_not_in_right": len(va - vb), "orphan_examples_left": sorted(va - vb)[:5],
                     "orphans_right_not_in_left": len(vb - va), "orphan_examples_right": sorted(vb - va)[:5],
                     "left_rows": len(a), "left_join_rows": joined_rows, "duplication_risk": joined_rows > len(a),
                     "case_or_space_mismatch": len({v.strip().lower() for v in va} & {v.strip().lower() for v in vb}) > len(va & vb)})

write_json(out, {"primary_key_candidates": pk, "relationships": rels,
                 "tables": {t: {"rows": len(d), "columns": [str(c) for c in d.columns]} for t, d in tables.items()}})
print("PRIMARY KEY CANDIDATES (unique, no nulls):")
for t, c in pk.items():
    print(f"  {t}: {c or 'none (look for a composite key)'}")
print("RELATIONSHIPS:")
for r in rels:
    warn = "  !! LEFT JOIN WOULD DUPLICATE ROWS" if r["duplication_risk"] else ""
    print(f"  {r['left']}.{r['left_col']} -> {r['right']}.{r['right_col']}  {r['cardinality']}; overlap {r['overlap']:,}; "
          f"orphans left {r['orphans_left_not_in_right']:,} right {r['orphans_right_not_in_left']:,}; "
          f"left join rows {r['left_join_rows']:,} vs {r['left_rows']:,}{warn}")
print("WROTE", os.path.relpath(out, root))
