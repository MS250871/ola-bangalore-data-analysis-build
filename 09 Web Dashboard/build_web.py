"""Build the web dashboard (step 09) from the cleaned data. Writes aggregated JSON only (no row-level or customer data).
Usage:
  python build_web.py                         -> data/*.json, index.html, Ola_Rides_Analysis_Web_Dashboard_v1.html
  python build_web.py --expect OUT.json [--week L] [--vehicle V] [--area A] [--payment P]   -> expected {data-k: value} from pandas
Run from anywhere; paths are relative to the project root (the folder that contains PROJECT_RULES.md)."""
import os, sys, json, argparse, importlib.util
import numpy as np, pandas as pd
ap = argparse.ArgumentParser()
ap.add_argument("--expect"); ap.add_argument("--week"); ap.add_argument("--vehicle"); ap.add_argument("--area"); ap.add_argument("--payment")
A = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PREFIX = "Ola_Rides_Analysis"
spec = importlib.util.spec_from_file_location("helpers", os.path.join(ROOT, "07 Analysis", "helpers.py")); H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
df = pd.read_csv(os.path.join(ROOT, "05 Cleaning and Prep", "ola_final.csv"), low_memory=False)
df = H.add_helpers(df)
assert len(df) == 103024

STAT = ["Success", "Canceled by Customer", "Canceled by Driver", "Driver Not Found"]
CLS = ["c4", "c2", "c3", "c5"]
weeks = sorted(df.Week_Label.unique()); vehicles = sorted(df.Vehicle_Type.unique()); areas = sorted(df.Pickup_Location.unique())
real_pay = sorted(df.Payment_Method.dropna().unique()); payments = real_pay + ["Not completed (no payment)"]
dates = sorted(df.Date_Label.unique())
date_week = [weeks.index(df.loc[df.Date_Label == d, "Week_Label"].iloc[0]) for d in dates]
cust_reasons = sorted(df.loc[df.Booking_Status == "Canceled by Customer", "Cust_Reason"].unique())
drv_reasons = sorted(df.loc[df.Booking_Status == "Canceled by Driver", "Driver_Reason"].unique())
QS = [("Q1", "Headline KPIs", "q1", "KPI cards"), ("Q2", "Booking outcome mix", "q2", "horizontal bar + table"),
      ("Q3", "Daily bookings and success rate", "q3", "column bar + line"), ("Q4", "Hourly demand profile", "q4", "column bar"),
      ("Q5", "Success rate by hour of day", "q5", "line"), ("Q6", "Bookings and revenue by vehicle type", "q6", "horizontal bars + table"),
      ("Q7", "Cancellation and driver-not-found rates by vehicle type", "q7", "stacked bar + table"),
      ("Q8", "Pickup areas by bookings and failure rate", "q8", "horizontal bar + table"), ("Q9", "Customer cancellation reasons", "q9", "horizontal bar + table"),
      ("Q10", "Driver cancellation reasons", "q10", "horizontal bar + table"), ("Q11", "Quoted value lost to non-completed bookings, by status", "q11", "horizontal bar + table"),
      ("Q12", "Turnaround time and ratings by vehicle type", "q12", "table")]
meta = {"weeks": weeks, "vehicles": vehicles, "areas": areas, "payments": payments, "dates": dates, "date_week": date_week,
        "statuses": [{"label": s, "cls": c} for s, c in zip(STAT, CLS)], "cust_reasons": cust_reasons, "drv_reasons": drv_reasons,
        "questions": [{"id": a, "title": b, "section": c, "chart": d} for a, b, c, d in QS],
        "totals": {"bookings": int(len(df)), "completed": int(df.Is_Completed.sum()), "revenue": float(df.Revenue.sum()), "quoted_lost": float(df.Quoted_Lost.sum())}}

def build():
    d = df.copy()
    d["w"] = d.Week_Label.map(weeks.index); d["v"] = d.Vehicle_Type.map(vehicles.index); d["a"] = d.Pickup_Location.map(areas.index)
    d["p"] = d.Payment_Label.map(payments.index); d["s"] = d.Booking_Status.map(STAT.index)
    d["vt"] = d.V_TAT_Min.fillna(0) * 60; d["ct"] = d.C_TAT_Min.fillna(0) * 60
    d["dr"] = (d.Driver_Ratings.fillna(0) * 10).round(); d["cr"] = (d.Customer_Rating.fillna(0) * 10).round()
    g = d.groupby(["w", "v", "a", "p", "s"]).agg(b=("Bookings", "sum"), q=("Quoted_Lost", "sum"), c=("Is_Completed", "sum"), rev=("Revenue", "sum"),
                                                 vt=("vt", "sum"), ct=("ct", "sum"), dr=("dr", "sum"), cr=("cr", "sum")).reset_index()
    base = [[int(r.w), int(r.v), int(r.a), int(r.p), int(r.s), int(r.b), round(float(r.q), 2), int(r.c), round(float(r.rev), 2),
             round(float(r.vt), 3), round(float(r.ct), 3), int(r.dr), int(r.cr)] for r in g.itertuples()]
    di = d.Date_Label.map(dates.index)
    day = []
    for (v, a), x in d.groupby(["v", "a"]):
        b = np.bincount(di[x.index], minlength=len(dates)); c = np.bincount(di[x.index], weights=x.Is_Completed, minlength=len(dates))
        day.append([int(v), int(a), b.tolist(), [int(z) for z in c]])
    hour = []
    hi = d.Hour_Label.astype(int)
    for (w, v, a), x in d.groupby(["w", "v", "a"]):
        b = np.bincount(hi[x.index], minlength=24); c = np.bincount(hi[x.index], weights=x.Is_Completed, minlength=24)
        hour.append([int(w), int(v), int(a), b.tolist(), [int(z) for z in c]])
    reasons = []
    d["cri"] = d.Cust_Reason.map({n: i for i, n in enumerate(cust_reasons)}); d["dri"] = d.Driver_Reason.map({n: i for i, n in enumerate(drv_reasons)})
    for (w, v, a), x in d.groupby(["w", "v", "a"]):
        cc = np.bincount(x.cri.dropna().astype(int), minlength=len(cust_reasons)); dd = np.bincount(x.dri.dropna().astype(int), minlength=len(drv_reasons))
        reasons.append([int(w), int(v), int(a), cc.tolist(), dd.tolist()])
    return {"meta": meta, "base": {"cols": "w,v,a,p,status,bookings,quoted_lost,completed,revenue,vt_sec,ct_sec,drv_rating_x10,cust_rating_x10", "rows": base},
            "hour": {"rows": hour}, "day": {"rows": day}, "reasons": {"rows": reasons}}

def write_all():
    out = build(); os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    for k, v in out.items():
        json.dump(v, open(os.path.join(HERE, "data", k + ".json"), "w", encoding="utf-8"), separators=(",", ":"))
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(tpl.replace("__INLINE__", ""))
    inline = '<script type="application/json" id="inline-data">' + json.dumps(out, separators=(",", ":")).replace("</", "<\\/") + "</script>"
    fn = os.path.join(HERE, f"{PREFIX}_Web_Dashboard_v1.html")
    open(fn, "w", encoding="utf-8").write(tpl.replace("__INLINE__", inline))
    for f in sorted(os.listdir(os.path.join(HERE, "data"))): print("data/" + f, os.path.getsize(os.path.join(HERE, "data", f)), "bytes")
    print("index.html", os.path.getsize(os.path.join(HERE, "index.html")), "bytes"); print(os.path.basename(fn), os.path.getsize(fn), "bytes")

def expect():
    W = weeks.index(A.week) if A.week else -1; V = vehicles.index(A.vehicle) if A.vehicle else -1
    AR = areas.index(A.area) if A.area else -1; PM = A.payment
    def sub(w=0, v=0, a=0, p=0):
        x = df
        if w and A.week: x = x[x.Week_Label == A.week]
        if v and A.vehicle: x = x[x.Vehicle_Type == A.vehicle]
        if a and A.area: x = x[x.Pickup_Location == A.area]
        if p and PM: x = x[x.Payment_Label == PM]
        return x
    nn = lambda z: None if (z is None or (isinstance(z, float) and np.isnan(z))) else float(z)
    dv = lambda a, b: nn(a / b) if b > 0 else None
    E = {}
    x = sub(1, 1, 1); b, c, rev = len(x), int(x.Is_Completed.sum()), float(x.Revenue.sum())
    E.update({"q1.bookings": b, "q1.completed": c, "q1.success": dv(c, b), "q1.revenue": rev, "q1.avgfare": dv(rev, c)})
    if b:
        for s in STAT: E[f"q2.{s}.count"] = int((x.Booking_Status == s).sum()); E[f"q2.{s}.share"] = dv(int((x.Booking_Status == s).sum()), b)
    g = x.groupby("Date_Label").agg(b=("Bookings", "sum"), c=("Is_Completed", "sum"))
    for dte in dates:
        if A.week and weeks[date_week[dates.index(dte)]] != A.week: continue
        bb, cc = (int(g.loc[dte, "b"]), int(g.loc[dte, "c"])) if dte in g.index else (0, 0)
        E[f"q3.{dte}.bookings"] = bb; E[f"q3.{dte}.success"] = dv(cc, bb)
    hb = x.groupby("Hour_Label").agg(b=("Bookings", "sum"), c=("Is_Completed", "sum"))
    if b:
        for h in range(24):
            k = f"{h:02d}"; bb, cc = (int(hb.loc[k, "b"]), int(hb.loc[k, "c"])) if k in hb.index else (0, 0)
            E[f"q4.{k}.bookings"] = bb; E[f"q5.{k}.success"] = dv(cc, bb)
    y = sub(1, 0, 1, 1)
    for v in vehicles:
        z = y[y.Vehicle_Type == v]; E[f"q6.{v}.bookings"] = len(z); E[f"q6.{v}.revenue"] = float(z.Revenue.sum())
        E[f"q12.{v}.vtat"] = nn(z.V_TAT_Min.mean()); E[f"q12.{v}.ctat"] = nn(z.C_TAT_Min.mean())
        E[f"q12.{v}.drating"] = nn(z.Driver_Ratings.mean()); E[f"q12.{v}.crating"] = nn(z.Customer_Rating.mean())
    y = sub(1, 0, 1, 0)
    for v in vehicles:
        z = y[y.Vehicle_Type == v]; n = len(z)
        E[f"q7.{v}.custcancel"] = dv(int((z.Booking_Status == STAT[1]).sum()), n); E[f"q7.{v}.drvcancel"] = dv(int((z.Booking_Status == STAT[2]).sum()), n)
        E[f"q7.{v}.notfound"] = dv(int((z.Booking_Status == STAT[3]).sum()), n); E[f"q7.{v}.success"] = dv(int((z.Booking_Status == STAT[0]).sum()), n)
    y = sub(1, 1, 0, 0)
    for a_, z in y.groupby("Pickup_Location"):
        n = len(z); f_ = int((z.Is_Completed == 0).sum())
        E[f"q8.{a_}.bookings"] = n; E[f"q8.{a_}.failed"] = f_; E[f"q8.{a_}.failrate"] = dv(f_, n)
    cr = x[x.Booking_Status == STAT[1]].Cust_Reason.value_counts(); dr = x[x.Booking_Status == STAT[2]].Driver_Reason.value_counts()
    for n_ in cust_reasons: E[f"q9.{n_}.count"] = int(cr.get(n_, 0))
    for n_ in drv_reasons: E[f"q10.{n_}.count"] = int(dr.get(n_, 0))
    E["q9.total"] = int(cr.sum()); E["q10.total"] = int(dr.sum())
    ft = float(x.Quoted_Lost.sum())
    if ft:
        for s in STAT[1:]: E[f"q11.{s}.value"] = float(x.loc[x.Booking_Status == s, "Quoted_Lost"].sum())
        E["q11.total"] = ft
    if not b:
        for k in [k for k in E if k.startswith(("q4.", "q5."))]: E.pop(k)
    if not (x.Cust_Cancelled.sum() or True): pass
    flt = {}
    if A.week: flt["f_week"] = A.week
    if A.vehicle: flt["f_vehicle"] = A.vehicle
    if A.area: flt["f_area"] = A.area
    if A.payment: flt["f_payment"] = A.payment
    json.dump({"filters": flt, "values": E}, open(A.expect, "w", encoding="utf-8"), indent=0)
    print("WROTE", A.expect, len(E), "values", flt)

if A.expect: expect()
else: write_all()
