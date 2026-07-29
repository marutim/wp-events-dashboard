# Events block for the Thursday Update / Comet + Orion Snap

Paste the block below into the agent's instructions (CoSnaps or equivalent). The data
source is public, so no credentials are needed. If the agent cannot fetch URLs, run
`python3 api/pull_events.py --block` locally instead and paste its output.

---

## AGENT INSTRUCTIONS: community events count

Produce the events block for this cycle's update using live data from WordCamp Central.

### Source
`https://central.wordcamp.org/wp-json/wp/v2/wordcamps?per_page=100&page=N`

Public and unauthenticated. Paginate from `page=1`, incrementing until a page returns
fewer than 100 records. There are roughly 1,480 records total (about 15 pages). This is
every official WordPress community event, not only WordCamps.

### Parsing rules
- The field `Start Date (YYYY-mm-dd)` is a **UNIX timestamp in seconds**, despite its name.
  Convert it as UTC. Do not read it as a date string.
- Skip records where that field is empty, missing, or `0`. About 7 records have no start date.
- Event title is at `title.rendered`.

### Counting basis (do not change this)
Count events by **event start date**. Do **not** filter on the `wcpt-closed` status.
Organizers close events out administratively one to three weeks after they happen, so a
status-based count under-reports. This is why earlier updates reported 41 / 47 / 59 on
Apr 28 / May 12 / Jun 9 when the true counts on those days were 46 / 53 / 63.

### Classify each event by title, lowercased, first match wins
1. contains `campus connect` → **Campus Connect**
2. contains `student club` → **Student Club**
3. contains `do_action` or `doaction` → **DoAction**
4. contains `wordcamp` → **WordCamp**
5. otherwise → **Other Event**

These match the tabs on WordCamp Central. Most events this year are not WordCamps, so
never report the WordCamp-only figure as the total.

### Compute
Let `today` be the publication date and `year` its year.
- **Past 2 weeks**: start date between `today - 13 days` and `today` inclusive.
- **Total so far this year**: start date in `year` and on or before `today`.
- **Scheduled for rest of year**: start date in `year` and after `today`.
- **Growth**: compare "total so far this year" to the same calendar point in `year - 1`.
- **Record chase**: full-year total for `year - 1`, and how many more events are needed to pass it.
- **By type**: counts per category for the year-to-date figure.

### Output format
```
WordPress Events and WordCamps during the past 2 weeks: {n}
Events and WordCamps scheduled for the rest of the year: {n}
Total Events and WordCamps hosted so far this year: {n}

That is {+X.X}% versus the same point in {year-1} ({n} events).
{n} more events beats the {year-1} full-year record of {n}. {n} are already scheduled.

By type so far this year: WordCamp {n} · Campus Connect {n} · Student Club {n} · Other Event {n}
```

### Caveats to respect
- Organizers reschedule events, so counts shift between pulls. Always state the date the
  figures were pulled.
- Report only the categories that have a non-zero count.
- If a pulled number moves backwards versus the previous update, that is usually a
  reschedule rather than an error. Say so rather than quietly correcting it.
