# Activity Pulse (DASH-247)

Answers a customer's question "is this normal for us?" at a glance. For one account it shows how the last
complete week of activity (calls, leads and appointments) compares with that account's usual week, and which
locations are unusually quiet.

- **Backend:** Django 5.2 + Django REST framework, SQLite, read-only JSON API with Swagger UI.
- **Frontend:** React 19 + TypeScript + Vite, plain CSS, no UI or chart libraries.
- **Data:** `seed.sql` (20 accounts, 69 locations, 12,626 events, 2026-02-01 to 2026-07-27).

`PLAN.md` is the original plan and is kept unchanged as a record. Where the implementation differs from it,
see [Differences from PLAN.md](#differences-from-planmd). This README describes what is built.

## Run it

Requirements: Python 3.12 (tested; Django 5.2 supports 3.10+), Node 22.12+ (tested on 24) and npm.

```bash
# 1. Backend (terminal 1), from the repository root
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd backend
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py import_seed        # "Imported 20 accounts, 69 locations, 12626 events."
../.venv/bin/python manage.py runserver          # http://127.0.0.1:8000

# 2. Frontend (terminal 2), from the repository root
cd frontend
npm ci
npm run dev                                      # http://localhost:5173
```

Open <http://localhost:5173>. Good pages to start with (append to the URL):

| Page | What it shows |
|---|---|
| `/?account=12` | The default week: one location (Site C) below usual |
| `/?account=6&as_of=2026-06-08` | The Metro Collision burst week (see [the spike](#the-metro-collision-spike)) |
| `/?account=6&as_of=2026-04-20` | Two locations below usual |
| `/?account=6&as_of=2026-02-16` | Every location has too little history |
| `/?account=20` | An account with no events |

API explorer: <http://127.0.0.1:8000/api/docs/> (Swagger UI; its assets load from a CDN, so it needs internet).
The raw schema is at `/api/schema/`.

Notes:
- `import_seed` refuses to run on a database that already has data. Use `import_seed --replace` to reload; it
  runs in one transaction, preserves every id and row, and rolls back if any count differs from the source.
- The Vite dev server proxies `/api` to `127.0.0.1:8000` (`frontend/vite.config.ts`), so there is no CORS setup.
  `npm run build` produces static files in `frontend/dist`; Django does not serve them, and there is no
  deployment configuration. `npm run preview` serves the build on port 4173 with the same proxy.
- Settings are development-only: a fixed `SECRET_KEY`, `DEBUG = True`, no authentication.

## Tests and checks

```bash
cd backend
../.venv/bin/python manage.py test                                           # 134 tests
../.venv/bin/python manage.py spectacular --validate --fail-on-warn --file /tmp/schema.yml

cd ../frontend
npm run typecheck && npm test && npm run build                               # 80 tests
```

The backend tests cover the weekly rules (DST weeks, Phoenix and UTC accounts, events whose week differs between UTC
and local time, zero weeks, short histories, the burst not hiding an outage), the import (ids, duplicates,
`--replace` guard, rollback), the API contract and a back-test against the real seed. The frontend tests cover
URL state, week navigation, popovers, expandable rows and the loading, error and empty states.

## Architecture

```text
seed.sql ──import_seed──▶ SQLite ──ORM──▶ activity/services.py ──▶ DRF views ──▶ /api/… ──▶ React page
 schema.sql              (3 tables)       weekly rules, no HTTP     serializers   (Vite proxy)
```

```text
backend/config/              settings, URLs
backend/activity/models.py   Account, Location, ActivityEvent (constraints, one index)
backend/activity/services.py the metric: weeks, baseline, status. No Django request/response code
backend/activity/serializers.py, views.py     the API contract and OpenAPI annotations
backend/activity/management/commands/import_seed.py
backend/activity/tests/      backend tests
frontend/src/                App (state, URL, fetching), WeekNav, HeadlinePanel, LocationTable,
                             LocationDetail, InfoPopover, EmptyState, weeks/format/urlState helpers
ai-log/                      decisions and full AI session exports (see the end of this file)
```

**Data model.** `Location` is normalized out of the seed's `location` string because it is the unit the feature
reports on and names are only unique within an account (`Site A` exists in many accounts). `event_type` and
`outcome` stay as text with `TextChoices` and database check constraints (an outcome must be valid for its event
type; a duration only for calls). There is one index, `(location, occurred_at)`. Duplicate-looking events are kept,
so there is no unique constraint on them.

## API

Read-only: `GET`, `HEAD` and `OPTIONS` only, no authentication.

| Endpoint | Returns |
|---|---|
| `GET /api/accounts/` | `[{id, name, timezone}]`, sorted by name |
| `GET /api/accounts/{id}/activity/?as_of=YYYY-MM-DD` | The weekly comparison below. `as_of` is optional |

`as_of` defaults to the date of the latest event. The judged week is the complete week before the week containing
`as_of`, so any date in the following week selects the same week. Errors:

| Status | When | Body |
|---|---|---|
| 400 | `as_of` is malformed, blank, outside 2000-01-01..2100-12-31, or later than `latest_event_date` | `{"as_of": ["…"]}` |
| 404 | Unknown account | `{"detail": "Account not found."}` |

Later dates are rejected on purpose: beyond the newest data the empty weeks would read as a real drop in activity.

Example (`/api/accounts/12/activity/`, locations and history shortened):

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

- `headline` is numbers only: no status for the account as a whole (see below).
- `usual` and `delta_pct` are `null` without enough history (and `delta_pct` when `usual` is 0), never a division error.
- `status` is `below`, `above`, `normal` or `not_enough_data`. Locations are sorted below-usual first, largest
  shortfall first, then by name.
- `history` lists the exact weekly counts `usual` is the median of, oldest first. Each location's median is computed
  from this list, so the explanation and the number cannot disagree.
- `calls`, `leads` and `appointments` are this week's counts by event type.
- Numbers are rounded to one decimal. The Swagger UI documents every field.

## How the weekly comparison works

All rules live in [`backend/activity/services.py`](backend/activity/services.py) and are independent of the API layer.

1. **Weeks** run Monday to Sunday in the account's own IANA timezone (UTC timestamps become local dates first).
   Weeks are calendar dates, not 168-hour blocks, so DST changes are safe. For 8 events in the seed the local week
   differs from the UTC week.
2. **Judged week:** the last complete week before the week containing `as_of`. A partial week is never judged or
   used in a baseline.
3. **Counted value:** all events (calls + leads + appointments) per location per week.
4. **Usual week:** the median of up to the 8 weeks before the judged week. A location's history starts the week after
   its first event (that week may be partial), and empty weeks after that count as 0. Fewer than 4 history weeks gives
   `not_enough_data`. A usual week of 0 with enough history is valid: 0 events is `normal`, any event is `above`.
5. **Status** (locations only). With `usual` as the expected count, a Poisson tail test decides: `below` if
   P(X ≤ count) < 0.025, `above` if P(X ≥ count) < 0.025, otherwise `normal`. In words: the count would be this low
   (or high) less than 2.5% of the time in a normal week. It is an indication of where to look, not a diagnosis.
6. **Account headline:** this week against the median of the account's own weekly totals, with the percentage
   change. It has no status. The same rule over-flags account totals, because locations of one account move together
   (their weekly variance is up to 2.3 times the mean), so showing the numbers is the honest choice.

`WINDOW_WEEKS = 8`, `MIN_HISTORY_WEEKS = 4` and `TAIL_PROBABILITY = 0.025` are constants at the top of the file.

Resulting thresholds (`below` when the count is at most):

| usual | 3.5 | 4.5 | 5.5 | 6.5 | 8 | 10 | 15 | 30 |
|---|---|---|---|---|---|---|---|---|
| flag if ≤ | none | 0 | 0 | 1 | 2 | 3 | 7 | 19 |

A location with a usual week below about 3.7 can never be flagged: one quiet week is not strong evidence at that
volume.

### Why a Poisson tail test

Weekly counts per location are small (about 4 to 10) and their variance is roughly equal to their mean, which is the
Poisson signature. A back-test over the 17 judged weeks from 2026-03-30 to 2026-07-20 (69 locations, 1,173
location-weeks) compared rules:

| Rule | Flags | Per week |
|---|---|---|
| Poisson tail, 0.025 (used) | 22 (1.9%) | 1.3 (max 3) |
| count ≤ 50% of usual (usual ≥ 3) | 126 (10.7%) | 7.4 |
| count ≤ 60% of usual (usual ≥ 5) | 160 (13.6%) | 9.4 |

Simple percentage rules would hand a customer a long, mostly noise list every Monday. With the Poisson rule the
default week gives 1 below, 1 above and 67 normal locations. There is no ground truth, so a flag is not
claimed to be a real problem; expect roughly one flag per Monday across all 69 locations.

### Why the median of 8 weeks

- **Median, not mean:** one extreme week must not become "normal". See the Metro Collision spike below, where a
  mean would have flagged most locations as below usual for the next seven weeks.
- **8 weeks:** about two months. That is long enough to absorb a few odd weeks (holiday, outage, campaign) and
  short enough to follow a location that has genuinely changed. The median stays honest as long as fewer than 4 of
  the 8 weeks are inflated.
- **At least 4 weeks:** with fewer, a median is mostly noise, so the location is marked "Not enough history" instead
  of guessing.

Both numbers are judgment calls: there is no labelled data to tune them against. They are named constants.

## The Metro Collision spike

On Wednesday 2026-06-03, Metro Collision Centers (account 6) recorded 805 events in one day. A normal day for that
account has a median of 10 (95th percentile 22, maximum 28). The week of June 1 shows 881 events against a usual
66 (+1,234.8%) and all 15 locations "above usual". I inspected the original data before deciding anything; the
events were not modified.

**Evidence**
- All 805 events fall on one local day, spread across the whole business day, in all 15 locations (42 to 69 each).
- They look like ordinary traffic at about 80 times the volume: 60% calls, 26% leads and 14% appointments (rest of the
  account: 61%, 23% and 16%); the same call outcomes and durations. Statistical tests could not tell the mix from the
  rest of the account (χ² 3.7 for event types on 2 degrees of freedom, 1.0 for call outcomes, 16.3 for locations on 14).
- They are not a replay or a duplicate dump: 798 of the 805 timestamps are distinct and the row ids are interleaved
  with other accounts' events in time order.
- Nothing like it exists elsewhere: no other account has a day above 28 events, and no other location-week is more
  than 3 times that location's median.

**What we do not know:** the cause. A real campaign, bot traffic, a test fixture or a data feed problem all look
alike here, because the data has no source or campaign field.

**Decision: keep the events and document the limitation.** Nothing proves they are invalid, and removing them would
need a threshold rule with its own product questions. I simulated excluding them on a copy of the database (never on
the real data), by dropping the day and by capping it to a normal day:
- The 15 "above usual" flags for that week disappear (14 in the capped run, where the 12 events kept happen to leave
  one location above). No "below usual" flag changes in any scenario, and no other account is affected.
- Later weeks barely move: the account's usual week stays between 66 and 73.5 in every scenario. Dropping the whole day
  even distorts later baselines (it makes that week unusually low), which is a reason not to clean data by deleting.
- The median is what protects later comparisons. Over the seven complete weeks after the spike, a mean baseline would
  flag 56 of 105 Metro Collision location-weeks as below usual, and the account's usual week would be about 170
  instead of 66 to 73. The median flags 1.

**Limits:** a sustained campaign covering 4 or more of the 8 weeks would move the median, and the dashboard still
shows the large percentage (+1,234.8%) as computed. The week itself is accurate: it was a very busy week.

## Frontend

- One page: account picker, week navigator (previous, next, Latest), the account's numbers, and a location table.
- **URL state:** `?account=6&as_of=2026-07-27`, written with `history.replaceState`. Invalid values fall back to
  defaults. Week navigation sends `as_of` to the API (the Monday after the shown week) and never goes past
  `latest_event_date`. Previous is disabled on an empty week, because nothing older exists.
- **Popovers** (ⓘ) explain the usual week, the change and the statuses. They open on click, tap, Enter or Space, close
  on Escape, outside click or when focus leaves, and are a bottom sheet on phones.
- **Expandable rows** show this week by event type and the weekly counts behind the usual week, with the median.
- States: loading, errors with a retry, an account without events, and locations without enough history. An
  out-of-range `as_of` from a bookmark shows a plain-language message with a "Show latest week" button.
- Timezones are shown as friendly names ("Pacific Time"). Light and dark themes follow the operating system.

## Assumptions

- "Normal" means a location's own recent history, not an industry benchmark.
- The page has no login in this exercise, so it has an account picker and the API has no authentication.
- "Now" is the `as_of` parameter (default: the latest event), not the wall clock, because the data ends on 2026-07-27.
- `latest_event_date` is the UTC date of the newest event in the whole database. It is also the newest allowed `as_of`.
- Only below-usual is highlighted; above-usual is shown for context.
- A location appears once it has an event; a location with no events at all does not exist in the data.

## Limitations and risks

- **Statistics:** the Poisson rule assumes independent events, a roughly steady weekly rate and variance near the
  mean. Bursts and campaigns break independence (the median limits the damage). Trends and seasonality are not
  modelled; a growing or shrinking location is compared with its own recent past.
- **Silent locations:** a location silent for most of the 8 weeks gets a usual week of 0 and is never flagged.
  Event data cannot tell a closed location from a broken one.
- **Low volume:** locations with a usual week under about 3.7 cannot be flagged.
- **Noise:** about 1.3 flags per Monday across the 69 seed locations is expected even when nothing is wrong.
- **Unused fields:** `outcome` and `duration_seconds` are stored and validated but not used by the metric or returned
  by the API, which reports counts by event type only. Nulls (3% of outcomes) are kept as null.
- **Large percentages:** very large changes (like +1,234.8%) are shown as computed, with no softer wording.
- **Not production-ready:** development settings, no authentication, no deployment setup, SQLite only. Swagger UI
  needs internet access. Tested in Chrome only (not Firefox or Safari), and not with a screen reader.
- **Out of scope** per the ticket: alerting and notifications, ML and forecasting.

## Where would an LLM fit?

- **Not in deciding what is normal.** That has to be deterministic, auditable and testable. Counts are tiny, so a
  statistical rule does the job with no cost, latency or run-to-run drift, and it can be back-tested, which is how
  the rule was chosen and checked.
- **A plausible addition, not built: a plain-language summary** of an already-computed result ("3 locations are below
  usual; Site C had 2 events against a usual 8 to 9"). The model would receive only the computed numbers, and a check
  would confirm that every number in its text appears in its input, with a fixed template as the fallback. Risks:
  invented figures, customer data sent to a third party, cost and latency, non-determinism. It adds no correctness,
  so it is out of scope.
- **Rejected: explaining why** a location is low. The data has no cause signals, so a model could only guess.
- **Where AI is used here:** an AI coding agent built, tested and reviewed this code under supervision, following the
  rules in `CLAUDE.md`.

## Differences from PLAN.md

`PLAN.md` was written before implementation. These later decisions supersede it (each is recorded in
`ai-log/DECISIONS.md`):

| PLAN.md | Implemented | Why |
|---|---|---|
| Account headline has a status | Numbers only: this week, usual, change | The Poisson rule over-flagged account totals in the back-test |
| Single-location accounts show the headline only | They also show the location table (**not yet confirmed**) | With no headline status, a single location's drop would not be flagged anywhere |
| `as_of` is any valid date | Dates later than the latest event are rejected with 400 | Empty weeks beyond the data read as a real drop |
| Response without extras | Adds `latest_event_date` and per-location `history`; Swagger UI and OpenAPI schema | Bound the week navigation; explain `usual` |
| Date input and "No recent activity (usual: 0)" wording | Week navigation; usual 0 shows as `0` with change `—` and "No usual activity to compare with" | Complete weeks make day selection meaningless |
| Null outcome reported as `unknown` | Not exposed: the API returns counts by type only | Outcomes do not feed the metric |
| "About 800 extra connected calls" on June 3 | 805 mixed events (calls, leads, appointments) | Corrected by the spike investigation |
| One frontend smoke test | 80 frontend tests, plus popovers and expandable rows | Behaviour grew during review |

## AI-assisted development log

`ai-log/DECISIONS.md` lists every decision, correction and rejection by the user, with a link to the session where it
happened. `ai-log/sessions/` holds the full exported conversations. `CLAUDE.md` holds the working rules given to the
agent (autonomy, verification, git and logging rules).
