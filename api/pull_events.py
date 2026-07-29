#!/usr/bin/env python3
"""
Community events pull for Year of the Meetup + the Thursday Update events block.

Source: https://central.wordcamp.org/wp-json/wp/v2/wordcamps  (PUBLIC, no auth)
So this runs anywhere, unlike pull_meetup.py which needs the Meetup JWT credentials.

Usage:
  python3 pull_events.py              # pull, append to ../history.json, print the TU block
  python3 pull_events.py --block      # just print the paste-ready TU block
  python3 pull_events.py --backfill   # add the three historical TU data points, then pull

COUNTING BASIS (important):
  We count by EVENT START DATE. The Thursday Update historically counted the
  "WordCamp Closed" status instead, which lags the actual event by 1-3 weeks because
  organizers close events out administratively after they happen. That is why the TU
  reported 41/47/59 on Apr 28 / May 12 / Jun 9 while the start-date basis was 46/53/63
  on those same days. Start date answers "did it happen", so we use it. The TU's
  originally published figures are preserved in history.json for provenance.
"""
import json, os, sys, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(HERE, "..", "history.json")
API = "https://central.wordcamp.org/wp-json/wp/v2/wordcamps"

# --asof YYYY-MM-DD reports as of a given date (use the update's publication date).
# Defaults to today.
TODAY = datetime.date.today()
for _i, _a in enumerate(sys.argv):
    if _a == "--asof" and _i + 1 < len(sys.argv):
        TODAY = datetime.date.fromisoformat(sys.argv[_i + 1])
    elif _a.startswith("--asof="):
        TODAY = datetime.date.fromisoformat(_a.split("=", 1)[1])
YEAR = TODAY.year

# WordCamp Central separates events into these tabs.
TYPES = ["WordCamp", "Campus Connect", "Student Club", "DoAction", "Other Event"]

def etype(title):
    s = (title or "").lower()
    if "campus connect" in s: return "Campus Connect"
    if "student club" in s: return "Student Club"
    if "do_action" in s or "doaction" in s: return "DoAction"
    if "wordcamp" in s: return "WordCamp"
    return "Other Event"

def fetch_all():
    rows, page = [], 1
    while True:
        url = "%s?per_page=100&page=%d" % (API, page)
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                batch = json.loads(r.read())
        except Exception as e:
            if page == 1: raise
            break
        if not isinstance(batch, list) or not batch: break
        rows += batch
        sys.stdout.write("\r  fetched %d events" % len(rows)); sys.stdout.flush()
        if len(batch) < 100: break
        page += 1
    print()
    return rows

def start_date(r):
    v = r.get("Start Date (YYYY-mm-dd)")
    if v in (None, "", 0, "0"): return None
    try: return datetime.datetime.utcfromtimestamp(int(v)).date()
    except Exception: return None

def analyse(rows):
    for r in rows:
        r["_d"] = start_date(r)
        r["_t"] = etype((r.get("title") or {}).get("rendered", ""))
    dated = [r for r in rows if r["_d"]]
    undated = len(rows) - len(dated)

    fortnight = TODAY - datetime.timedelta(days=13)
    ytd     = [r for r in dated if r["_d"].year == YEAR and r["_d"] <= TODAY]
    last14  = [r for r in dated if fortnight <= r["_d"] <= TODAY]
    rest    = [r for r in dated if r["_d"].year == YEAR and r["_d"] > TODAY]

    def by_type(subset):
        return {t: sum(1 for r in subset if r["_t"] == t) for t in TYPES if any(r["_t"] == t for r in subset)}

    prev = YEAR - 1
    prev_ytd = [r for r in dated if r["_d"].year == prev
                and (r["_d"].month, r["_d"].day) <= (TODAY.month, TODAY.day)]
    prev_full = [r for r in dated if r["_d"].year == prev]

    growth = None
    if prev_ytd:
        growth = round((len(ytd) - len(prev_ytd)) / len(prev_ytd) * 100, 1)

    return {
        "date": TODAY.isoformat(),
        "eventsLast14": len(last14),
        "eventsYTD": len(ytd),
        "eventsScheduledRest": len(rest),
        "eventsByTypeYTD": by_type(ytd),
        "eventsByTypeRest": by_type(rest),
        "eventsPrevYearYTD": len(prev_ytd),
        "eventsPrevYearFull": len(prev_full),
        "eventsGrowthPct": growth,
        "eventsProjected": len(ytd) + len(rest),
        "_undatedRecords": undated,
        "_basis": "event start date (not wcpt-closed status)",
    }

def tu_block(a):
    prev = YEAR - 1
    need = a["eventsPrevYearFull"] - a["eventsYTD"] + 1
    lines = []
    lines.append("WordPress Events and WordCamps during the past 2 weeks: %d" % a["eventsLast14"])
    lines.append("Events and WordCamps scheduled for the rest of the year: %d" % a["eventsScheduledRest"])
    lines.append("Total Events and WordCamps hosted so far this year: %d" % a["eventsYTD"])
    lines.append("")
    if a["eventsGrowthPct"] is not None:
        lines.append("That is %+.1f%% versus the same point in %d (%d events)."
                     % (a["eventsGrowthPct"], prev, a["eventsPrevYearYTD"]))
    if need > 0:
        lines.append("%d more events beats the %d full-year record of %d. %d are already scheduled."
                     % (need, prev, a["eventsPrevYearFull"], a["eventsScheduledRest"]))
    else:
        lines.append("This year has already passed the %d full-year record of %d."
                     % (prev, a["eventsPrevYearFull"]))
    lines.append("")
    lines.append("By type so far this year: " +
                 " · ".join("%s %d" % (k, v) for k, v in a["eventsByTypeYTD"].items()))
    return "\n".join(lines)

# Thursday Update figures as originally published, kept for provenance only.
# These used the lagging "WordCamp Closed" status, so they read lower than the
# start-date basis on the same day (shown as eventsYTD).
TU_BACKFILL = [
    {"date": "2026-04-28", "eventsLast14": 3, "eventsYTD_tuReported": 41, "eventsScheduledRest": 24, "eventsYTD": 46},
    {"date": "2026-05-12", "eventsLast14": 6, "eventsYTD_tuReported": 47, "eventsScheduledRest": 23, "eventsYTD": 53,
     "note": "TU also reported +56.67% vs same point 2025, and a 2025 full-year record of 103."},
    {"date": "2026-06-09", "eventsLast14": 4, "eventsYTD_tuReported": 59, "eventsScheduledRest": 22, "eventsYTD": 63},
]

def load_history():
    try: return json.load(open(HISTORY))
    except Exception: return []

def save_history(hist):
    hist.sort(key=lambda h: h["date"])
    json.dump(hist, open(HISTORY, "w"), indent=1)

def merge(hist, snap):
    """Merge into the row for that date so meetup + event metrics share one snapshot."""
    for h in hist:
        if h.get("date") == snap["date"]:
            h.update(snap); return hist
    hist.append(snap); return hist

def main():
    if "--backfill" in sys.argv:
        hist = load_history()
        for row in TU_BACKFILL:
            row = dict(row); row["_source"] = "Thursday Update archive (backfilled)"
            hist = merge(hist, row)
        save_history(hist)
        print("backfilled %d Thursday Update data points" % len(TU_BACKFILL))

    print("Pulling community events from WordCamp Central (public API)...")
    rows = fetch_all()
    a = analyse(rows)

    print("\n%d events YTD · %d in the last 2 weeks · %d scheduled for the rest of %d"
          % (a["eventsYTD"], a["eventsLast14"], a["eventsScheduledRest"], YEAR))
    print("by type YTD:", a["eventsByTypeYTD"])
    if a["_undatedRecords"]:
        print("note: %d records have no start date and are excluded" % a["_undatedRecords"])

    if "--block" not in sys.argv:
        hist = merge(load_history(), a)
        save_history(hist)
        print("history: %d snapshots" % len(hist))

    print("\n" + "=" * 62)
    print("PASTE-READY THURSDAY UPDATE BLOCK")
    print("=" * 62)
    print(tu_block(a))
    print("=" * 62)

if __name__ == "__main__":
    main()
