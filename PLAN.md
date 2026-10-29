# DASH-247 Implementation Plan

Help a customer answer "is this normal for us?" at a glance, and spot which location needs attention. Budget: 4-6 hours.

## 1. Scope

**In:** a Django/DRF API, a minimal React/TypeScript page, SQLite, a reproducible seed import, and tests for the metric and the import.

**Out:** alerting/notifications, ML/forecasting (per product), auth, charts library, benchmarks across accounts, exports, Docker.

**Assumptions (stated, not silently resolved):**
- "Normal" means the location's own recent history, not an industry benchmark.
- The dashboard has no login in this exercise, so the page has an account picker.
- Status is an indication that activity may need attention, not a diagnosis of an anomaly.
- Flag below-usual only. Above-usual is shown but not highlighted.

## 2. Data findings that drive the design

From the seed data (12,626 events, 20 accounts, 69 locations, 2026-02-01 to 2026-07-27):
- Location names (`Site A`...) are unique only within an account, so the key is `(account, location)`.
- Typical weekly volume is small (about 4-10 events per location), and variance is roughly equal to the mean. Percentage-change rules would be mostly noise.
- On 2026-06-03, about 800 extra connected calls hit all 15 Metro Collision locations in one day. They are kept (no evidence they are invalid); a median baseline absorbs them.
- 12 apparent duplicate rows are kept for the same reason.
- `outcome` is null on 3% of events; `duration_seconds` on 4% of calls. Null outcome is reported as `unknown`, never counted as missed.
- Quiet Harbor Spa (account 20) has no events.
- Data ends on Monday 2026-07-27, so "now" is an `as_of` parameter, not the wall clock.
- Timezones: five US zones (Phoenix has no DST) plus UTC. Weeks bucketed in UTC vs local differ for only 8 events, but the local week is the correct one, and DST (2026-03-08) falls inside the data.

## 3. Metric definition

**Week:** Monday-Sunday in the account's timezone (`zoneinfo`). UTC `occurred_at` becomes a local date, then a local Monday. Weeks are calendar dates, not 168-hour offsets, so DST is safe.

**Judged week:** the complete local week before the week containing `as_of`. Default `as_of` is the date of the latest event (2026-07-27), so the judged week is 2026-07-20 to 07-26. A partial week is never judged or used in a baseline.

**Counted value:** total weekly events (calls + leads + appointments). Per-type counts are shown for context only.

**History:** a location's history starts the week after its first event week (that week may be partial). Weeks after that with no events count as **0**. Weeks before it are not zeros because the location did not exist yet.

**Baseline `e`:** median of the up-to-8 history weeks before the judged week. At least 4 history weeks are required; otherwise status is `not_enough_data`. A zero baseline with enough history is a valid baseline (see below).

**Status** with `c` = judged-week count:

| Condition | Status |
|---|---|
| fewer than 4 history weeks | `not_enough_data` |
| `e = 0` and `c = 0` | `normal` (usual 0; UI says "No recent activity") |
| `e = 0` and `c > 0` | `above` |
| `P(X <= c \| Poisson(e)) < 0.025` | `below` |
| `P(X >= c \| Poisson(e)) < 0.025` | `above` |
| otherwise | `normal` |

The CDF is a short sum in plain Python (no scipy).

**Account headline:** the same rule applied to the account's own weekly totals (all locations summed per week, zeros counted, same 4-week rule). It is not a sum of location medians.

**Thresholds** (`below` when the count is at most):

| usual (e) | 3.5 | 4.5 | 5.5 | 6.5 | 8 | 10 | 15 | 30 |
|---|---|---|---|---|---|---|---|---|
| flag if <= | none | 0 | 0 | 1 | 2 | 3 | 7 | 19 |

**Back-test** over 17 judged weeks (2026-03-30 to 2026-07-20), 1,173 location-weeks:

| Rule | Flags | Per week |
|---|---|---|
| Poisson tail, 0.025 (chosen) | 22 (1.9%) | 1.3 (max 3) |
| `c <= 0.5e`, `e >= 3` | 126 (10.7%) | 7.4 |
| `c <= 0.6e`, `e >= 5` | 160 (13.6%) | 9.4 |

At the default `as_of` the result is 1 below, 1 above, 67 normal.

**Reference cases** (prior-8 median `e`, judged count `c`), used as test fixtures:
- Account 12 Site C, week 2026-07-20: e 8.5, c 2 -> `below`.
- Account 6 Site G, week 2026-04-13: e 5.5, c 0 -> `below`.
- Account 6 Site G, week 2026-06-29: the prior weeks include the 57-event burst week, e stays 4.5, c 0 -> `below`.
- Account 18 Site C (lowest volume): 2026-06-29 e 6, c 1 -> `below`; 2026-07-13 e 6, c 4 -> `normal`.
- Account 16 (single location), week 2026-07-20: e 6.5, c 8 -> `normal`.
- Account 6 Site M, week 2026-06-01: e 3.5, c 50 -> `above`.

**Assumptions of the Poisson rule:** events are independent; the weekly rate is roughly stationary over 8 weeks; variance is about equal to the mean (checked: mean 4.2, sd 2.0 at a low-volume location); the median of 8 weeks is a fair estimate of the rate.

**Limitations:**
- Bursts and campaigns violate independence. The median limits the damage but cannot remove it.
- Trends and seasonality are not modeled; a growing or shrinking location is compared with its own past.
- Expect about 1.3 flags per Monday across the 69 locations (well under 1 per week for the largest account). Without ground truth these are not necessarily false positives; they are locations the rule says deserve a look. The 0.025 threshold is a single tunable constant.
- A location silent for most of the window gets a baseline of 0 and is never flagged. Event data cannot tell a closed location from a broken one.
- A location with no events ever does not exist in the data.
- Locations with a baseline under about 3.7 cannot be flagged at all; a single zero week is not strong enough evidence at that volume.

**Wording:** the UI says "Below usual: may need attention". It never says "anomaly" or "problem".

## 4. Data model

```text
Account        id (kept from seed), name, industry, timezone (validated IANA), created_at
Location       id, account FK, name                 UNIQUE(account, name)
ActivityEvent  id (kept from seed), location FK, event_type, occurred_at (UTC, aware),
               duration_seconds (null), outcome (null)
```

- **`location` is normalized** because it is the unit the feature reports on and gives the API a stable id. Rows are derived from distinct `(account, location)` at import. Events carry no `account_id`; it is derived through the location, which avoids inconsistent pairs.
- **`event_type` and `outcome` are not normalized.** They are tiny fixed sets with no attributes: `TextChoices` plus database `CheckConstraint`s. A new type needs a migration, which is acceptable.
- **Constraints** (all verified against the seed, 0 violations):
  - `event_type` is one of the 3 values.
  - `outcome` is null or valid for its type: calls `connected|missed|voicemail`, leads `open|converted`, appointments `completed|no_show`.
  - `duration_seconds` is null, or positive and only for `call_received`.
  - No uniqueness on `(location, event_type, occurred_at)`, because the duplicates are kept.
- **Index:** one, on `(location, occurred_at)`. 12.6k rows need nothing more.
- Standard Django migrations. The SQLite file is already gitignored.

**Seed import** (`manage.py import_seed`):
- Loads `schema.sql` and `seed.sql` into an in-memory stdlib `sqlite3`, so there is no hand parsing of SQL.
- Refuses to run on a non-empty database unless `--replace` is passed.
- Runs in one transaction. Preserves original ids and every row, including duplicates and nulls. Timestamps become UTC-aware datetimes.
- Before committing, verifies 20 accounts, 69 locations, 12,626 events, and per-account event counts against the source. Any mismatch rolls back.
- Reproduce with: `migrate && import_seed`.

## 5. API and UI

**API**
- `GET /api/accounts/` returns id, name, timezone for the picker.
- `GET /api/accounts/{id}/activity/?as_of=YYYY-MM-DD` returns:
  - `week` (start, end, local dates) and `as_of`;
  - `headline`: this week, usual, % delta, status;
  - `locations`: id, name, this week, usual, delta, status, per-type counts (calls, leads, appointments).
- Locations are sorted `below` first (largest shortfall first), then the rest by name.
- Invalid `as_of` or unknown account returns a clear 400/404.

**UI** (one page, no extra features)
- Account picker, headline card, and a ranked location table with a status badge.
- Single-location accounts show the headline only.
- States: loading, error, empty account (no events), `not_enough_data`, and "No recent activity (usual: 0)".
- **Selected account and `as_of` live in URL query parameters** (`?account=6&as_of=2026-07-27`). They are read on load and updated with `history.replaceState`. Invalid values fall back to defaults. No other client-side state storage.

## 6. Where would an LLM fit?

- **Not in deciding "normal".** That must be deterministic, auditable and testable. Counts are tiny, and a statistical rule beats a model here, with no cost, latency or run-to-run drift. The back-test above is only possible because the rule is deterministic.
- **Plausible, not built: a plain-language summary** of an already-computed result ("3 locations are below usual; Site C had 2 events vs a usual 8-9"). The model would get only the computed numbers, and a check would confirm every number in its text appears in the input, with a deterministic template as fallback. Risks: invented figures, customer data sent to a third party, cost and latency, non-determinism. It adds nothing to correctness, so it is out of scope.
- **Rejected: explaining why a flag happened.** The data has no cause signals, so a model would only guess.
- **Where AI is used here:** an AI agent builds, tests and reviews the code under supervision, with the evidence in `ai-log/`.

## 7. Verification

Backend tests (the metric and the import matter most):
- DST week (2026-03-02 and 03-09), a Phoenix account, a UTC account.
- An event whose week differs between UTC and local time.
- Zero weeks count as zero; zero baseline (`c = 0` normal, `c > 0` above); under 4 history weeks gives `not_enough_data`.
- The reference cases in section 3, including the burst not hiding the Site G outage.
- Null outcome reported as `unknown`; partial final week never judged.
- Account headline uses account weekly totals, not location medians.
- Import: counts, ids preserved, duplicates kept, `--replace` guard, rollback on mismatch.
- API: ordering, 400/404, empty account (Quiet Harbor Spa).

Frontend: one smoke check that the URL params restore the selected account and `as_of` after a reload. Finish with a manual run of the real app at the default `as_of`.

## 8. Milestones

| # | Work | Time |
|---|---|---|
| M1 | Django project, models, migrations, `import_seed` with tests | 1.0 h |
| M2 | Weekly service and Poisson rule, tests from section 7 | 1.25 h |
| M3 | DRF endpoints and API tests | 0.75 h |
| M4 | React/TS page with URL state | 1.25 h |
| M5 | README (run, assumptions, limitations, LLM section), final run-through | 0.5 h |

Total about 4.75 h, leaving about 1 h of buffer. Each milestone is verified, committed, and pushed after approval.

**Cut line if time slips:** drop the per-type breakdown columns first, then account picker polish. Never cut the metric tests or the import tests.
