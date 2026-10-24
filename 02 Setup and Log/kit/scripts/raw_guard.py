"""Prove Raw Data was not modified: compare every file's SHA-256 with the values recorded at setup.

Usage: python raw_guard.py            (check, exit code 1 if anything changed)
       python raw_guard.py --record   (record hashes; setup does this once, and when the user adds a new raw file)"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dakit import find_root, load_cfg, save_cfg, sha256, raw_files, today

ap = argparse.ArgumentParser()
ap.add_argument("--record", action="store_true")
ap.add_argument("--root")
A = ap.parse_args()
root = find_root(A.root)
cfg = load_cfg(root)
rec = cfg.setdefault("raw_hashes", {})
now = {os.path.relpath(p, root).replace("\\", "/"): sha256(p) for p in raw_files(root)}
if A.record:
    for k, v in now.items():
        if k in rec and rec[k]["sha256"] != v:
            sys.exit(f"ERROR: {k} already recorded with a different hash. Raw files must not change; ask the user.")
        rec.setdefault(k, {"sha256": v, "bytes": os.path.getsize(os.path.join(root, k)), "recorded": today()})
    save_cfg(root, cfg)
    for k, v in rec.items():
        print(f"RECORDED {k} {v['bytes']} bytes sha256={v['sha256']}")
    sys.exit(0)
bad = 0
for k, v in rec.items():
    if k not in now:
        print(f"MISSING  {k}"); bad += 1
    elif now[k] != v["sha256"]:
        print(f"CHANGED  {k}"); bad += 1
    else:
        print(f"OK       {k}")
for k in now:
    if k not in rec:
        print(f"NEW      {k} (not recorded yet: run with --record after the user confirms it is a source file)")
print("RAW DATA UNCHANGED" if not bad else "RAW DATA CHANGED: stop and tell the user")
sys.exit(1 if bad else 0)
