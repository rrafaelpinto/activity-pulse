
⏺ The UI refinement is committed and pushed in two commits, with no attribution
  lines. The frontend tests (45), type-check and production build pass, and the
  120 backend tests still pass. I did not start M5.

  What changed

  Only the frontend changed. The API, business logic and URL state are
  untouched, and there are still no UI libraries, charts or animations.
  - Identity and hierarchy:
    - A product header with a small logo and a clear page title, "Weekly
      activity".
    - A restrained token-based color system for light and dark, and tighter
      typography, with tabular numbers.
    - Cards with consistent spacing.
  - Controls: the account picker, the date input joined to its Latest button,
    and "Data through Jul 27, 2026" now sit in one toolbar.
  - Weekly comparison:
    - The headline is three stats: This week (large), Usual week ("Median of the
      previous 8 weeks") and Change.
    - It is still numbers only.
    - When history is missing it shows "—" with "Needs at least 4 weeks of
      history".
  - Location table:
    - A below-usual row now has a very light tint and one soft amber chip, "▼
      Below usual".
    - The solid orange pill, the left bar and the extra "May need attention"
      label in the row are gone.
    - "Normal" and "Not enough history" are plain muted text.
    - The count appears once, as a small dot and sentence in the card header.
    - A test asserts that the old label doesn't come back.
  - Labels: timezones read "Pacific Time" or "Central Time" instead of
    America/Los_Angeles. The empty state is a proper card: "No activity recorded
    yet", with a short explanation naming the account and week.

  Things I found while reviewing the screenshots

  - Developer wording in an error: the date-out-of-range banner showed the API's
    message, "as_of cannot be later than…". The page now says "That date is
    after the latest available data (Jul 27, 2026)." The API message is
    unchanged.
  - Layout bugs: on mobile the "Data through" note was centered and the stat
    padding was off, and on desktop the stat captions didn't line up. All three
    are fixed. The first mobile fix didn't take, because the cause was
    align-self: center, and I corrected it on the second attempt.
  - Contrast: I checked every text and background pair numerically, and the
    lowest is 4.6:1.

  Review: how I checked it

  I drove Chrome through its debugging protocol. That let me force each color
  scheme and a true 390px mobile viewport, instead of relying on the window size
  and the OS setting. I reviewed:
  - light and dark at desktop width;
  - light and dark at 390px mobile width;
  - a multi-flag account (Metro Collision, two below-usual rows);
  - the empty account;
  - the date-error banner;
  - the early-history state, where "Not enough history" shows on every row.

  There was no horizontal overflow in any capture.

  Not verified: Firefox and Safari, and real touch interaction. I also didn't
  run keyboard or screen-reader checks. The semantics (labelled form controls, a
  table with row headers, role="status" and role="alert") are tested through
  the roles, but I haven't listened to it with a screen reader.

  Visual review instructions

  Backend (skip if your server on port 8000 is still running; I did not touch it
  or its database this time):
  cd backend && ../.venv/bin/python manage.py runserver
  Frontend:
  cd frontend && npm install && npm run dev      # http://localhost:5173
  To compare light and dark, switch your OS appearance, or in Chrome DevTools
  open the Rendering panel and set "Emulate CSS media feature
  prefers-color-scheme". For mobile use the device toolbar at 390px.

  URLs to open (http://localhost:5173/ plus):
  - ?account=12 is the default case: Site C is below usual.
  - ?account=6&as_of=2026-04-20 has two flagged locations in a long list.
  - ?account=6&as_of=2026-06-08 is the burst week, with every location above
    usual.
  - ?account=6&as_of=2026-02-16 is the not-enough-history state.
  - ?account=20 is the empty state.
  - ?account=12&as_of=2026-10-29 is the date past the data, with the friendly
    error and a "Show latest week" button.

  Housekeeping

  - Unexported session: the decision-log rows point to
    ai-log/sessions/2026-10-29-07-dashboard.md, which doesn't exist yet. Please
    export it before M5. It will also cover this refinement.
  - Screenshots: they are in the scratchpad (before/, after/, final/) and not
    committed. Tell me if you want any saved into the repo.

  I'm waiting for your review before M5.

❯ Before we move on, I'd like to take a closer look at the unusual activity
  spike for Metro Collision Centers during the week of June 1, 2026.

  The dashboard shows increases above 1,000% across several locations. The
  calculations seem correct, but I'd like to understand what's happening in the
  underlying data and whether we're missing something important.

  Please inspect the original dataset, especially the events around June 3.
  Look at timestamps, event types, outcomes, durations, and how the activity is
  distributed across locations. Check whether similar patterns appear in other
  accounts.

  I'd also like to understand how much this spike affects the weekly
  comparisons and classifications. You can simulate excluding those events, but
  don't modify the actual data.

  Summarize what you find, distinguish evidence from assumptions, and recommend
  whether we should change anything or simply document the limitation.

  This is investigation only. Don't change code, documentation, or commits yet.
  Let's discuss the findings before deciding what to do.
  ⎿  Read frontend/src/styles.css (568 lines)
  ⎿  Read ../../../../private/tmp/claude-501/-Users-rafaelpinto-workspace-activi
     ty-pulse/96ebab22-5a5c-4b19-ad1e-f75f63da1d69/scratchpad/shots.mjs (69
     lines)
  ⎿  Read backend/activity/services.py (203 lines)
  ⎿  Referenced file backend/activity/tests/test_api.py
  ⎿  Read backend/config/urls.py (12 lines)
  ⎿  Plan file referenced
     (~/.claude/plans/pasted-content-id-acf6-i-d-like-proud-rivest.md)

⏺ Compacted using a summary written while you were away · turn off with
  "idleCompaction": false in settings.json

⏺ I'll work read-only: load the original seed.sql into an in-memory SQLite
  database and run the analysis from scratchpad scripts. I won't touch the repo
  or db.sqlite3.

  Ran 6 shell commands (ctrl+o to expand)

⏺ Profiling confirms the burst is a single-day spike of 805 events across all 15
  locations, unique to this account. I'll now run the impact simulation against
  the real service code using a scratchpad copy of the database, leaving your
  db.sqlite3 untouched. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ The error means system python3 picked up an older Django. I'll rerun with the
  project's venv interpreter.

  Ran 1 shell command (ctrl+o to expand)

⏺ The repo database hash is unchanged, and scenario A (dropping the whole day)
  is done. Next, I'll run scenario B, keeping a typical day's volume of about 12
  events to avoid understating that week, then diff all three. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ Neither scenario changes any "below" flags. Before writing up, I'll check
  three things: how a mean baseline compares to the median choice, whether
  elevated activity persists into the following week, and whether the burst
  day's event mix differs from normal days. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ Found a crash caused by a None key for null outcomes, though the "below" flag
  counts match the earlier back-test (22 over Mar 30–Jul 20, plus 2 from the
  added Mar 23 week). I'll fix the null-key bug and rerun. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ The last row of that run judges Jul 27, a partial week with only 10 events,
  which isn't a valid judged week. I'm rerunning the counterfactual without it.

  Ran 2 shell commands (ctrl+o to expand)

⏺ The June 3 spike looks like real activity at about 80 times the normal volume,
  not a data-quality fault. The shipped median baseline already handles it, but
  a few things on the dashboard are misleading. Nothing in the repo or
  db.sqlite3 changed: the simulations ran on a scratchpad copy of the database,
  and its hash is identical before and after.

  Evidence

  The spike is one local day in one account.
  - Metro Collision Centers (ET) recorded 805 events on Wednesday 2026-06-03. A
    normal day for that account has a median of 10, with the 95th percentile at
    22 and a maximum of 28.
  - All 805 fall on the same local date, spread from 00:43 to 19:54 ET. There is
    no midnight-boundary effect.
  - The week total of 881 is 805 plus 76 from the other six days.

  The burst looks like ordinary traffic, only much larger. I compared it with
  the rest of that account's events:

  ┌──────────────────┬───────────────┬───────────────┬─────────────────────┐
  │      Check       │   Burst day   │   Rest of     │       Result        │
  │                  │               │    account    │                     │
  ├──────────────────┼───────────────┼───────────────┼─────────────────────┤
  │ Event types      │ 60.2 / 26.1 / │ 60.8 / 23.3 / │ χ² 3.7, within      │
  │ (call / lead /   │  13.7%        │  15.9%        │ chance              │
  │ appt)            │               │               │                     │
  ├──────────────────┼───────────────┼───────────────┼─────────────────────┤
  │                  │ 63 / 24 / 11% │ 62 / 24 / 12% │ χ² 1.0, within      │
  │ Call outcomes    │  plus 2.5%    │  plus 3% null │ chance              │
  │                  │ null          │               │                     │
  ├──────────────────┼───────────────┼───────────────┼─────────────────────┤
  │ Call duration    │ avg 754s,     │ avg 765s,     │ same                │
  │                  │ range 30–1499 │ range 26–1499 │                     │
  ├──────────────────┼───────────────┼───────────────┼─────────────────────┤
  │ Locations        │ 42–69 events  │ each 6–8% of  │ χ² 16.3 on 14 df,   │
  │                  │ each          │ the account   │ within chance       │
  ├──────────────────┼───────────────┼───────────────┼─────────────────────┤
  │                  │               │               │ similar             │
  │ Mean local hour  │ 12.1          │ 11.7          │ business-hours      │
  │                  │               │               │ shape               │
  └──────────────────┴───────────────┴───────────────┴─────────────────────┘

  - Not a replay or duplicate dump: 798 of the 805 timestamps are distinct.
    There is one duplicate group, and that is within the 12 duplicate groups the
    dataset already contained.
  - Not a separate bulk insert: the ids (8114–8994) are interleaved with other
    accounts' events. Across the whole table there are zero inversions between
    id order and time order.
  - Not a tracking fault at one site: all 15 locations are affected.

  No other account has anything similar.
  - Outside this burst, no account has a day above 28 events and no location has
    a day above 8.
  - The next largest location-week is 3.0× that location's median, against 8–17×
    for the burst week. No other account-week is above about 1.7× its median.
  - The week after the burst is slightly elevated: 102 against a usual 66, with
    daily counts of 17, 16, 16, 20 and 24. That is at the edge of normal noise
    for this account.

  Impact on comparisons

  I simulated two ways of excluding the day. Scenario A removes all 805 events.
  Scenario B keeps 12 random ones, roughly a typical day. I ran every account
  over 18 judged weeks, 1,242 location-weeks, through the real service code.

  ┌───────────────────────────────┬─────────┬────────────┬──────────────────┐
  │                               │ Actual  │  A: drop   │   B: cap to a    │
  │                               │         │  the day   │    normal day    │
  ├───────────────────────────────┼─────────┼────────────┼──────────────────┤
  │ Headline, week of Jun 1 (881  │ +1,235% │ 76 → +15%  │ 88 → +33%        │
  │ vs usual 66)                  │         │            │                  │
  ├───────────────────────────────┼─────────┼────────────┼──────────────────┤
  │ "Above usual" flags, all      │ 45      │ 32         │ 32               │
  │ weeks                         │         │            │                  │
  ├───────────────────────────────┼─────────┼────────────┼──────────────────┤
  │ "Below usual" flags, all      │ 24      │ 24         │ 24               │
  │ weeks                         │         │            │                  │
  ├───────────────────────────────┼─────────┼────────────┼──────────────────┤
  │ Accounts other than 6         │ none    │ none       │ none             │
  │ affected                      │         │            │                  │
  └───────────────────────────────┴─────────┴────────────┴──────────────────┘

  - The 15 "above" flags that week disappear, apart from one location that stays
    flagged in scenario B. That one is down to which 12 random events I kept.
  - No below-usual flag changes in any scenario. The spike never hides an outage
    and never creates a false alarm.
  - Later weeks barely move. The account headline's usual stays within 72–73.5
    either way. Scenario A produces one or two odd "above" flags in later weeks
    (Site O on Jun 15, Site B on Jun 29). Deleting a whole day makes that week
    unusually low, which pulls the baseline down. This is a reason not to
    simulate or implement exclusion by deletion.
  - The median baseline matters a lot. I recomputed Metro Collision's seven
    complete weeks after the burst using a mean baseline instead. It flags 56 of
    105 location-weeks as below usual, against 1 for the median. Its headline
    usual becomes about 170 against 72.

  What is evidence and what is assumption

  - Evidence: everything above.
  - Assumption (cause): I can't tell whether this was a real campaign or viral
    day, bot traffic, a test fixture planted in a synthetic seed, or something
    else. The data has no source, campaign or tag field, and the docs don't
    mention it.
  - Assumption (median limit): the median tolerates up to 3 inflated weeks out
    of 8. A sustained campaign of 4 or more weeks would shift the baseline. I
    reasoned this from how a median works and didn't simulate it.

  Recommendation

  I recommend documenting this and making one small UI fix. I don't recommend
  excluding the data.
  1. Do not exclude or clean the events.
     - We can't prove they're invalid, and the shape suggests they're genuine.
     - Excluding them needs a rule, such as "a day above 10× the median is an
       outlier", and that adds threshold tuning, product semantics and a new
       dependency on rules the ticket doesn't ask for.
     - Deleting them also distorts later baselines, as scenario A showed.
  2. Document the limitation in the M5 README, with the numbers above.
     - The median handles isolated bursts and the dashboard shows what happened.
     - Bursts of 4 or more weeks, and campaigns generally, are not handled.
     - The data can't tell a campaign from a bot.
  3. Optional, cheap UI clarification, which needs your decision as a product
     change. A "+1,235%" headline is accurate but invites misreading. Two
     options:
     - Cap the display, for example "+1,000% or more", or show "12× usual".
     - Add a neutral note when this_week is far above usual, for example "Much
       higher than usual. This may be a one-off event."

     This would be wording only, with no change to counts, baselines or
     statuses.

  I'd pick the documentation plus the second UI option. Wording affects what
  customers infer, so I'd like your call first.

  If you approve any change, I'll record it in ai-log/DECISIONS.md as a separate
  commit. The scratchpad scripts (a1.py–a6.py, sim*.py, diff.py) are not
  committed. I can attach a short version to the README or DECISIONS entry if
  you want the evidence preserved.

❯ Let's make one final round of product improvements before M5.

  I'd like to replace the date picker with week navigation. Since the dashboard
  always evaluates complete weeks, selecting different days within the same
  week doesn't make much sense. Show the selected week range, with
  previous/next controls and a Latest button. Keep the existing as_of API
  behavior and URL persistence.

  I'd also like a few small information popovers explaining the baseline,
  percentage change, and location statuses. They should work on click or tap,
  including keyboard navigation, without cluttering the interface.

  Finally, let's make the location rows expandable. When I open a location, I
  want to understand the numbers behind its status: the selected week's
  activity, the breakdown by event type, and the weekly counts used to
  calculate its historical median. Extend the existing API response as needed,
  but keep the contract simple.

  Please keep the table compact, reuse the current components, and avoid new UI
  or charting libraries. Don't change the statistical rules or remove any
  events from the dataset.

  Add focused tests for the new API data and frontend interactions. Check
  desktop and mobile layouts, light and dark modes, and run the full test
  suites and production build.

  Commit and push the changes, then give me instructions to test them in the
  browser. Don't start M5 yet. We'll review the result first.

⏺ I'll start by re-reading the current frontend and API code that this touches.

  Read 1 file, ran 1 shell command (ctrl+o to expand)

⏺ Now the existing frontend tests, types and the backend test helpers, so the
  new work follows their conventions.

  Read 1 file, ran 1 shell command (ctrl+o to expand)

⏺ Starting with the backend: expose the weekly counts that feed each location's
  median. The median will be computed from that same list, so the two can't
  disagree.

  Ran 2 shell commands (ctrl+o to expand)

⏺ Now the backend tests: service-level history rules, the API contract, and a
  check against the real seed that the median of history always equals usual.

  Ran 2 shell commands (ctrl+o to expand)

⏺ My test was wrong, not the code: with as_of 05-04 the judged week is the
  second week, so no history exists yet. Using as_of 05-11 gives one real
  history week.

  Ran 1 shell command (ctrl+o to expand)

⏺ Backend is at 134 passing tests. Now the frontend, starting with types, week
  arithmetic and formatting helpers.

  Ran 1 shell command (ctrl+o to expand)
⏺ Now the components: the popover, the week navigator, and the expandable
  detail.

  Read 1 file (ctrl+o to expand)

⏺ Now wire them into the table, headline and app.

  Ran 1 shell command (ctrl+o to expand)

⏺ Now the styles: week navigator, popovers (a bottom sheet on phones), and the
  expanded row.

  Ran 1 shell command (ctrl+o to expand)

⏺ Source compiles; only the test fixtures need the new history field. Now I'll
  rewrite the date-picker tests as week-navigation tests and add popover and
  expand/collapse tests.

  Ran 2 shell commands (ctrl+o to expand)

⏺ All 56 pass. Now the popover and expandable-row tests, as component-level
  files, plus one integration check that the expansion resets when the week
  changes.

  Ran 1 shell command (ctrl+o to expand)

⏺ Everything passed on the first run, so I'll check the tests can actually fail.
  I'll break the code in five places, confirm the suite catches each one, and
  restore the files after.

  Ran 1 shell command (ctrl+o to expand)

⏺ I caught 4 of 5 mutations, but missed the outside-click handler since the
  focus-leave logic was masking it in tests—this matters for Safari, which
  doesn't focus buttons on click. I'll add a dedicated test to exercise that
  path. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ Tests are green. Now the visual check. First I'll confirm the API on port 8000
  is serving the new field (Django's dev server reloads on change), then start
  Vite.

  Ran 1 shell command (ctrl+o to expand)

⏺ The live API returns the history, and the median checks out: 2, 4, 4, 8, 9,
  10, 12, 12 gives 8.5. Now screenshots in light and dark, desktop and 390px,
  with rows expanded and popovers open.

  Read 2 files, ran 1 shell command (ctrl+o to expand)

⏺ Desktop light looks right: the week navigator is joined, the expanded row
  shows type counts and the eight weeks, and the popover floats cleanly. Now
  mobile and dark.

  Read 3 files (ctrl+o to expand)

⏺ Dark mode and mobile views check out—the bottom sheet only appears mid-page
  because it's a full-page screenshot stitch, but it'll pin to the viewport
  bottom on an actual phone. Next I'll capture the two remaining edge cases: a
  location with sparse history and the burst week. · summary

  Read 2 files (ctrl+o to expand)

⏺ The edge cases read well, including the "no earlier weeks yet" and "has 0"
  wording. I'll stop my dev server and run the full verification.

  Ran 1 shell command (ctrl+o to expand)

⏺ All checks pass—80 frontend tests, 134 backend tests, type-check, production
  build, OpenAPI validation—and the API on :8000 still responds with 200. Now
  I'll commit in three focused commits: backend, frontend, then the decision
  log. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ I'll check the first appended row didn't merge into the previous line, then
  push.

  Ran 1 shell command (ctrl+o to expand)

⏺ Week navigation, the info popovers and the expandable location rows are built,
  committed and pushed to origin/main. I did not start M5.

  Everything passes:

  ┌───────────────────────────────────────────┬─────────────────────────────┐
  │                   Check                   │           Result            │
  ├───────────────────────────────────────────┼─────────────────────────────┤
  │ Frontend tests                            │ 80 passed                   │
  ├───────────────────────────────────────────┼─────────────────────────────┤
  │ Backend tests                             │ 134 passed                  │
  ├───────────────────────────────────────────┼─────────────────────────────┤
  │ Type-check, production build, OpenAPI     │ pass                        │
  │ validation                                │                             │
  ├───────────────────────────────────────────┼─────────────────────────────┤
  │ Mutation checks                           │ 6 deliberate breaks, all    │
  │                                           │ caught                      │
  └───────────────────────────────────────────┴─────────────────────────────┘

  The mutation checks led to one extra test for the outside-click path. I
  reviewed light and dark at 1200px and 390px, plus the no-history, burst-week
  and empty-account cases. There was no horizontal overflow anywhere.

  What changed

  - Week navigation:
    - The date picker is gone. The toolbar now has a joined ‹ Jul 20 – Jul 26,
      2026 › control and a Latest button.
    - The page still sends as_of to the API and keeps it in the URL. The
      previous-week and next-week buttons are always one week apart. Old
      bookmarks, including mid-week dates, still work.
    - Next and Latest are disabled on the newest week. The buttons wait while a
      week loads and keep the old range on screen.
  - Popovers:
    - There are three ⓘ buttons: usual week, change, and location statuses
      (beside the "Locations" title).
    - They open on click, tap, Enter or Space. They close on Escape (focus
      returns to the button), when you click elsewhere, or when focus leaves,
      and only one is open at a time.
    - On phones they appear as a sheet at the bottom of the screen.
  - Expandable rows: the location name is now a button with a chevron. Opening
    it shows:
    - a sentence such as "2 events this week against a usual week of 8.5
      (−76.5%)…";
    - this week by type: calls, leads, appointments;
    - the weekly counts behind the usual week, with the median stated.

    Rows stay compact when closed, and open rows reset when you change week or
    account. Locations with too little history get an explanation instead of
    numbers.
  - API: each location has a new history field: [{week_start, count}], oldest
    first. The median is now computed from that same list, so the explanation
    and the number can't disagree. For example, Site C shows 2, 4, 4, 8, 9, 10,
    12, 12, which gives 8.5. A test checks this for every location and week in
    the seed. The statistical rules and the data are untouched.

  Choices I made that you should confirm

  - Previous week is disabled when the shown week has no locations, rather than
    adding an "earliest date" field to the API. The catch is that, on an
    account's first week, you can step back once into an empty week.
  - Duplicate week label: the headline card still says "Week of …", so the range
    appears there and in the navigator. I kept it to tie the numbers to the
    week.
  - Spike wording: I did not implement the wording change from my spike
    investigation (for example "+1,235%"). It is logged as pending your
    decision.

  All of these are recorded in ai-log/DECISIONS.md.

  Not verified

  - Firefox and Safari, and real touch devices. I tested the bottom-sheet
    popover only through Chrome's mobile emulation.
  - Screen-reader behavior. The ARIA states are covered by tests.

  Test it in the browser

  Backend (skip if your server on port 8000 is still running; it reloads on its
  own and already serves the new field):
  cd backend && ../.venv/bin/python manage.py runserver
  Frontend:
  cd frontend && npm install && npm run dev      # http://localhost:5173
  Pages to open, each preceded by http://localhost:5173/:

  ┌──────────────────────────────┬───────────────────────────────────────────┐
  │             Page             │                What to try                │
  ├──────────────────────────────┼───────────────────────────────────────────┤
  │                              │ Expand Site C (below usual, 2 vs 8.5).    │
  │ ?account=12                  │ Click ‹ and › and then Latest, and watch  │
  │                              │ the URL.                                  │
  ├──────────────────────────────┼───────────────────────────────────────────┤
  │ ?account=6&as_of=2026-04-20  │ Two flagged rows. Expand Site G (0 events │
  │                              │  against a 5.5 usual).                    │
  ├──────────────────────────────┼───────────────────────────────────────────┤
  │ ?account=6&as_of=2026-06-08  │ The burst week. Expand any location.      │
  ├──────────────────────────────┼───────────────────────────────────────────┤
  │ ?account=6&as_of=2026-02-16  │ Every row is "Not enough history". Expand │
  │                              │  one to see the explanation.              │
  ├──────────────────────────────┼───────────────────────────────────────────┤
  │ ?account=20                  │ Empty state, with Previous disabled.      │
  ├──────────────────────────────┼───────────────────────────────────────────┤
  │ ?account=12&as_of=2026-10-29 │ The friendly error. Navigation is         │
  │                              │ disabled and "Show latest week" works.    │
  └──────────────────────────────┴───────────────────────────────────────────┘

  For keyboard checks: Tab to an ⓘ or a location name, press Enter or Space to
  open, Esc to close. For themes, switch the OS appearance or use DevTools →
  Rendering → "Emulate CSS prefers-color-scheme". For mobile, use the device
  toolbar at 390px.

  Housekeeping

  - Session export: please /export this session to
    ai-log/sessions/2026-10-29-07-dashboard.md. The new decision rows point to
    that name, and it now also covers the spike investigation.
  - Screenshots: they are in /private/tmp/claude-501/-Users-rafaelpinto-workspac
    e-activity-pulse/96ebab22-5a5c-4b19-ad1e-f75f63da1d69/scratchpad/nav/ and
    are not committed.

  I'm waiting for your review before M5.

❯ I think we're ready for M5.

  Let's focus on documentation and final technical validation. Please review
  the current implementation against PLAN.md, the ticket, and the assessment
  requirements, then prepare a concise README that lets another engineer get
  the application running from scratch.

  Document the architecture, API, how the weekly comparisons work, why we chose
  an 8-week median, the main assumptions and limitations, and where an LLM
  could realistically fit.

  Include what we learned from the Metro Collision spike investigation,
  especially why we kept the original events and how the median protects later
  comparisons.

  Make sure the documentation reflects the actual implementation and our later
  decisions, even where they differ from the original PLAN.md.

  Run the backend and frontend tests, type-check, production build, OpenAPI
  validation, and verify the setup instructions using a fresh environment
  without touching my existing local database.

  Please also check the AI interaction logs for missing files or broken
  references, and record any relevant decisions or corrections.

  Keep this focused. Don't add features, refactor working code, or introduce
  new infrastructure. Commit and push the documentation and any necessary small
  corrections separately.

  When you're done, summarize the verification results, remaining risks, and
  anything that still needs attention. Don't submit anything or treat the
  project as finished. I'll decide whether we need further improvements before
  submission.

⏺ I'll start by re-reading the ticket, the product background and PLAN.md, so
  the review is against the source documents rather than my memory of them.

  Read 1 file, ran 1 shell command (ctrl+o to expand)

⏺ Now the AI log: which files exist, and whether every session reference in
  DECISIONS.md resolves.

  Ran 1 shell command (ctrl+o to expand)

⏺ All session references check out. Now I'll verify what the 13:07 export
  covers, given it predates the week-navigation work that finished around 15:10.
  · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ The 07 export cuts off before the spike investigation and week-navigation
  work, yet five DECISIONS rows reference it—I'll fix that after the code
  review. Now I'm checking the implementation against PLAN.md claim by claim.
  · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ I've found PLAN.md discrepancies—outcomes aren't exposed by the API, and the
  UI doesn't use the "No recent activity (usual: 0)" wording. I'll gather a few
  more facts before listing all deviations, and meanwhile I'm kicking off a
  from-scratch verification in a clean clone (its own venv and database,
  separate from your backend/db.sqlite3) while I write the README. · summary

  Ran 1 shell command (ctrl+o to expand)
⏺ The clone will contain only committed files. I'm running the setup steps from
  a fresh clone now to find problems early, and I'll repeat the run from the
  final README commit.

  Ran 1 shell command (ctrl+o to expand)

⏺ The backend side of the fresh clone works. Next in the clone: the backend
  tests, OpenAPI validation, a server on a spare port, and the frontend install,
  checks and build.

  Ran 2 shell commands (ctrl+o to expand)

⏺ The fresh clone passed all checks. Next, I'll point the clone's own Vite proxy
  at port 8765 (leaving your :8000 server untouched) to run an end-to-end test
  against the fresh database, and also test the import safety guard there.
  · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ The curl failure was my unquoted ? in zsh, not an app problem. I'll check the
  end-to-end screenshot to confirm real data loaded rather than an error state.

  Read 1 file (ctrl+o to expand)

⏺ The new stack checks out end to end — the screenshot confirms the burst week
  (881 vs. usual 66, +1,234.8%) with all 15 locations flagged "above usual."
  Before writing further, I'll scan for stale comments or leftover wording from
  recent changes to the date picker, headline status, and unknown outcomes.
  · summary

  Searched for 1 pattern, ran 1 shell command (ctrl+o to expand)

⏺ No stale comments or wording in the code. Now the README, written against what
  is actually implemented, with the later decisions called out where they
  differ from PLAN.md.

⏺ Write(README.md)
  ⎿  Wrote 307 lines to README.md
      1 # Activity Pulse (DASH-247)
      2
      3 Answers a customer's question "is this normal for us?" at a glanc
        e. For one account it shows how the last
      4 complete week of activity (calls, leads and appointments) compare
        s with that account's usual week, and which
      5 locations are unusually quiet.
      6
      7 - **Backend:** Django 5.2 + Django REST framework, SQLite, read-o
        nly JSON API with Swagger UI.
     … +300 lines (ctrl+o to expand)

⏺ I wrote the example's location id from memory, so I'm checking it and the
  other facts quoted in the README against the live API.

  Ran 1 shell command (ctrl+o to expand)

⏺ Good catch: the location id is 48, not 31. I'm fixing that and tightening
  three statements that were looser than the data.

  Ran 1 shell command (ctrl+o to expand)

⏺ The notice says the README changed on disk beyond my edit. I'll read it back
  to confirm what is there.

  Ran 1 shell command (ctrl+o to expand)

⏺ I'll correct the README to note one location stayed "above" in the capped
  simulation, then commit it locally and test the commands against a fresh
  clone. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ Now the fresh-environment run, executing the README's commands exactly as
  written from a clone of that commit, with errors fatal.

  Ran 2 shell commands (ctrl+o to expand)

⏺ All checks on the fresh README commit clone pass cleanly, and your database
  hash is unchanged. Next, I'll fix the AI log by re-pointing the five rows
  whose work isn't in the 07 export and recording this session's decisions.
  · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ I stated a row count in that entry, so I'll verify it, and check whether any
  export is unreferenced.

  Ran 1 shell command (ctrl+o to expand)

⏺ Found two issues: my own entry has the wrong row count (should be 30, not 33),
  and 04-django-setup.md isn't referenced by any row. I'll now check whether
  the Django-simplification correction points to the wrong export. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ The exports are cumulative, and 03 does not contain the simplification
  request, while 04 does. So that row cites the wrong export. I'll check the
  other rows citing 03, 05 and 06 the same way.

  Ran 2 shell commands (ctrl+o to expand)

⏺ Row 26's Django simplification citation points to 03, but that conversation
  actually belongs in 04-django-setup.md, which has no citations yet. I'll fix
  the reference and update the wording and count accordingly. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ I only content-checked part of the earlier rows, so I'm narrowing the claim in
  the audit entry to what I actually verified.

  Ran 1 shell command (ctrl+o to expand)

⏺ Both commits are local. The code hasn't changed since the last verified
  commit, so I'll push now and confirm the remote matches.

  Ran 1 shell command (ctrl+o to expand)

⏺ The README is written and pushed in two commits. Nothing is submitted, and I
  haven't treated the project as finished.

  Commits on origin/main

  - 00a3b2b docs: add README.
  - ec2ab81 docs(ai-log): fix two session references and record M5 decisions.

  I found no code problems, so there are no code commits. PLAN.md is unchanged.
  The README has a "Differences from PLAN.md" table for the places where the
  plan and the implementation diverge.

  Verification

  ┌───────────────────────────────────┬─────────────────────────────────────┐
  │               Check               │               Result                │
  ├───────────────────────────────────┼─────────────────────────────────────┤
  │ Fresh clone of the README commit: │ Imported 20 accounts, 69 locations, │
  │  venv, pip install, migrate,      │  12,626 events                      │
  │ import_seed                       │                                     │
  ├───────────────────────────────────┼─────────────────────────────────────┤
  │ import_seed run again on the same │ Refused, as documented              │
  │  database                         │                                     │
  ├───────────────────────────────────┼─────────────────────────────────────┤
  │ Backend tests                     │ 134 passed                          │
  ├───────────────────────────────────┼─────────────────────────────────────┤
  │ OpenAPI validation (--validate    │ exit 0                              │
  │ --fail-on-warn)                   │                                     │
  ├───────────────────────────────────┼─────────────────────────────────────┤
  │ npm ci, type-check, tests, build  │ 80 tests passed, build OK           │
  ├───────────────────────────────────┼─────────────────────────────────────┤
  │                                   │ Same figures as your database (Site │
  │ Fresh API on port 8765            │  C below usual, 2 vs 8.5); Swagger  │
  │                                   │ page and schema return 200          │
  ├───────────────────────────────────┼─────────────────────────────────────┤
  │ Fresh build plus fresh API, in    │ The burst week renders (881 vs 66); │
  │ Chrome                            │  no overflow at 390px               │
  ├───────────────────────────────────┼─────────────────────────────────────┤
  │ Your backend/db.sqlite3 and       │ Hash 89f927f… identical before and  │
  │ server on :8000                   │ after; the server still returns 200 │
  └───────────────────────────────────┴─────────────────────────────────────┘

  All of this ran in clones under the scratchpad, each with its own virtualenv
  and database. The one Vite edit (the proxy port) was made in the clone only.

  Review against PLAN.md and the ticket

  The ticket requirements are met: a baseline comparison, multi-location
  support, and below-usual locations listed first so a Monday-morning admin can
  act on them. Alerting and ML are untouched. These plan claims no longer
  matched the code or data, and the README corrects them:
  - June 3 spike: the plan said about 800 connected calls. It was 805 mixed
    events: calls, leads and appointments.
  - Outcomes: the plan said null outcomes would be reported as unknown. The API
    never exposes outcomes, only counts by event type.
  - Usual of 0: the "No recent activity (usual: 0)" wording is not implemented.
    A usual of 0 shows as 0 with change —.

  Log audit

  Every file cited in DECISIONS.md exists, except one that is waiting for your
  export. I fixed two problems:
  1. Five rows cited an export that doesn't cover their work. The week
     navigation, popovers, history and spike rows cited 07-dashboard.md, which
     ends at the UI refinement (exported at 13:07). They now cite
     2026-10-29-08-spike-week-nav-m5.md, which doesn't exist until you export
     this session.
  2. The Django-simplification correction cited 03-m1-import.md. That
     conversation is in 04-django-setup.md, so the row now cites that export,
     which no row cited before.

  Exports are cumulative, so each row should cite the first export that contains
  its discussion. The corrections and my M5 decisions are recorded as new rows.

  Remaining risks and attention items

  - Export needed: please /export this session as
    ai-log/sessions/2026-10-29-08-spike-week-nav-m5.md. Nine rows cite that
    name.
  - Unconfirmed deviation: single-location accounts show the location table,
    where PLAN.md says headline only. This is flagged in the README but still
    needs your answer.
  - Spike wording: a change of +1,234.8% is shown as computed, and I haven't
    decided whether to soften it. The README lists it as a limitation.
  - README length: it is 307 lines and about 3,000 words. It covers everything
    you listed, but it is longer than "concise". I can trim it if you prefer.
  - npm run dev not run in the fresh clone: I verified the production build and
    vite preview, not the dev server from scratch. I did run the dev server
    earlier, in the real repo.
  - Local environment only:
    - I only tested Python 3.12 and Node 24.15.
    - The Vite proxy to port 8000 is hardcoded.
    - Swagger UI needs internet.
    - Chrome is the only browser I tested, and I didn't use a screen reader.
    - There is no CI.
  - README numbers: the hard-coded test counts (134 and 80) and the spike
    figures are correct today but would go stale if the code or data changes.

  A Vite process from your own repo (PID 27137) is running. It isn't mine, so I
  left it alone.