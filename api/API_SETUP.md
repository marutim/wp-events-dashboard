# Meetup API — one-command refresh

Goal: pull the whole WordPress Meetup Pro network (with group URLs) and rebuild the
tracker in one command, instead of the export-and-download dance.

## Security first
- Secrets go in `meetup_secrets.json` (this folder). It's **git-ignored** — never commit it, never paste its contents into chat.
- The script only ever **reads** that file locally. It never prints your token.

## 1. Get credentials (from the Meetup API Guide)
In the Pro admin sidebar there's an **API Guide** link. Open it and find the auth section. There are two common paths — pick whichever the Guide documents for you:

- **Simple — access token.** If the Guide (or the OAuth flow at <https://www.meetup.com/api/oauth/list/>) lets you generate an **access token**, that's the easiest. Copy it.
- **Advanced — JWT (server-to-server).** Create an OAuth client, generate a **signing key**, authorize it for an admin member. You'll get a client id, a signing key id, the authorized member id, and a private key file.

## 2. Fill in secrets
```
cp meetup_secrets.example.json meetup_secrets.json
```
Then edit `meetup_secrets.json`:
- Easiest: paste the token into `access_token`.
- JWT: leave `access_token` empty and fill the `jwt_*` fields (and `pip install pyjwt`).

Set `pro_network_urlname` (it's the slug in `meetup.com/pro/<slug>/` — almost certainly `wordpress`).

## 3. Test the connection (do this first)
```
python3 pull_meetup.py --raw
```
This authenticates and dumps the **first page of raw JSON**. If you see group data, auth works.
The raw output also shows the **real field names** — if they differ from what the script expects
(e.g. `memberships.count`, `link`, `pastEvents`), send me the raw output (it's not secret — it's
group-level data, no member PII) and I'll lock the query/mapping in one edit.

## 4. Full pull
```
python3 pull_meetup.py
```
Writes:
- `../meetup_groups.csv` — full export with a `url` column.
- `../data.js` — rebuilt with all groups **including URLs**; carries over the members/events
  aggregates from the previous data.js (those come from the members/events exports, not the
  groups query).

Reload the dashboard and the refresh is live.

## Notes
- This reads **your own network** for internal reporting — standard Pro-API use, not "building a competitor."
- The groups query gives group-level data only (no member emails/names), so nothing PII lands on disk beyond what's already public on each group page.
- For members/events 90-day aggregates, we can add separate queries later; v1 focuses on the group roster + URLs.
