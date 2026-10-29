# Activity Pulse (DASH-247)

Answers a customer's question "is this normal for us?". For one account it compares the last complete week of
activity (calls, leads, appointments) with that account's usual week and shows which locations are unusually quiet.

- **Backend:** Django 5.2, Django REST framework, SQLite. Read-only JSON API with Swagger UI.
- **Frontend:** React 19, TypeScript, Vite, plain CSS. No UI or chart libraries.
- **Data:** `seed.sql` (20 accounts, 69 locations, 12,626 events, 2026-02-01 to 2026-07-27).

`PLAN.md` is the original plan, kept unchanged as a record. This README describes what is built; see
[Differences from PLAN.md](#differences-from-planmd).

## Run it

Requirements: Python 3.12 (tested; Django 5.2 supports 3.10+), Node 22.12+ (tested on 24) and npm.

```bash
# Backend (terminal 1), from the repository root
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd backend
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py import_seed        # "Imported 20 accounts, 69 locations, 12626 events."
../.venv/bin/python manage.py runserver          # http://127.0.0.1:8000

# Frontend (terminal 2), from the repository root
cd frontend
npm ci
npm run dev                                      # http://localhost:5173
```

Pages worth opening (append to the URL):

| Page | Shows |
|---|---|
| `/?account=12` | The default week: one location (Site C) below usual |
| `/?account=6&as_of=2026-06-08` | The Metro Collision burst week ([see below](#the-metro-collision-spike)) |
| `/?account=6&as_of=2026-02-16` | Every location has too little history |
| `/?account=20` | An account with no events |

API explorer: <http://127.0.0.1:8000/api/docs/> (Swagger UI; assets load from a CDN, so it needs internet). The raw
schema is at `/api/schema/`.

- `import_seed` refuses to run on a database that already has data; `--replace` reloads. It runs in one transaction,
  keeps every id and row, and rolls back if any count differs from the source.
- Vite proxies `/api` to `127.0.0.1:8000` (`frontend/vite.config.ts`), so there is no CORS setup. `npm run build`
  writes static files to `frontend/dist`; Django does not serve them and there is no deployment configuration.
- Settings are development-only: fixed `SECRET_KEY`, `DEBUG = True`, no authentication.

## Tests and checks

```bash
cd backend
../.venv/bin/python manage.py test
../.venv/bin/python manage.py spectacular --validate --fail-on-warn --file /tmp/schema.yml

cd ../frontend
npm run typecheck && npm test && npm run build
```

Backend tests cover the weekly rules (DST, Phoenix and UTC accounts, UTC-versus-local weeks, zero weeks, short
histories), the import, the API contract and a back-test on the real seed. Frontend tests cover URL state, week
navigation, popovers, expandable rows and the loading, error and empty states.

## Architecture

```text
backend/activity/models.py       Account, Location, ActivityEvent (constraints, one index)
backend/activity/services.py     the metric: weeks, baseline, status. No request/response code
backend/activity/serializers.py, views.py   API contract and OpenAPI annotations
backend/activity/management/commands/import_seed.py
frontend/src/                    App (state, URL, fetching) and the components, plus small helpers
ai-log/                          decisions and full AI session exports
```

`Location` is normalized out of the seed's `location` string: it is the unit the feature reports on, and names like
`Site A` are only unique within an account. `event_type` and `outcome` stay as text with `TextChoices` and database
check constraints. There is one index, `(location, occurred_at)`. Duplicate-looking events are kept, so they have no
unique constraint.

## API

Read-only (`GET`, `HEAD`, `OPTIONS`), no authentication.

| Endpoint | Returns |
|---|---|
| `GET /api/accounts/` | `[{id, name, timezone}]`, sorted by name |
| `GET /api/accounts/{id}/activity/?as_of=YYYY-MM-DD` | The weekly comparison. `as_of` is optional |

`as_of` defaults to the latest event date. The judged week is the complete week before the week containing `as_of`.
Errors: `400 {"as_of": ["…"]}` for a malformed or blank date, one outside 2000-01-01..2100-12-31, or one later than
`latest_event_date` (beyond the data, empty weeks would read as a real drop); `404 {"detail": "Account not found."}`.

```json
{
  "account": {"id": 12, "name": "Redline Tire & Service", "timezone": "America/Los_Angeles"},
  "as_of": "2026-07-27",
  "latest_event_date": "2026-07-27",
  "week": {"start": "2026-07-20", "end": "2026-07-26"},
  "headline": {"this_week": 54, "usual": 56.0, "delta_pct": -3.6},
  "locations": [
    {
      "id": 48, "name": "Site C", "this_week": 2, "usual": 8.5, "delta_pct": -76.5, "status": "below",
      "calls": 1, "leads": 1, "appointments": 0,
      "history": [{"week_start": "2026-05-25", "count": 10}, {"week_start": "2026-06-01", "count": 12}, "…"]
    }
  ]
}
```

- `headline` is numbers only, with no status for the account as a whole.
- `usual` and `delta_pct` are `null` without enough history (`delta_pct` also when `usual` is 0), never a division error.
- `status` is `below`, `above`, `normal` or `not_enough_data`. Locations are sorted below-usual first (largest
  shortfall first), then by name.
- `history` holds the exact weekly counts `usual` is the median of, oldest first; the median is computed from this list.

## How the weekly comparison works

All rules are in [`backend/activity/services.py`](backend/activity/services.py).

1. **Weeks** run Monday to Sunday in the account's own timezone. UTC timestamps become local dates, and weeks are
   calendar dates rather than 168-hour blocks, so DST is safe. The judged week is the last complete week before the
   week containing `as_of`; a partial week is never judged or used in a baseline.
2. **Counted value:** all events (calls + leads + appointments) per location per week.
3. **Usual week:** the median of up to the 8 weeks before the judged week. A location's history starts the week after
   its first event, and empty weeks after that count as 0. Fewer than 4 history weeks gives `not_enough_data`. A usual
   of 0 with enough history is valid: 0 events is `normal`, any event is `above`.
4. **Status** (locations only): `below` if P(X ≤ count) < 0.025 under a Poisson distribution with mean `usual`, `above`
   if P(X ≥ count) < 0.025, otherwise `normal`. That is, a count this low (or high) would happen less than 2.5% of the
   time in a normal week. It points at where to look; it is not a diagnosis.
5. **Account headline:** this week against the median of the account's own weekly totals, plus the percentage change,
   with no status: the same test over-flags account totals because a customer's locations move together (weekly
   variance up to 2.3 times the mean).

`WINDOW_WEEKS = 8`, `MIN_HISTORY_WEEKS = 4` and `TAIL_PROBABILITY = 0.025` are constants at the top of the file.
`below` fires when the count is at most:

| usual | 3.5 | 4.5 | 5.5 | 6.5 | 8 | 10 | 15 | 30 |
|---|---|---|---|---|---|---|---|---|
| flag if ≤ | none | 0 | 0 | 1 | 2 | 3 | 7 | 19 |

**Why a Poisson tail test.** Weekly counts per location are small (about 4 to 10) with variance close to the mean, the
Poisson signature. A back-test over the 17 judged weeks from 2026-03-30 to 2026-07-20 (1,173 location-weeks) counted
the flags each rule raised:

| Rule | Flags observed | Per week |
|---|---|---|
| Poisson tail, 0.025 (used) | 22 (1.9%) | 1.3 (max 3) |
| count ≤ 50% of usual (usual ≥ 3) | 126 (10.7%) | 7.4 |
| count ≤ 60% of usual (usual ≥ 5) | 160 (13.6%) | 9.4 |

At the default `as_of` the used rule gives 1 below, 1 above and 67 normal locations. There is no ground truth, so these
are flags the rule raised, not confirmed problems, false positives or misses.

**Why the median of 8 weeks.** The median keeps one extreme week from becoming "normal" (a mean would have flagged most
Metro Collision locations as below usual for weeks, see below). Eight weeks is about two months: long enough to absorb a
few odd weeks, short enough to follow a location that really changed, and the median stays steady while fewer than 4
of the 8 are inflated. A minimum of 4 weeks keeps a median from being mostly noise. Both numbers are judgment calls;
there is no labelled data to tune them against.

## The Metro Collision spike

On Wednesday 2026-06-03, Metro Collision Centers (account 6) recorded 805 events in one day, against a median day
of 10 (95th percentile 22, maximum 28). The week of June 1 shows 881 events against a usual 66 (+1,234.8%) with all 15
locations "above usual". The original events were inspected and never modified.

**Evidence**

- One local day, spread across the business day and all 15 locations (42 to 69 each).
- Ordinary traffic at about 80 times the volume: 60% calls, 26% leads, 14% appointments (rest of the account: 61%, 23%,
  16%), with the same call outcomes and durations. Tests could not tell the mix from the rest of the account (χ² 3.7 for
  event types on 2 degrees of freedom, 1.0 for call outcomes, 16.3 for locations on 14).
- Not a replay: 798 of 805 timestamps are distinct and row ids are interleaved with other accounts' events in time
  order. Nothing similar exists elsewhere: no other account has a day above 28 events and no other location-week is
  more than 3 times its median.
- **Unknown:** the cause. A real campaign, bot traffic, a test fixture or a feed problem look alike, because the data
  has no source field.

**Decision: keep the events and document the limitation.** Nothing proves they are invalid, and removing them needs a
threshold rule with its own product questions. Simulating their exclusion on a copy of the database (dropping the day,
or capping it to a normal day):

- The 15 "above usual" flags for that week disappear (14 in the capped run, where the 12 kept events leave one location
  above). No "below usual" flag changes and no other account is affected.
- Later weeks barely move: the account's usual stays between 66 and 73.5 in every scenario. Deleting the day even
  distorts later baselines, since it makes that week unusually low.
- **The median protects later comparisons.** Over the seven complete weeks after the spike, a mean baseline would flag 56
  of 105 Metro Collision location-weeks as below usual (account usual about 170 instead of 66 to 73). The median flags 1.

The dashboard shows the exact percentage, and the expandable weekly history on each location gives the context. A
sustained campaign covering 4 or more of the 8 weeks would move the median.

## Frontend

- **URL state:** `?account=6&as_of=2026-07-27` via `history.replaceState`; invalid values fall back to defaults.
- **Week navigation** (previous, next, Latest) sends `as_of` (the Monday after the shown week), never passes
  `latest_event_date`, and disables Previous on an empty week because nothing older exists.
- **Popovers** (ⓘ) explain the usual week, the change and the statuses. They open on click, tap, Enter or Space, close
  on Escape, outside click or lost focus, and are a bottom sheet on phones.
- **Expandable rows** show this week by event type and the weekly counts behind the usual week, with the median.
- **Single-location accounts** also show the location table: the headline has no status, so the location row is the
  only place a drop can be flagged.
- Loading, error (with retry), empty-account and not-enough-history states. Light and dark themes follow the OS.

## Assumptions and limitations

- "Normal" is a location's own recent history, not an industry benchmark. "Now" is `as_of` (default: the latest event),
  not the wall clock, because the data ends on 2026-07-27. `latest_event_date` is the UTC date of the newest event in
  the whole database and the newest allowed `as_of`.
- There is no login: the page has an account picker and the API has no authentication.
- **Statistics:** Poisson assumes independent events, a steady weekly rate and variance near the mean. Bursts and
  campaigns break independence (the median limits the damage). Trends and seasonality are not modelled.
- **Silent locations:** one silent for most of the 8 weeks gets a usual of 0 and is never flagged. Event data cannot tell
  a closed location from a broken one. Locations with a usual under about 3.7 cannot be flagged at all.
- **Flag volume:** the back-test observed about 1.3 flags per Monday across 69 locations. Without ground truth, how many
  are real problems is unknown.
- **Unused fields:** `outcome` and `duration_seconds` are stored and validated but not used by the metric or returned.
- **Not production-ready:** development settings, no authentication, no deployment setup, SQLite only. Tested in Chrome
  only, and not with a screen reader. Out of scope per the ticket: alerting, ML and forecasting.

## Where would an LLM fit?

- **Not in deciding what is normal.** That must be deterministic, auditable and testable. Counts are tiny, so a statistical
  rule works with no cost, latency or run-to-run drift, and it can be back-tested, which is how it was chosen and checked.
- **A plausible addition, not built: a plain-language summary** of an already-computed result ("3 locations are below
  usual; Site C had 2 events against a usual 8 to 9"). The model would see only the computed numbers, a check would
  confirm every number in its text appears in the input, and a fixed template would be the fallback. Risks: invented
  figures, customer data sent to a third party, cost, latency, non-determinism. It adds no correctness, so it is out of
  scope.
- **Rejected: explaining why** a location is low. The data has no cause signals, so a model could only guess.

## Differences from PLAN.md

Later decisions that supersede the plan (each is in `ai-log/DECISIONS.md`):

| PLAN.md | Implemented | Why |
|---|---|---|
| Account headline has a status | Numbers only | The Poisson test over-flagged account totals |
| Single-location accounts show the headline only | They also show the location table (confirmed) | Nothing else would flag a single location's drop |
| Any valid `as_of`; date input | Dates after the latest event are rejected (400); week navigation | Empty weeks beyond the data read as a real drop; complete weeks make choosing a day meaningless |
| Response without extras | Adds `latest_event_date`, per-location `history`, Swagger UI and OpenAPI schema | Bound navigation; explain `usual` |
| Null outcome reported as `unknown`; usual 0 shown as "No recent activity" | Outcomes not exposed; a usual of 0 shows `0` with change `—` | Outcomes do not feed the metric |
| "About 800 extra connected calls" on June 3 | 805 mixed events (calls, leads, appointments) | Corrected by the spike investigation |

## AI-assisted development log

`ai-log/DECISIONS.md` lists every decision, correction and rejection by the user, linked to the session where it
happened; `ai-log/sessions/` holds the full exported conversations; `CLAUDE.md` holds the working rules given to the
agent. An AI coding agent built, tested and reviewed this code under that supervision.
