"""Build the analysis base (step 07) or the Excel dashboard (step 08) from a JSON spec.

Usage:
  python pivot_builder.py --spec "07 Analysis/analysis_spec.json" --mode v1 --out "07 Analysis/X_analysis_base_v1.xlsx"
  python pivot_builder.py --spec "07 Analysis/analysis_spec.json" --mode v1 --dashboard --out "08 Excel Dashboard/X_Dashboard_v1.xlsx"
  python pivot_builder.py --spec ... --expected-only        (only write expected_values.json from pandas)

Modes (the ladder in PROJECT_RULES.md):
  v1  native PivotTables + slicers (one pivot cache on the data table, refreshed by Excel when the file opens)
  v2  native PivotTables + report filters (page fields) instead of slicers
  v3  no PivotTables: formula summaries (SUMIFS/COUNTIFS) driven by dropdown selectors

--dashboard adds a first sheet "Dashboard": the slicers (v1) or selectors (v3), one compact table per
PivotTable that reads it (GETPIVOTDATA in v1/v2, cell links in v3), native charts, and a coverage table.

The spec format is documented in the da-analyze skill (references/analysis-spec.md). Outputs:
  the workbook, and <out folder>/expected_values.json (pandas values for every PivotTable cell and grand
  total, used by integrity_check.py and to validate Findings and dashboards).
Sources are read only. The output is written to a temp file first and renamed when complete."""
import os, re, sys, json, zipfile, argparse, math, datetime, shutil, importlib.util
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dakit import find_root, write_json
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--spec", required=True)
ap.add_argument("--mode", choices=["v1", "v2", "v3"], default="v1")
ap.add_argument("--out")
ap.add_argument("--dashboard", action="store_true")
ap.add_argument("--expected-only", action="store_true")
ap.add_argument("--root")
A = ap.parse_args()
root = find_root(A.root)
spec_path = os.path.join(root, A.spec) if not os.path.isabs(A.spec) else A.spec
SPEC = json.load(open(spec_path, encoding="utf-8"))
MODE = A.mode

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_X14 = "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main"
NS_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "application/vnd.openxmlformats-officedocument.spreadsheetml."
FMT = {"money": (4, "#,##0.00"), "int": (3, "#,##0"), "pct": (10, "0.00%"), "num": (2, "0.00"), "general": (0, "General")}
AGG = {"sum": None, "count": "count", "average": "average", "max": "max", "min": "min"}

# ---------------------------------------------------------------- data
def load_source():
    src = os.path.join(root, SPEC["source"])
    ext = os.path.splitext(src)[1].lower()
    names = [SPEC["data_table"]] + SPEC.get("other_tables", [])
    if ext in (".xlsx", ".xlsm"):
        d = pd.read_excel(src, sheet_name=names)
    else:
        d = {SPEC["data_table"]: pd.read_csv(src, low_memory=False)}
        for t in SPEC.get("other_tables", []):
            d[t] = pd.read_csv(os.path.join(os.path.dirname(src), f"{t}_final.csv"), low_memory=False)
    df = d[SPEC["data_table"]]
    hs = SPEC.get("helper_columns_script")
    if hs:
        p = os.path.join(root, hs)
        m = importlib.util.spec_from_file_location("helpers", p)
        mod = importlib.util.module_from_spec(m)
        m.loader.exec_module(mod)
        before = len(df)
        df = mod.add_helpers(df.copy())
        assert len(df) == before, "add_helpers must not change the row count"
    d[SPEC["data_table"]] = df
    return d

D = load_source()
DF = D[SPEC["data_table"]]
FIELDS = [str(c) for c in DF.columns]
CALC = SPEC.get("calculated_fields", [])
CALC_NAMES = [c["name"] for c in CALC]
ALLF = FIELDS + CALC_NAMES
FI = {n: i for i, n in enumerate(ALLF)}
SLICE = SPEC.get("slicers", [])
PIVOTS = []
for q in SPEC["questions"]:
    for p in q["pivots"]:
        p = dict(p); p["qid"] = q["id"]; p["sheet"] = q["sheet"]; p.setdefault("rows", []); p.setdefault("cols", [])
        p.setdefault("ignore_slicers", []); p.setdefault("chart", "bar"); p.setdefault("dashboard", True)
        PIVOTS.append(p)

for p in PIVOTS:
    for f in p["rows"] + p["cols"]:
        if f not in FIELDS:
            sys.exit(f"ERROR {p['name']}: axis field '{f}' is not a column of {SPEC['data_table']}")
        if pd.api.types.is_datetime64_any_dtype(DF[f]):
            sys.exit(f"ERROR {p['name']}: axis field '{f}' is a date. Add a text helper column (e.g. 'Order Month' = YYYY-MM) and use that.")
    for v in p["values"]:
        if v["field"] not in ALLF:
            sys.exit(f"ERROR {p['name']}: value field '{v['field']}' not found (columns or calculated_fields)")
        if v["field"] in CALC_NAMES and v.get("agg", "sum") != "sum":
            sys.exit(f"ERROR {p['name']}: calculated field '{v['field']}' must use agg sum")
    if MODE == "v3" and (len(p["rows"]) > 2 or len(p["cols"]) > 1):
        sys.exit(f"ERROR {p['name']}: v3 supports at most 2 row fields and 1 column field")
for f in SLICE:
    if f not in FIELDS:
        sys.exit(f"ERROR slicer field '{f}' not found")


def items_of(f):
    s = DF[f].dropna().unique().tolist()
    try:
        return sorted(s)
    except TypeError:
        return sorted(s, key=str)


ITEMS = {}
for f in set(SLICE) | {f for p in PIVOTS for f in p["rows"] + p["cols"]}:
    ITEMS[f] = items_of(f)

# ---------------------------------------------------------------- pandas expectations
TOK = re.compile(r"'([^']+)'|([A-Za-z_][A-Za-z0-9_]*)")


def calc_eval(formula, sums):
    def rep(m):
        name = m.group(1) or m.group(2)
        if name not in sums:
            raise KeyError(name)
        return f"__v[{name!r}]"
    expr = TOK.sub(rep, formula)
    try:
        r = eval(expr, {"__builtins__": {}}, {"__v": sums})
        return None if r is None or (isinstance(r, float) and (math.isinf(r) or math.isnan(r))) else float(r)
    except ZeroDivisionError:
        return None


def calc_inputs(formula):
    return [m.group(1) or m.group(2) for m in TOK.finditer(formula)]


def agg_value(df, v):
    f = v["field"]; a = v.get("agg", "sum")
    if f in CALC_NAMES:
        c = next(c for c in CALC if c["name"] == f)
        sums = {n: float(pd.to_numeric(df[n], errors="coerce").sum()) for n in calc_inputs(c["formula"])}
        return calc_eval(c["formula"], sums)
    s = df[f]
    if a == "count":
        return float(s.notna().sum())
    s = pd.to_numeric(s, errors="coerce")
    if a == "sum":
        return float(s.sum())
    if len(s.dropna()) == 0:
        return None
    return float({"average": s.mean, "max": s.max, "min": s.min}[a]())


def key(*parts):
    return "|".join(str(x) for x in parts)


def expected_for(p, df):
    """Cells keyed 'value caption|rowitem1|rowitem2|colitem' (missing parts are blank)."""
    out = {"grand_total": {}, "cells": {}}
    rows, cols = p["rows"], p["cols"]
    for v in p["values"]:
        cap = v["caption"]
        if v.get("show_as"):
            base = v["base_field"]
            axis = rows + cols
            groups = [g for g in axis if g != base]
            for gkey, gdf in ([((), df)] if not groups else df.groupby(groups, dropna=True)):
                gkey = gkey if isinstance(gkey, tuple) else (gkey,)
                vals = {b: agg_value(gdf[gdf[base] == b], dict(v, show_as=None)) for b in ITEMS[base]}
                prev = None
                for b in ITEMS[base]:
                    cur = vals[b]
                    pct = None if (prev in (None, 0) or cur is None) else (cur - prev) / prev
                    parts = dict(zip(groups, gkey)); parts[base] = b
                    rk = [parts.get(r, "") for r in rows]; ck = [parts.get(c, "") for c in cols]
                    out["cells"][key(cap, *rk, *ck)] = pct
                    prev = cur if gdf[gdf[base] == b].shape[0] else prev
            continue
        out["grand_total"][cap] = agg_value(df, v)
        if rows or cols:
            axis = rows + cols
            for k, g in df.groupby(axis, dropna=True):
                k = k if isinstance(k, tuple) else (k,)
                out["cells"][key(cap, *k)] = agg_value(g, v)
            if rows and cols:   # row and column totals
                for k, g in df.groupby(rows, dropna=True):
                    k = k if isinstance(k, tuple) else (k,)
                    out["cells"][key(cap, *k, "")] = agg_value(g, v)
                for k, g in df.groupby(cols, dropna=True):
                    k = k if isinstance(k, tuple) else (k,)
                    out["cells"][key(cap, *([""] * len(rows)), *k)] = agg_value(g, v)
            if len(rows) == 2:
                for k, g in df.groupby(rows[0], dropna=True):
                    out["cells"][key(cap, k, "", *([""] * len(cols)))] = agg_value(g, v)
    return out


EXP = {"mode": MODE, "data_rows": len(DF),
       "control_totals": {c: float(pd.to_numeric(DF[c], errors="coerce").sum()) for c in SPEC.get("control_totals", [])},
       "pivots": {p["name"]: {"question": p["qid"], "sheet": p["sheet"],
                               "calc_captions": [v["caption"] for v in p["values"] if v["field"] in CALC_NAMES],
                               "anchor": None, **expected_for(p, DF)} for p in PIVOTS}}
out = A.out and (os.path.join(root, A.out) if not os.path.isabs(A.out) else A.out)
exp_path = os.path.join(os.path.dirname(out) if out else os.path.dirname(spec_path), "expected_values.json")
write_json(exp_path, EXP)
print("WROTE", os.path.relpath(exp_path, root))
if A.expected_only:
    sys.exit(0)
if not out:
    sys.exit("ERROR: --out is required")

# ---------------------------------------------------------------- layout
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter as L
from openpyxl.styles import Font
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart, LineChart, Reference

BOLD = Font(bold=True)
safe_tbl = lambda s: "tbl" + re.sub(r"[^A-Za-z0-9_]", "", s)
DATA_TBL = safe_tbl(SPEC["data_table"])
qsheets = [q["sheet"] for q in SPEC["questions"]]
if len(set(qsheets)) != len(qsheets) or any(len(s) > 31 for s in qsheets):
    sys.exit("ERROR: question sheet names must be unique and at most 31 characters")


def est_height(p):
    page = len([f for f in SLICE if f not in p["rows"] + p["cols"] and f not in p["ignore_slicers"]]) if MODE == "v2" else 0
    if p["rows"]:
        h = DF[p["rows"]].drop_duplicates().dropna().shape[0]
        if len(p["rows"]) == 2:
            h += DF[p["rows"][0]].nunique()
    else:
        h = 1
    return h + 4 + (page + 1 if page else 0) + (1 if p["cols"] else 0)


# anchors: stacked down each question sheet with 4 spare rows between PivotTables
ANCH = {}
for q in SPEC["questions"]:
    r = 3
    for p in [x for x in PIVOTS if x["sheet"] == q["sheet"]]:
        page = len([f for f in SLICE if f not in p["rows"] + p["cols"] and f not in p["ignore_slicers"]]) if MODE == "v2" else 0
        top = r + (page + 1 if page else 0)        # page filters sit above the location
        ANCH[p["name"]] = (top, 1)
        r = top + est_height(p) + 4

wb = Workbook()
wb.remove(wb.active)
title = SPEC.get("title", "Analysis")
if A.dashboard:
    wsD = wb.create_sheet("Dashboard")
wsI = wb.create_sheet("Index")
for q in SPEC["questions"]:
    ws = wb.create_sheet(q["sheet"])
    ws["A1"] = f"{q['id']}: {q['title']}"; ws["A1"].font = BOLD
    if MODE == "v2":
        ws["A2"] = "Filters: use the report filters above each PivotTable."
if MODE == "v1" and not A.dashboard:
    wsS = wb.create_sheet("Slicers")
    wsS["A1"] = "Slicers: " + ", ".join(SLICE) + ". Each slicer filters every PivotTable on the question sheets."
if MODE == "v3":
    wsC = wsD if A.dashboard else wb.create_sheet("Controls")
    wsLst = wb.create_sheet("Lists")
for t in [SPEC["data_table"]] + SPEC.get("other_tables", []):
    wb.create_sheet(t)

# data sheets as Excel Tables
for t in [SPEC["data_table"]] + SPEC.get("other_tables", []):
    ws, df = wb[t], D[t]
    ws.append([str(c) for c in df.columns])
    datecols = [i for i, c in enumerate(df.columns) if pd.api.types.is_datetime64_any_dtype(df[c])]
    for row in df.itertuples(index=False, name=None):
        ws.append([None if (v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NaT) else
                   (v.to_pydatetime() if hasattr(v, "to_pydatetime") else v) for v in row])
    for i in datecols:
        for c in ws.iter_cols(min_col=i + 1, max_col=i + 1, min_row=2):
            for x in c:
                x.number_format = "yyyy-mm-dd"
    ref = f"A1:{L(len(df.columns))}{len(df) + 1}"
    tb = Table(displayName=safe_tbl(t), ref=ref)
    tb.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=False)
    ws.add_table(tb)

# Index
wsI["A1"] = f"{title}: {'Excel dashboard' if A.dashboard else 'analysis base'} ({MODE})"; wsI["A1"].font = BOLD
for j, h in enumerate(["Sheet", "Question", "Content", "Tables"], 1):
    wsI.cell(3, j, h).font = BOLD
r = 4
for q in SPEC["questions"]:
    wsI.append([q["sheet"], q["id"], q["title"], ", ".join(p["name"] for p in PIVOTS if p["sheet"] == q["sheet"])]); r += 1
notes = [f"Data: {DATA_TBL} on sheet '{SPEC['data_table']}' ({len(DF):,} rows), copied from {SPEC['source']} (never modified)."]
notes += [f"Calculated field {c['name']} = {c['formula']}" for c in CALC]
notes += {"v1": ["Native PivotTables on one pivot cache; they refresh when the file opens in Excel. Slicers: " + ", ".join(SLICE) + "."],
          "v2": ["Native PivotTables with report filters (" + ", ".join(SLICE) + ") above each table."],
          "v3": ["Formula summaries (SUMIFS/COUNTIFS) driven by the selectors on the " + ("Dashboard" if A.dashboard else "Controls") + " sheet."]}[MODE]
notes += SPEC.get("notes", [])
for n_ in notes:
    r += 1; wsI.cell(r, 1, n_)
wsI.column_dimensions["A"].width = 24; wsI.column_dimensions["C"].width = 90

# ---------------------------------------------------------------- v3 formula tables
V3_CELLS = {}   # pivot name -> {expected key: cell ref "Sheet!$C$5"}
SEL = {}        # slicer field -> absolute selector ref
if MODE == "v3":
    wsC["A3" if not A.dashboard else "A3"] = None
    base_r = 4 if not A.dashboard else 4
    if not A.dashboard:
        wsC["A1"] = "Selectors: pick a value or (All). Every summary table updates."; wsC["A1"].font = BOLD
    for i, f in enumerate(SLICE):
        rr = base_r + i
        wsC.cell(rr, 1, f).font = BOLD
        wsC.cell(rr, 2, "(All)")
        wsLst.cell(1, i + 1, f)
        wsLst.cell(2, i + 1, "(All)")
        for k, it in enumerate(ITEMS[f]):
            wsLst.cell(3 + k, i + 1, it)
        dv = DataValidation(type="list", formula1=f"=Lists!${L(i + 1)}$2:${L(i + 1)}${2 + len(ITEMS[f])}", allow_blank=False)
        wsC.add_data_validation(dv); dv.add(wsC.cell(rr, 2))
        SEL[f] = f"'{wsC.title}'!$B${rr}"
    TBLREF = lambda col: f"{DATA_TBL}[{col}]".replace("]", "]").replace("[", "[")

    def colref(c):
        c2 = c.replace("'", "''").replace("[", "'[").replace("]", "']").replace("#", "'#")
        return f"{DATA_TBL}[{c2}]"

    def crit(p, fixed):
        parts = []
        for f, val in fixed:
            parts.append(f"{colref(f)}," + (str(val) if isinstance(val, (int, float)) and not isinstance(val, bool) else '"' + str(val).replace('"', '""') + '"'))
        for f in SLICE:
            if f in p["ignore_slicers"] or f in [x for x, _ in fixed]:
                continue
            parts.append(f'{colref(f)},IF({SEL[f]}="(All)","<>",{SEL[f]})')
        return parts

    def v3formula(p, v, fixed):
        cs = crit(p, fixed)
        f = v["field"]
        if f in CALC_NAMES:
            c = next(c for c in CALC if c["name"] == f)
            sums = {n: (f"SUMIFS({colref(n)}," + ",".join(cs) + ")" if cs else f"SUM({colref(n)})") for n in calc_inputs(c["formula"])}
            expr = TOK.sub(lambda m: sums[m.group(1) or m.group(2)], c["formula"])
            return f'=IFERROR({expr},"")'
        a = v.get("agg", "sum")
        if a == "count":
            return f"=COUNTIFS({colref(f)},\"<>\"" + ("," + ",".join(cs) if cs else "") + ")"
        fn = {"sum": "SUMIFS", "average": "AVERAGEIFS", "max": "MAXIFS", "min": "MINIFS"}[a]
        if not cs:
            return f"={ {'sum': 'SUM', 'average': 'AVERAGE', 'max': 'MAX', 'min': 'MIN'}[a] }({colref(f)})".replace("{ ", "").replace(" }", "")
        return f'=IFERROR({fn}({colref(f)},' + ",".join(cs) + '),"")'

# ---------------------------------------------------------------- write v3 tables on question sheets
CACHED = {}   # (sheet, ref) -> value, injected into the saved XML
CHECKS = []   # every formula cell with its pandas value, for integrity_check.py --recalc


def write_grid(ws, top, p, formula_for, label_cols):
    """Generic grid writer used by v3 tables and dashboard mirrors. Returns (last_row, mapping, value columns)."""
    rows, cols = p["rows"], p["cols"]
    exp = EXP["pivots"][p["name"]]["cells"]; gt = EXP["pivots"][p["name"]]["grand_total"]
    rkeys = [tuple(x) for x in DF[rows].drop_duplicates().dropna().sort_values(rows).values.tolist()] if rows else [()]
    citems = ITEMS[cols[0]] if cols else [None]
    hdr = list(rows) or [""]
    colspec = []
    for v in p["values"]:
        for ci in citems:
            colspec.append((v, ci))
            hdr.append(v["caption"] if ci is None else f"{ci}" if len(p["values"]) == 1 else f"{v['caption']} {ci}")
    for j, h in enumerate(hdr, 1):
        ws.cell(top, j, h).font = BOLD
    mapping = {}
    r = top + 1
    for rk in rkeys:
        for j, it in enumerate(rk, 1):
            ws.cell(r, j, it)
        if not rows:
            ws.cell(r, 1, "Total")
        for k, (v, ci) in enumerate(colspec):
            c = ws.cell(r, max(1, len(rows)) + 1 + k)
            c.value = formula_for(p, v, list(zip(rows, rk)) + ([(cols[0], ci)] if ci is not None else []), r, max(1, len(rows)) + 1 + k)
            c.number_format = FMT[v.get("format", "general")][1]
            ek = key(v["caption"], *rk, *([ci] if ci is not None else []))
            val = gt.get(v["caption"]) if (not rows and ci is None and not v.get("show_as")) else exp.get(ek)
            mapping[ek] = f"'{ws.title}'!${L(c.column)}${r}"
            if isinstance(val, (int, float)):
                CACHED[(ws.title, f"{L(c.column)}{r}")] = val
                CHECKS.append({"sheet": ws.title, "cell": f"{L(c.column)}{r}", "pivot": p["name"], "key": ek, "expected": val,
                               "calc": v["field"] in CALC_NAMES})
        r += 1
    return r - 1, mapping, len(colspec)


def v3_cell_formula(p, v, fixed, r, c):
    if v.get("show_as"):
        base = v["base_field"]
        # previous item of the base field on the same axis
        if base in p["cols"]:
            return f'=IFERROR(({L(c)}{r}-{L(c - 1)}{r})/{L(c - 1)}{r},"")' if c > max(1, len(p["rows"])) + 1 else '=""'
        return f'=IFERROR(({L(c)}{r}-{L(c)}{r - 1})/{L(c)}{r - 1},"")'
    return v3formula(p, v, fixed)


if MODE == "v3":
    for q in SPEC["questions"]:
        ws = wb[q["sheet"]]
        for p in [x for x in PIVOTS if x["sheet"] == q["sheet"]]:
            top = ANCH[p["name"]][0]
            ws.cell(top - 1, 1, p["name"]).font = BOLD
            # show_as needs the underlying measure in the table: written as a hidden helper value column
            fixv = []
            for v in p["values"]:
                fixv.append(dict(v, show_as=None, caption=v["caption"] + " (base)") if v.get("show_as") else None)
            p2 = dict(p)
            p2["values"] = [x for pair in zip([f for f in fixv], p["values"]) for x in pair if x is not None]
            # expectations for base helper captions
            for v in p["values"]:
                if v.get("show_as"):
                    vv = dict(v, show_as=None, caption=v["caption"] + " (base)")
                    e = expected_for(dict(p, values=[vv]), DF)
                    EXP["pivots"][p["name"]]["cells"].update(e["cells"]); EXP["pivots"][p["name"]]["grand_total"].update(e["grand_total"])

            def ff(pp, v, fixed, r, c, _p=p2):
                if v.get("show_as"):
                    # base column is the column right before this one when there is no column field
                    if _p["cols"]:
                        n = len(ITEMS[_p["cols"][0]])
                        if v["base_field"] in _p["cols"]:
                            first = max(1, len(_p["rows"])) + 1
                            pos = (c - first) % n
                            return '=""' if pos == 0 else f'=IFERROR(({L(c - n)}{r}-{L(c - n - 1)}{r})/{L(c - n - 1)}{r},"")'
                        return f'=IFERROR(({L(c - n)}{r}-{L(c - n)}{r - 1})/{L(c - n)}{r - 1},"")'
                    return '=""' if r == top + 1 else f'=IFERROR(({L(c - 1)}{r}-{L(c - 1)}{r - 1})/{L(c - 1)}{r - 1},"")'
                return v3formula(pp, v, fixed)
            last, mapping, _ = write_grid(ws, top, p2, ff, None)
            V3_CELLS[p["name"]] = mapping
        ws.column_dimensions["A"].width = 22
    write_json(exp_path, EXP)

# ---------------------------------------------------------------- dashboard sheet (mirrors + charts + coverage)
COVER = []
SL_R0 = 10        # 0-based row index where the slicer band starts (row 11)
if A.dashboard:
    from openpyxl.styles import PatternFill, Alignment, Border, Side
    from openpyxl.chart.label import DataLabelList
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.drawing.line import LineProperties
    NAVY, TEAL, AMBER, RED, GREY, INK, PALE = "1F3A5F", "2A9D8F", "E9A23B", "D1495B", "8D99AE", "1B2733", "EEF3F8"
    ws = wsD
    wsDD = wb.create_sheet("Dashboard_Data", index=2)
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = NAVY
    wsDD.sheet_properties.tabColor = GREY
    NC = 24
    for j in range(1, NC + 1):
        ws.column_dimensions[L(j)].width = 7.6
    fill = lambda h: PatternFill("solid", start_color=h, end_color=h)
    white = Side(style="thick", color="FFFFFF")

    def band(row, text, h=24, size=11, color=NAVY, fc="FFFFFF", bold=True):
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=NC)
        c = ws.cell(row, 1, text); c.fill = fill(color); c.font = Font(bold=bold, size=size, color=fc)
        c.alignment = Alignment(vertical="center", indent=1, wrap_text=True)
        ws.row_dimensions[row].height = h

    band(1, SPEC.get("dashboard", {}).get("title", title + " dashboard"), h=38, size=20)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=NC)
    c = ws.cell(2, 1, " ".join(SPEC.get("dashboard", {}).get("notes", [])) + "  Data: 103,024 bookings, July 2024.")
    c.font = Font(size=10, italic=True, color="555F6B"); c.alignment = Alignment(indent=1, vertical="center")
    ws.row_dimensions[2].height = 20; ws.row_dimensions[3].height = 8

    def gp_ref(pn, cap):
        p = next(x for x in PIVOTS if x["name"] == pn)
        return f"'{p['sheet']}'!${L(ANCH[pn][1])}${ANCH[pn][0]}"
    KPI = [("Bookings", "PT_Q01", "Bookings", "int", "Q1"), ("Completed rides", "PT_Q01", "Completed Rides", "int", "Q1"),
           ("Success rate", "PT_Q01", "Success Rate", "pct", "Q1"), ("Revenue (INR)", "PT_Q01", "Revenue (INR)", "int", "Q1"),
           ("Average fare (INR)", "PT_Q01", "Average Fare (INR)", "money", "Q1"), ("Failed bookings", "PT_Q08", "Failed Bookings", "int", "Q8"),
           ("Driver cancellations", "PT_Q10", "Driver Cancellations", "int", "Q10"), ("Quoted value lost (INR)", "PT_Q11", "Quoted Value Lost (INR)", "int", "Q11")]
    for i, (lab, pn, cap, fmt, qid) in enumerate(KPI):
        rl = 4 if i < 4 else 7
        c0 = 1 + (i % 4) * 6
        for rr, txt in ((rl, lab.upper()), (rl + 1, None)):
            ws.merge_cells(start_row=rr, start_column=c0, end_row=rr, end_column=c0 + 5)
            for cc in range(c0, c0 + 6):
                ws.cell(rr, cc).fill = fill(PALE)
        a = ws.cell(rl, c0, lab.upper()); a.font = Font(size=9, bold=True, color="5B6B7B"); a.alignment = Alignment(horizontal="center", vertical="bottom")
        v = ws.cell(rl + 1, c0)
        v.value = f'=IFERROR(GETPIVOTDATA("{cap}",{gp_ref(pn, cap)}),0)'
        v.font = Font(size=22, bold=True, color=NAVY); v.alignment = Alignment(horizontal="center", vertical="center")
        v.number_format = {"int": "#,##0", "pct": "0.0%", "money": "#,##0.00"}[fmt]
        for rr in (rl, rl + 1):
            ws.cell(rr, c0).border = Border(left=white); ws.cell(rr, c0 + 5).border = Border(right=white)
        ws.row_dimensions[rl].height = 20; ws.row_dimensions[rl + 1].height = 40
        gtv = EXP["pivots"][pn]["grand_total"].get(cap)
        if isinstance(gtv, (int, float)):
            CACHED[("Dashboard", f"{L(c0)}{rl + 1}")] = gtv
            CHECKS.append({"sheet": "Dashboard", "cell": f"{L(c0)}{rl + 1}", "pivot": pn, "key": key(cap), "expected": gtv,
                           "calc": next(vv["field"] for pp in PIVOTS if pp["name"] == pn for vv in pp["values"] if vv["caption"] == cap) in CALC_NAMES})
    ws.row_dimensions[6].height = 6; ws.row_dimensions[9].height = 8
    band(SL_R0, "FILTERS   Click a button to filter (Ctrl+click for several, the funnel icon clears). Every number and chart below updates. "
                "First time: click Enable Editing, then Data > Refresh All.", h=30, size=10, color="3B4B5E")
    for rr in range(SL_R0 + 1, SL_R0 + 14):
        ws.row_dimensions[rr].height = 20
    ws.row_dimensions[SL_R0 + 13].height = 8

    # ---- chart data on Dashboard_Data (GETPIVOTDATA tables), stacked down with gaps
    def mf1(pp, v, fixed, rr, cc, _p=None):
        pref = gp_ref(pp["name"], None)
        args = "".join(f',"{f}",' + (str(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else '"' + str(x).replace('"', '""') + '"') for f, x in fixed)
        blank = '""' if (v.get("show_as") or v["field"] in CALC_NAMES or v.get("agg") in ("average", "max", "min")) else "0"
        return f'=IFERROR(GETPIVOTDATA("{v["caption"]}",{pref}{args}),{blank})'
    wsDD["A1"] = "Chart data for the Dashboard sheet. These cells read the PivotTables (GETPIVOTDATA); do not type here."; wsDD["A1"].font = BOLD
    TB = {}
    rr_ = 3
    for pn in ["PT_Q02", "PT_Q03", "PT_Q04", "PT_Q05", "PT_Q06", "PT_Q07", "PT_Q09", "PT_Q10", "PT_Q11", "PT_Q12"]:
        p = next(x for x in PIVOTS if x["name"] == pn)
        wsDD.cell(rr_, 1, f"{p['qid']}  {pn}").font = Font(bold=True, color=NAVY)
        last, _m, nv = write_grid(wsDD, rr_ + 1, p, mf1, None)
        TB[pn] = (rr_ + 1, last)
        rr_ = last + 3
    # Q8: top 10 pickup areas (fixed list by overall bookings; GETPIVOTDATA returns 0 for areas hidden by a slicer)
    p8 = next(x for x in PIVOTS if x["name"] == "PT_Q08")
    top10 = DF.groupby("Pickup_Location")["Bookings"].sum().sort_values(ascending=False, kind="mergesort").head(10).index.tolist()
    wsDD.cell(rr_, 1, "Q8  PT_Q08 (top 10 pickup areas by bookings, all data)").font = Font(bold=True, color=NAVY)
    for j, h_ in enumerate(["Pickup_Location", "Bookings", "Failed Bookings", "Failure Rate"], 1):
        wsDD.cell(rr_ + 1, j, h_).font = BOLD
    for k, area in enumerate(top10):
        r_ = rr_ + 2 + k
        wsDD.cell(r_, 1, area)
        for j, (cap, fmtk) in enumerate([("Bookings", "int"), ("Failed Bookings", "int"), ("Failure Rate", "pct")], 2):
            cell = wsDD.cell(r_, j, f'=IFERROR(GETPIVOTDATA("{cap}",{gp_ref("PT_Q08", None)},"Pickup_Location","{area}"),0)')
            cell.number_format = FMT[fmtk][1]
            ev = EXP["pivots"]["PT_Q08"]["cells"].get(key(cap, area))
            if isinstance(ev, (int, float)):
                CACHED[("Dashboard_Data", f"{L(j)}{r_}")] = ev
                CHECKS.append({"sheet": "Dashboard_Data", "cell": f"{L(j)}{r_}", "pivot": "PT_Q08", "key": key(cap, area), "expected": ev,
                               "calc": cap == "Failure Rate"})
    TB["PT_Q08"] = (rr_ + 1, rr_ + 1 + len(top10))
    wsDD.column_dimensions["A"].width = 30
    for j in range(2, 8):
        wsDD.column_dimensions[L(j)].width = 16

    def chart(kind, qid, ttl, pn, cols, anchor, colors, pct=False, labels=False, horiz=False, fmt=None, ymin=None, legend=None):
        first, last = TB[pn]
        if kind == "line":
            ch = LineChart()
        else:
            ch = BarChart(); ch.type = "bar" if horiz else "col"
        ch.title = f"{qid} · {ttl}"
        ch.height, ch.width = 8.2, 17.8
        for cidx in cols:
            ch.add_data(Reference(wsDD, min_col=cidx, min_row=first, max_row=last), titles_from_data=True)
        ch.set_categories(Reference(wsDD, min_col=1, min_row=first + 1, max_row=last))
        for s, colr in zip(ch.series, colors):
            if kind == "line":
                s.graphicalProperties.line.solidFill = colr; s.graphicalProperties.line.width = 28000; s.smooth = False
            else:
                s.graphicalProperties.solidFill = colr; s.graphicalProperties.line.solidFill = colr
        if kind != "line":
            ch.gapWidth = 60
        ch.x_axis.delete = False; ch.y_axis.delete = False
        if horiz:
            ch.x_axis.scaling.orientation = "maxMin"
        ch.y_axis.majorGridlines.spPr = GraphicalProperties(ln=LineProperties(solidFill="E3E7EC"))
        ch.y_axis.number_format = "0%" if pct else "#,##0"
        ch.y_axis.numFmt.sourceLinked = False if ch.y_axis.numFmt is not None else None
        if ymin is not None:
            ch.y_axis.scaling.min = ymin
        if labels:
            ch.dataLabels = DataLabelList(); ch.dataLabels.showVal = True
            for a in ("showSerName", "showCatName", "showLegendKey", "showPercent"):
                setattr(ch.dataLabels, a, False)
            ch.dataLabels.numFmt = fmt or ("0.0%" if pct else "#,##0")
        if len(cols) > 1:
            ch.legend.position = "b"
        else:
            ch.legend = None
        ws.add_chart(ch, anchor)

    SECTIONS = [
        ("OUTCOMES AND MONEY", [[("bar", "Q2", "Booking outcome mix (bookings)", "PT_Q02", [2], [NAVY], dict(labels=True, horiz=True)),
                                 ("bar", "Q11", "Quoted value lost by status (INR)", "PT_Q11", [2], [RED], dict(labels=True, horiz=True))]]),
        ("WHEN DEMAND HAPPENS", [[("line", "Q3", "Daily bookings", "PT_Q03", [2], [NAVY], {}),
                                  ("bar", "Q4", "Hourly demand (bookings by hour)", "PT_Q04", [2], [TEAL], {})],
                                 [("line", "Q3", "Daily success rate", "PT_Q03", [3], [TEAL], dict(pct=True)),
                                  ("line", "Q5", "Success rate by hour of day", "PT_Q05", [2], [AMBER], dict(pct=True))]]),
        ("VEHICLE TYPES", [[("bar", "Q6", "Bookings by vehicle type", "PT_Q06", [2], [NAVY], dict(labels=True)),
                            ("bar", "Q6", "Revenue by vehicle type (INR)", "PT_Q06", [3], [TEAL], dict(labels=True))],
                           [("bar", "Q7", "Cancel and not-found rates by vehicle", "PT_Q07", [2, 3, 4], [AMBER, RED, GREY], dict(pct=True)),
                            ("bar", "Q12", "Average turnaround (minutes) by vehicle", "PT_Q12", [2, 3], [NAVY, TEAL], dict(fmt="0.0"))]]),
        ("SERVICE QUALITY, PICKUP AREAS AND CANCELLATION REASONS", [[("bar", "Q12", "Average ratings by vehicle (out of 5)", "PT_Q12", [4, 5], [AMBER, NAVY], dict(fmt="0.00", ymin=0)),
                                                                     ("bar", "Q8", "Top 10 pickup areas: bookings and failed bookings", "PT_Q08", [2, 3], [NAVY, RED], dict(horiz=True))],
                                                                    [("bar", "Q9", "Customer cancellation reasons", "PT_Q09", [2], [AMBER], dict(labels=True, horiz=True)),
                                                                     ("bar", "Q10", "Driver cancellation reasons", "PT_Q10", [2], [RED], dict(labels=True, horiz=True))]]),
    ]
    r = SL_R0 + 15           # first row after slicers (1-based)
    where = {}
    for stitle, rows_ in SECTIONS:
        band(r, stitle, h=26, size=11); r += 1
        for pair in rows_:
            for k, (kind, qid, ttl, pn, cols, colors, kw) in enumerate(pair):
                anchor = f"{L(1 + k * 12)}{r}"
                chart(kind, qid, ttl, pn, cols, anchor, colors, **kw)
                where.setdefault(qid, []).append((anchor, {"line": "line chart", "bar": "bar chart"}[kind]))
            for rr in range(r, r + 17):
                ws.row_dimensions[rr].height = 20
            r += 17
    r += 1
    band(r, "COVERAGE   Every selected question and where it appears", h=26, size=11, color="3B4B5E"); r += 1
    spans = [(1, 2), (3, 11), (12, 17), (18, 24)]
    for j, h_ in enumerate(["Question", "Title", "Where on this sheet", "Source PivotTable"]):
        ws.merge_cells(start_row=r, start_column=spans[j][0], end_row=r, end_column=spans[j][1])
        cc = ws.cell(r, spans[j][0], h_); cc.font = BOLD; cc.fill = fill(PALE)
    for q in SPEC["questions"]:
        r += 1
        wh = "KPI cards (top)" if q["id"] == "Q1" else "; ".join(f"{a} ({t})" for a, t in where.get(q["id"], []))
        if q["id"] in ("Q8", "Q10", "Q11"):
            wh = ("KPI card (top); " if q["id"] != "Q8" else "KPI card (top); ") + wh
        row = [q["id"], q["title"], wh, ", ".join(p["name"] for p in PIVOTS if p["sheet"] == q["sheet"])]
        COVER.append(tuple(row))
        for j, x in enumerate(row):
            ws.merge_cells(start_row=r, start_column=spans[j][0], end_row=r, end_column=spans[j][1])
            ws.cell(r, spans[j][0], x).alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A3"
    ws.sheet_view.zoomScale = 90

if MODE == "v3" and A.dashboard:
    wsD.cell(4 + len(SLICE), 1, "Selectors above: pick a value or (All).")

EXP["cell_checks"] = CHECKS
write_json(exp_path, EXP)
tmp = out + ".openpyxl.tmp"
os.makedirs(os.path.dirname(out), exist_ok=True)
wb.save(tmp)

# ---------------------------------------------------------------- XML: pivots, slicers, cached values
z = zipfile.ZipFile(tmp)
parts = {n: z.read(n) for n in z.namelist()}
z.close()
os.remove(tmp)
P = lambda n: parts[n].decode("utf-8")
wbx = P("xl/workbook.xml")
wrels = P("xl/_rels/workbook.xml.rels")
ct = P("[Content_Types].xml")
def _attr(tag, a):
    m = re.search(r'\s' + re.escape(a) + r'="([^"]*)"', tag)
    return m.group(1) if m else None
from xml.sax.saxutils import unescape as _unesc
sheet_rid = {_unesc(_attr(t, "name")): (_attr(t, "sheetId"), _attr(t, "r:id")) for t in re.findall(r"<sheet\s[^>]*>", wbx)}
rid_target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="/?(?:xl/)?([^"]+)"', wrels)) or {}
if not rid_target:
    rid_target = {m.group(2): m.group(1) for m in re.finditer(r'Target="/?(?:xl/)?([^"]+)"[^>]*Id="(rId\d+)"', wrels)}
SHEETFILE = {n: "xl/" + rid_target[rid].lstrip("/") for n, (sid, rid) in sheet_rid.items()}
SHEETID = {n: sid for n, (sid, rid) in sheet_rid.items()}
ct_add, wb_rel_add = [], []
next_wb_rid = max(int(x[3:]) for x in re.findall(r'Id="(rId\d+)"', wrels)) + 1


def sheet_rels_add(sheet, rels_xml_list):
    """Append relationships to a sheet's rels file; returns the new rIds."""
    sf = SHEETFILE[sheet]
    rp = os.path.dirname(sf) + "/_rels/" + os.path.basename(sf) + ".rels"
    cur = P(rp) if rp in parts else f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{PKG}"></Relationships>'
    used = [int(x) for x in re.findall(r'Id="rId(\d+)"', cur)]
    nxt = (max(used) if used else 0) + 1
    ids = []
    for typ, target in rels_xml_list:
        cur = cur.replace("</Relationships>", f'<Relationship Id="rId{nxt}" Type="{typ}" Target="{target}"/></Relationships>')
        ids.append(f"rId{nxt}"); nxt += 1
    parts[rp] = cur.encode()
    return ids


# cached values for formula cells (so values show even before recalculation)
by_sheet = {}
for (sh, ref), val in CACHED.items():
    by_sheet.setdefault(sh, {})[ref] = val
for sh, vals in by_sheet.items():
    x = P(SHEETFILE[sh])
    def put_v(m):
        ref = m.group(2)
        if ref in vals:
            return f'{m.group(1)}<f>{m.group(3)}</f><v>{repr(float(vals[ref]))}</v></c>'
        return m.group(0)
    x = re.sub(r'(<c r="([A-Z]+\d+)"[^>]*>)<f>(.*?)</f>(?:<v\s*/>|<v>[^<]*</v>)?</c>', put_v, x)
    parts[SHEETFILE[sh]] = x.encode()

n_pivots = n_slicers = 0
if MODE in ("v1", "v2"):
    def shared_xml(f):
        if f not in ITEMS:
            return "<sharedItems/>"
        v = ITEMS[f]
        miss = DF[f].isna().any()
        if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v) and v:
            isint = all(float(x).is_integer() for x in v)
            return (f'<sharedItems containsSemiMixedTypes="0" containsString="0" containsNumber="1"' + (' containsInteger="1"' if isint else "") +
                    (' containsBlank="1"' if miss else "") + f' minValue="{min(v)}" maxValue="{max(v)}" count="{len(v) + miss}">' +
                    "".join(f'<n v="{int(x) if isint else x}"/>' for x in v) + ("<m/>" if miss else "") + "</sharedItems>")
        return (f'<sharedItems' + (' containsBlank="1"' if miss else "") + f' count="{len(v) + miss}">' +
                "".join(f'<s v="{escape(str(x))}"/>' for x in v) + ("<m/>" if miss else "") + "</sharedItems>")

    cf = "".join(f'<cacheField name="{escape(n)}" numFmtId="0">{shared_xml(n)}</cacheField>' for n in FIELDS)
    cf += "".join(f'<cacheField name="{escape(c["name"])}" numFmtId="0" formula="{escape(c["formula"])}" databaseField="0"/>' for c in CALC)
    parts["xl/pivotCache/pivotCacheDefinition1.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<pivotCacheDefinition xmlns="{NS_MAIN}" xmlns:r="{NS_R}" r:id="rId1" '
        f'refreshOnLoad="1" refreshedBy="Data Analysis Build kit" refreshedDate="45000" createdVersion="6" refreshedVersion="6" minRefreshableVersion="3" recordCount="0">'
        f'<cacheSource type="worksheet"><worksheetSource name="{DATA_TBL}"/></cacheSource><cacheFields count="{len(ALLF)}">{cf}</cacheFields>'
        f'<extLst><ext uri="{{725AE2AE-9491-48be-B2B4-4EB974FC3084}}" xmlns:x14="{NS_X14}"><x14:pivotCacheDefinition pivotCacheId="1"/></ext></extLst>'
        f'</pivotCacheDefinition>').encode()
    parts["xl/pivotCache/pivotCacheRecords1.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<pivotCacheRecords xmlns="{NS_MAIN}" xmlns:r="{NS_R}" count="0"/>'.encode()
    parts["xl/pivotCache/_rels/pivotCacheDefinition1.xml.rels"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{PKG}">'
        f'<Relationship Id="rId1" Type="{REL}pivotCacheRecords" Target="pivotCacheRecords1.xml"/></Relationships>').encode()
    ct_add += [f'<Override PartName="/xl/pivotCache/pivotCacheDefinition1.xml" ContentType="{CT}pivotCacheDefinition+xml"/>',
               f'<Override PartName="/xl/pivotCache/pivotCacheRecords1.xml" ContentType="{CT}pivotCacheRecords+xml"/>']
    cache_rid = f"rId{next_wb_rid}"; next_wb_rid += 1
    wb_rel_add.append(f'<Relationship Id="{cache_rid}" Type="{REL}pivotCacheDefinition" Target="pivotCache/pivotCacheDefinition1.xml"/>')

    def items_xml(f):
        n = len(ITEMS[f]) + (1 if DF[f].isna().any() else 0)
        return f'<items count="{n + 1}">' + "".join(f'<item x="{i}"/>' for i in range(n)) + '<item t="default"/></items>'

    sheet_pts = {}
    for k, p in enumerate(PIVOTS, start=1):
        rows, cols = p["rows"], p["cols"]
        page = [f for f in SLICE if f not in rows + cols and f not in p["ignore_slicers"]] if MODE == "v2" else []
        dataf = {v["field"] for v in p["values"]}
        pf = []
        for f in ALLF:
            attrs, inner = ['showAll="0"'], ""
            if f in rows or f in cols or f in page:
                attrs.insert(0, f'axis="{"axisRow" if f in rows else "axisCol" if f in cols else "axisPage"}"'); inner = items_xml(f)
            elif f in ITEMS:
                inner = items_xml(f)      # slicer fields not on an axis still list their items
            if f in dataf:
                attrs.insert(0, 'dataField="1"')
            if f in CALC_NAMES:
                attrs += ['dragToRow="0"', 'dragToCol="0"', 'dragToPage="0"', 'defaultSubtotal="0"']
                inner = ""
            pf.append(f'<pivotField {" ".join(attrs)}>{inner}</pivotField>' if inner else f'<pivotField {" ".join(attrs)}/>')
        ar, ac = ANCH[p["name"]]
        x = f'<location ref="{L(ac)}{ar}" firstHeaderRow="1" firstDataRow="1" firstDataCol="1"' + (f' rowPageCount="{len(page)}" colPageCount="1"' if page else "") + "/>"
        x += f'<pivotFields count="{len(ALLF)}">{"".join(pf)}</pivotFields>'
        if rows:
            x += f'<rowFields count="{len(rows)}">' + "".join(f'<field x="{FI[f]}"/>' for f in rows) + "</rowFields>"
        cfs = [FI[f] for f in cols] + ([-2] if len(p["values"]) > 1 else [])
        if cfs:
            x += f'<colFields count="{len(cfs)}">' + "".join(f'<field x="{i}"/>' for i in cfs) + "</colFields>"
        if page:
            x += f'<pageFields count="{len(page)}">' + "".join(f'<pageField fld="{FI[f]}" hier="-1"/>' for f in page) + "</pageFields>"
        dfx = []
        for v in p["values"]:
            nf = FMT[v.get("format", "general")][0]
            sub = AGG[v.get("agg", "sum")] if v["field"] not in CALC_NAMES else None
            sa = f' subtotal="{sub}"' if sub else ""
            if v.get("show_as"):
                if v["base_field"] not in rows + cols:
                    sys.exit(f"ERROR {p['name']}: base_field {v['base_field']} must be a row or column field")
                dfx.append(f'<dataField name="{escape(v["caption"])}" fld="{FI[v["field"]]}"{sa} showDataAs="percentDiff" baseField="{FI[v["base_field"]]}" baseItem="1048828" numFmtId="{nf}"/>')
            else:
                dfx.append(f'<dataField name="{escape(v["caption"])}" fld="{FI[v["field"]]}"{sa} baseField="0" baseItem="0" numFmtId="{nf}"/>')
        x += f'<dataFields count="{len(dfx)}">{"".join(dfx)}</dataFields>'
        x += '<pivotTableStyleInfo name="PivotStyleLight16" showRowHeaders="1" showColHeaders="1" showRowStripes="0" showColStripes="0" showLastColumn="1"/>'
        parts[f"xl/pivotTables/pivotTable{k}.xml"] = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<pivotTableDefinition xmlns="{NS_MAIN}" name="{escape(p["name"])}" cacheId="1" '
            f'applyNumberFormats="0" applyBorderFormats="0" applyFontFormats="0" applyPatternFormats="0" applyAlignmentFormats="0" '
            f'applyWidthHeightFormats="1" dataCaption="Values" updatedVersion="6" minRefreshableVersion="3" useAutoFormatting="1" '
            f'itemPrintTitles="1" createdVersion="6" indent="0" outline="1" outlineData="1" multipleFieldFilters="0">{x}</pivotTableDefinition>').encode()
        parts[f"xl/pivotTables/_rels/pivotTable{k}.xml.rels"] = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{PKG}">'
            f'<Relationship Id="rId1" Type="{REL}pivotCacheDefinition" Target="../pivotCache/pivotCacheDefinition1.xml"/></Relationships>').encode()
        ct_add.append(f'<Override PartName="/xl/pivotTables/pivotTable{k}.xml" ContentType="{CT}pivotTable+xml"/>')
        sheet_pts.setdefault(p["sheet"], []).append(k)
    for sh, ks in sheet_pts.items():
        sheet_rels_add(sh, [(f"{REL}pivotTable", f"../pivotTables/pivotTable{k}.xml") for k in ks])
    n_pivots = len(PIVOTS)

    wb_ext, defined = "", ""
    if MODE == "v1" and SLICE:
        sc_refs = []
        for i, f in enumerate(SLICE, start=1):
            cname = "Slicer_" + re.sub(r"[^A-Za-z0-9_]", "_", f)
            pts = "".join(f'<pivotTable tabId="{SHEETID[p["sheet"]]}" name="{escape(p["name"])}"/>' for p in PIVOTS if f not in p["ignore_slicers"])
            nitems = len(ITEMS[f]) + (1 if DF[f].isna().any() else 0)
            its = "".join(f'<i x="{j}" s="1"/>' for j in range(nitems))
            parts[f"xl/slicerCaches/slicerCache{i}.xml"] = (
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<slicerCacheDefinition xmlns="{NS_X14}" xmlns:mc="{NS_MC}" mc:Ignorable="x" '
                f'xmlns:x="{NS_MAIN}" name="{cname}" sourceName="{escape(f)}"><pivotTables>{pts}</pivotTables>'
                f'<data><tabular pivotCacheId="1"><items count="{nitems}">{its}</items></tabular></data></slicerCacheDefinition>').encode()
            ct_add.append(f'<Override PartName="/xl/slicerCaches/slicerCache{i}.xml" ContentType="application/vnd.ms-excel.slicerCache+xml"/>')
            rid = f"rId{next_wb_rid}"; next_wb_rid += 1
            wb_rel_add.append(f'<Relationship Id="{rid}" Type="http://schemas.microsoft.com/office/2007/relationships/slicerCache" Target="slicerCaches/slicerCache{i}.xml"/>')
            sc_refs.append(f'<x14:slicerCache r:id="{rid}"/>')
            defined += f'<definedName name="{cname}">#N/A</definedName>'
        wb_ext = f'<extLst><ext uri="{{BBE1A952-AA13-448e-AADC-164F8A28A991}}" xmlns:x14="{NS_X14}"><x14:slicerCaches>{"".join(sc_refs)}</x14:slicerCaches></ext></extLst>'
        host = "Dashboard" if A.dashboard else "Slicers"
        parts["xl/slicers/slicer1.xml"] = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<slicers xmlns="{NS_X14}" xmlns:mc="{NS_MC}" mc:Ignorable="x" xmlns:x="{NS_MAIN}">'
            + "".join(f'<slicer name="{escape(f)}" cache="Slicer_{re.sub(r"[^A-Za-z0-9_]", "_", f)}" caption="{escape(f)}" rowHeight="241300"/>' for f in SLICE) + "</slicers>").encode()
        ct_add.append('<Override PartName="/xl/slicers/slicer1.xml" ContentType="application/vnd.ms-excel.slicer+xml"/>')
        XDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"; AA = "http://schemas.openxmlformats.org/drawingml/2006/main"
        anchors = ""
        r0 = SL_R0 if A.dashboard else 2
        for i, f in enumerate(SLICE):
            c0 = (i * 6) if A.dashboard else (i * 3)
            anchors += (f'<xdr:twoCellAnchor editAs="oneCell"><xdr:from><xdr:col>{c0}</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>{r0}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from>'
                        f'<xdr:to><xdr:col>{c0 + (5 if A.dashboard else 2)}</xdr:col><xdr:colOff>{380000 if A.dashboard else 400000}</xdr:colOff><xdr:row>{r0 + (13 if A.dashboard else 13)}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:to>'
                        f'<mc:AlternateContent xmlns:mc="{NS_MC}"><mc:Choice xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" Requires="a14">'
                        f'<xdr:graphicFrame macro=""><xdr:nvGraphicFramePr><xdr:cNvPr id="{1000 + i}" name="{escape(f)}"/><xdr:cNvGraphicFramePr/></xdr:nvGraphicFramePr>'
                        f'<xdr:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></xdr:xfrm><a:graphic><a:graphicData uri="http://schemas.microsoft.com/office/drawing/2010/slicer">'
                        f'<sle:slicer xmlns:sle="http://schemas.microsoft.com/office/drawing/2010/slicer" name="{escape(f)}"/></a:graphicData></a:graphic></xdr:graphicFrame></mc:Choice>'
                        f'<mc:Fallback><xdr:sp macro="" textlink=""><xdr:nvSpPr><xdr:cNvPr id="0" name=""/><xdr:cNvSpPr><a:spLocks noTextEdit="1"/></xdr:cNvSpPr></xdr:nvSpPr>'
                        f'<xdr:spPr><a:xfrm><a:off x="{i * 2200000}" y="400000"/><a:ext cx="1828800" cy="2524125"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                        f'<a:solidFill><a:prstClr val="white"/></a:solidFill><a:ln w="1"><a:solidFill><a:prstClr val="green"/></a:solidFill></a:ln></xdr:spPr>'
                        f'<xdr:txBody><a:bodyPr vertOverflow="clip" horzOverflow="clip"/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1100"/>'
                        f'<a:t>This shape represents a slicer. Slicers are supported in Excel 2010 or later.</a:t></a:r></a:p></xdr:txBody></xdr:sp></mc:Fallback></mc:AlternateContent>'
                        f'<xdr:clientData/></xdr:twoCellAnchor>')
        sf = SHEETFILE[host]
        rp = os.path.dirname(sf) + "/_rels/" + os.path.basename(sf) + ".rels"
        existing_drawing = None
        if rp in parts:
            m = re.search(r'Type="[^"]*/drawing" Target="([^"]+)"', P(rp)) or re.search(r'Target="([^"]+)"[^>]*Type="[^"]*/drawing"', P(rp))
            if m:
                t = m.group(1)
                existing_drawing = t.lstrip("/") if t.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(sf), t)).replace("\\", "/")
        if existing_drawing:
            dx = P(existing_drawing)
            if "xmlns:a=" not in dx.split(">", 2)[1]:
                dx = dx.replace("<xdr:wsDr ", f'<xdr:wsDr xmlns:a="{AA}" ', 1)
            parts[existing_drawing] = dx.replace("</xdr:wsDr>", anchors + "</xdr:wsDr>").encode()
            (sl_rid,) = sheet_rels_add(host, [("http://schemas.microsoft.com/office/2007/relationships/slicer", "../slicers/slicer1.xml")])
            sx = P(sf)
        else:
            parts["xl/drawings/drawing_slicers.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<xdr:wsDr xmlns:xdr="{XDR}" xmlns:a="{AA}">{anchors}</xdr:wsDr>'.encode()
            ct_add.append('<Override PartName="/xl/drawings/drawing_slicers.xml" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>')
            dr_rid, sl_rid = sheet_rels_add(host, [(f"{REL}drawing", "../drawings/drawing_slicers.xml"),
                                                    ("http://schemas.microsoft.com/office/2007/relationships/slicer", "../slicers/slicer1.xml")])
            sx = P(sf)
            drawing_tag = f'<drawing r:id="{dr_rid}"/>'
            # drawing goes before tableParts/extLst; after pageMargins/pageSetup
            if "<tableParts" in sx:
                sx = sx.replace("<tableParts", drawing_tag + "<tableParts", 1)
            else:
                sx = sx.replace("</worksheet>", drawing_tag + "</worksheet>")
        wtag = re.search(r"<worksheet\b[^>]*>", sx).group(0)
        if "xmlns:r=" not in wtag:
            sx = sx.replace(wtag, wtag[:-1] + f' xmlns:r="{NS_R}">', 1)
        ext = (f'<extLst><ext uri="{{A8765BA9-456A-4dab-B4F3-ACF838C121DE}}" xmlns:x14="{NS_X14}">'
               f'<x14:slicerList><x14:slicer r:id="{sl_rid}"/></x14:slicerList></ext></extLst>')
        sx = sx.replace("</worksheet>", ext + "</worksheet>")
        parts[sf] = sx.encode()
        n_slicers = len(SLICE)

    # workbook.xml: definedNames, pivotCaches, extLst
    wbx = wbx.replace("<definedNames/>", "")
    if defined:
        if "<definedNames>" in wbx:
            wbx = wbx.replace("<definedNames>", "<definedNames>" + defined, 1)
        else:
            wbx = wbx.replace("</sheets>", "</sheets><definedNames>" + defined + "</definedNames>", 1)
    pc = f'<pivotCaches><pivotCache cacheId="1" r:id="{cache_rid}"/></pivotCaches>'
    m = re.search(r"<calcPr[^>]*/>", wbx)
    wbx = wbx[:m.end()] + pc + wbx[m.end():] if m else wbx.replace("</workbook>", pc + "</workbook>")
    if wb_ext:
        wbx = wbx.replace("</workbook>", wb_ext + "</workbook>")
    roottag = re.search(r"<workbook\b[^>]*>", wbx).group(0)
    if "xmlns:r=" not in roottag:
        wbx = wbx.replace(roottag, roottag[:-1] + f' xmlns:r="{NS_R}">', 1)

parts["xl/workbook.xml"] = wbx.encode()
parts["xl/_rels/workbook.xml.rels"] = wrels.replace("</Relationships>", "".join(wb_rel_add) + "</Relationships>").encode()
parts["[Content_Types].xml"] = ct.replace("</Types>", "".join(ct_add) + "</Types>").encode()

order = ["[Content_Types].xml", "_rels/.rels", "xl/workbook.xml", "xl/_rels/workbook.xml.rels"]
names = [n for n in order if n in parts] + [n for n in parts if n not in order]
tmp = out + ".tmp"
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zz:
    for n in names:
        zz.writestr(n, parts[n])
os.replace(tmp, out)
print(f"BUILT {os.path.relpath(out, root)} mode={MODE} dashboard={A.dashboard} pivots={n_pivots} slicers={n_slicers} "
      f"question_sheets={len(SPEC['questions'])} data_rows={len(DF):,}")
print("Next: run integrity_check.py on the file with --expect", os.path.relpath(exp_path, root))
