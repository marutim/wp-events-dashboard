#!/usr/bin/env python3
"""
merge_funnel_detail.py — fold a manual funnel-detail pull into dashboard_data.json.

The per-event funnel detail (and momentum) can't be fetched by the automated job;
they come from api/pull_funnel_detail.js run in a logged-in Central browser session.
This script takes that downloaded funnel_detail.json and updates the dashboard's
pipeline.records (+ testCount, detailAsOf). Momentum is left as-is unless the JSON
includes a "momentum" object.

Usage:
    python3 api/merge_funnel_detail.py funnel_detail.json
    # then:  python3 build_dashboard.py && cp events-dashboard.html index.html
    #        git add dashboard_data.json events-dashboard.html events-dashboard.artifact.html index.html
    #        git commit -m "Refresh funnel detail" && git push
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(HERE, "..", "dashboard_data.json")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 api/merge_funnel_detail.py funnel_detail.json"); sys.exit(1)
    src = sys.argv[1]
    if not os.path.exists(src):
        print("Not found:", src); sys.exit(1)
    payload = json.load(open(src))
    incoming = payload.get("records", [])
    if not incoming:
        print("No records in", src, "- aborting (nothing to merge)."); sys.exit(1)
    asof = payload.get("asOf")

    d = json.load(open(DASH))
    p = d.setdefault("pipeline", {})
    live = [r for r in incoming if not r.get("test")]
    tests = sum(1 for r in incoming if r.get("test"))
    p["records"] = live
    p["testCount"] = tests
    if asof:
        p["detailAsOf"] = asof
    if isinstance(payload.get("momentum"), dict) and payload["momentum"]:
        p["momentum"] = payload["momentum"]
    # keep the top-level dates block in sync so the footer is accurate
    d.setdefault("dates", {})["pipelineDetail"] = asof or d.get("dates", {}).get("pipelineDetail")

    json.dump(d, open(DASH, "w"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(f"Merged {len(live)} funnel records ({tests} test records excluded), detail as of {asof}.")
    print("  by stage:", dict(Counter(r.get("stage") for r in live)))
    print("Next: python3 build_dashboard.py && cp events-dashboard.html index.html, then commit + push.")

if __name__ == "__main__":
    main()
