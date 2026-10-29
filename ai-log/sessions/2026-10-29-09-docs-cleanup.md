
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

❯ <ide_opened_file>The user opened the file /Users/rafaelpinto/workspace/activi
  ty-pulse/ai-log/sessions/2026-10-29-08-spike-week-nav-m5.md in the IDE. This
  may or may not be related to the current task.</ide_opened_file>

❯ Before the final assessment review, I'd like to clean up a few documentation
  details.

  The README is a bit longer than necessary. Please make it more concise
  without losing the setup instructions, technical decisions, important
  limitations, or the key findings from the Metro Collision investigation.

  Let's also confirm that single-location accounts should display the location
  table, since the headline no longer carries a status. Update the README and
  decision log accordingly.

  For the Metro Collision spike, keep the exact percentages as they are. The
  expandable history already provides enough context, so we don't need
  additional wording or UI changes.

  Remove hardcoded test counts from the README, since they can become outdated.
  Also make sure the back-test results are described as observed flags, not
  confirmed false positives.

  Please verify that the latest session export is committed and that all
  decision-log references resolve correctly.

  Keep this documentation-only. Run any relevant checks, then commit and push
  the changes. Don't start another development phase or make any submission.
⏺ First I'll check the export's state: whether it exists, whether it's
  committed, and what it covers.

  Ran 1 shell command (ctrl+o to expand)

⏺ The export exists and was committed by you in b317e7c. But it has no mention
  of chi-square, InfoPopover or history_weeks, so I'm checking what it actually
  covers, since nine log rows cite it.

  Ran 1 shell command (ctrl+o to expand)

⏺ The 08 export (commit b317e7c) is pushed and main is synced, resolving the
  nine rows that cite it—though this turn's decisions will need a new 09 export
  I'll flag as missing. Next, I'm scanning for every mention of false positives,
  hard-coded counts, or softer spike wording before rewriting. · summary

  Searched for 1 pattern (ctrl+o to expand)

⏺ Now the rewrite. I'm keeping every section you named and cutting the prose
  around it.

⏺ Write(README.md)
  ⎿  Error writing file

⏺ The README changed on disk since my last read, so I'll read the current
  version before overwriting it.

  Ran 1 shell command (ctrl+o to expand)

⏺ The README matches the committed version, so nothing was lost. The tool just
  needs a fresh Read first.

  Read 1 file (ctrl+o to expand)

⏺ Write(README.md)
  ⎿  Added 144 lines, removed 171 lines
       1  # Activity Pulse (DASH-247)
       2  
       3 -Answers a customer's question "is this normal for us?" at a gla
         -nce. For one account it shows how the last                     
       4 -complete week of activity (calls, leads and appointments) compa
         -res with that account's usual week, and which                  
       5 -locations are unusually quiet.                                 
       3 +Answers a customer's question "is this normal for us?". For one
         + account it compares the last complete week of                 
       4 +activity (calls, leads, appointments) with that account's usual
         + week and shows which locations are unusually quiet.           
       5  
       7 -- **Backend:** Django 5.2 + Django REST framework, SQLite, read
         --only JSON API with Swagger UI.                                
       8 -- **Frontend:** React 19 + TypeScript + Vite, plain CSS, no UI 
         -or chart libraries.                                            
       6 +- **Backend:** Django 5.2, Django REST framework, SQLite. Read-
         +only JSON API with Swagger UI.                                 
       7 +- **Frontend:** React 19, TypeScript, Vite, plain CSS. No UI or
         + chart libraries.                                              
       8  - **Data:** `seed.sql` (20 accounts, 69 locations, 12,626 event
          s, 2026-02-01 to 2026-07-27).
       9  
      11 -`PLAN.md` is the original plan and is kept unchanged as a recor
         -d. Where the implementation differs from it,                   
      12 -see [Differences from PLAN.md](#differences-from-planmd). This 
         -README describes what is built.                                
      10 +`PLAN.md` is the original plan, kept unchanged as a record. Thi
         +s README describes what is built; see                          
      11 +[Differences from PLAN.md](#differences-from-planmd).          
      12  
      13  ## Run it
      14  
      15  Requirements: Python 3.12 (tested; Django 5.2 supports 3.10+), 
          Node 22.12+ (tested on 24) and npm.
      16  
      17  ```bash
      19 -# 1. Backend (terminal 1), from the repository root            
      18 +# Backend (terminal 1), from the repository root               
      19  python3 -m venv .venv
      20  .venv/bin/pip install -r backend/requirements.txt
      21  cd backend
     ...
       23  ../.venv/bin/python manage.py import_seed        # "Imported 2
           0 accounts, 69 locations, 12626 events."
       24  ../.venv/bin/python manage.py runserver          # http://127.
           0.0.1:8000
       25  
       27 -# 2. Frontend (terminal 2), from the repository root          
       26 +# Frontend (terminal 2), from the repository root             
       27  cd frontend
       28  npm ci
       29  npm run dev                                      # http://loca
           lhost:5173
       30  ```
       31  
       33 -Open <http://localhost:5173>. Good pages to start with (append
          - to the URL):                                                 
       32 +Pages worth opening (append to the URL):                      
       33  
       35 -| Page | What it shows |                                      
       34 +| Page | Shows |                                              
       35  |---|---|
       36  | `/?account=12` | The default week: one location (Site C) bel
           ow usual |
       38 -| `/?account=6&as_of=2026-06-08` | The Metro Collision burst w
          -eek (see [the spike](#the-metro-collision-spike)) |           
       37 +| `/?account=6&as_of=2026-06-08` | The Metro Collision burst w
          +eek ([see below](#the-metro-collision-spike)) |               
       38  | `/?account=6&as_of=2026-04-20` | Two locations below usual |
       39  | `/?account=6&as_of=2026-02-16` | Every location has too litt
           le history |
       40  | `/?account=20` | An account with no events |
       41  
       43 -API explorer: <http://127.0.0.1:8000/api/docs/> (Swagger UI; i
          -ts assets load from a CDN, so it needs internet).             
       44 -The raw schema is at `/api/schema/`.                          
       42 +API explorer: <http://127.0.0.1:8000/api/docs/> (Swagger UI; a
          +ssets load from a CDN, so it needs internet). The raw         
       43 +schema is at `/api/schema/`.                                  
       44  
       46 -Notes:                                                        
       47 -- `import_seed` refuses to run on a database that already has 
          -data. Use `import_seed --replace` to reload; it               
       48 -  runs in one transaction, preserves every id and row, and rol
          -ls back if any count differs from the source.                 
       49 -- The Vite dev server proxies `/api` to `127.0.0.1:8000` (`fro
          -ntend/vite.config.ts`), so there is no CORS setup.            
       50 -  `npm run build` produces static files in `frontend/dist`; Dj
          -ango does not serve them, and there is no                     
       51 -  deployment configuration. `npm run preview` serves the build
          - on port 4173 with the same proxy.                            
       52 -- Settings are development-only: a fixed `SECRET_KEY`, `DEBUG 
          -= True`, no authentication.                                   
       45 +- `import_seed` refuses to run on a database that already has 
          +data; `--replace` reloads. It runs in one transaction,        
       46 +  keeps every id and row, and rolls back if any count differs 
          +from the source.                                              
       47 +- Vite proxies `/api` to `127.0.0.1:8000` (`frontend/vite.conf
          +ig.ts`), so there is no CORS setup. `npm run build`           
       48 +  writes static files to `frontend/dist`; Django does not serv
          +e them and there is no deployment configuration.              
       49 +- Settings are development-only: fixed `SECRET_KEY`, `DEBUG = 
          +True`, no authentication.                                     
       50  
       51  ## Tests and checks
       52  
       53  ```bash
       54  cd backend
       58 -../.venv/bin/python manage.py test                            
          -               # 134 tests                                    
       55 +../.venv/bin/python manage.py test                            
       56  ../.venv/bin/python manage.py spectacular --validate --fail-on
           -warn --file /tmp/schema.yml
       57  
       58  cd ../frontend
       62 -npm run typecheck && npm test && npm run build                
          -               # 80 tests                                     
       59 +npm run typecheck && npm test && npm run build                
       60  ```
       61  
       65 -The backend tests cover the weekly rules (DST weeks, Phoenix a
          -nd UTC accounts, events whose week differs between UTC        
       66 -and local time, zero weeks, short histories, the burst not hid
          -ing an outage), the import (ids, duplicates,                  
       67 -`--replace` guard, rollback), the API contract and a back-test
          - against the real seed. The frontend tests cover              
       68 -URL state, week navigation, popovers, expandable rows and the 
          -loading, error and empty states.                              
       62 +Backend tests cover the weekly rules (DST weeks, Phoenix and U
          +TC accounts, events whose week differs between UTC and        
       63 +local time, zero weeks, short histories, a burst not hiding an
          + outage), the import (ids, duplicates, `--replace`,           
       64 +rollback), the API contract and a back-test on the real seed. 
          +Frontend tests cover URL state, week navigation,              
       65 +popovers, expandable rows and the loading, error and empty sta
          +tes.                                                          
       66  
       67  ## Architecture
       68  
       69  ```text
       70  seed.sql ──import_seed──▶ SQLite ──ORM──▶ activity/services.py
            ──▶ DRF views ──▶ /api/… ──▶ React page
       74 - schema.sql              (3 tables)       weekly rules, no HTT
          -P     serializers   (Vite proxy)                              
       71 + schema.sql                               weekly rules, no HTT
          +P     serializers   (Vite proxy)                              
       72  ```
       73  
       74  ```text
       78 -backend/config/              settings, URLs                   
       79 -backend/activity/models.py   Account, Location, ActivityEvent 
          -(constraints, one index)                                      
       80 -backend/activity/services.py the metric: weeks, baseline, stat
          -us. No Django request/response code                           
       81 -backend/activity/serializers.py, views.py     the API contract
          - and OpenAPI annotations                                      
       75 +backend/activity/models.py       Account, Location, ActivityEv
          +ent (constraints, one index)                                  
       76 +backend/activity/services.py     the metric: weeks, baseline, 
          +status. No request/response code                              
       77 +backend/activity/serializers.py, views.py   API contract and O
          +penAPI annotations                                            
       78  backend/activity/management/commands/import_seed.py
       83 -backend/activity/tests/      backend tests                    
       84 -frontend/src/                App (state, URL, fetching), WeekN
          -av, HeadlinePanel, LocationTable,                             
       85 -                             LocationDetail, InfoPopover, Empt
          -yState, weeks/format/urlState helpers                         
       86 -ai-log/                      decisions and full AI session exp
          -orts (see the end of this file)                               
       79 +frontend/src/                    App (state, URL, fetching), W
          +eekNav, HeadlinePanel, LocationTable,                         
       80 +                                 LocationDetail, InfoPopover, 
          +EmptyState, helpers                                           
       81 +ai-log/                          decisions and full AI session
          + exports                                                      
       82  ```
       83  
       89 -**Data model.** `Location` is normalized out of the seed's `lo
          -cation` string because it is the unit the feature             
       90 -reports on and names are only unique within an account (`Site 
          -A` exists in many accounts). `event_type` and                 
       91 -`outcome` stay as text with `TextChoices` and database check c
          -onstraints (an outcome must be valid for its event            
       92 -type; a duration only for calls). There is one index, `(locati
          -on, occurred_at)`. Duplicate-looking events are kept,         
       93 -so there is no unique constraint on them.                     
       84 +`Location` is normalized out of the seed's `location` string: 
          +it is the unit the feature reports on, and names like         
       85 +`Site A` are only unique within an account. `event_type` and `
          +outcome` stay as text with `TextChoices` and database         
       86 +check constraints (an outcome must fit its event type; a durat
          +ion only for calls). There is one index,                      
       87 +`(location, occurred_at)`. Duplicate-looking events are kept, 
          +so they have no unique constraint.                            
       88  
       89  ## API
       90  
       97 -Read-only: `GET`, `HEAD` and `OPTIONS` only, no authentication
          -.                                                             
       91 +Read-only (`GET`, `HEAD`, `OPTIONS`), no authentication.      
       92  
       93  | Endpoint | Returns |
       94  |---|---|
       95  | `GET /api/accounts/` | `[{id, name, timezone}]`, sorted by n
           ame |
      102 -| `GET /api/accounts/{id}/activity/?as_of=YYYY-MM-DD` | The we
          -ekly comparison below. `as_of` is optional |                  
       96 +| `GET /api/accounts/{id}/activity/?as_of=YYYY-MM-DD` | The we
          +ekly comparison. `as_of` is optional |                        
       97  
      104 -`as_of` defaults to the date of the latest event. The judged w
          -eek is the complete week before the week containing           
      105 -`as_of`, so any date in the following week selects the same we
          -ek. Errors:                                                   
       98 +`as_of` defaults to the latest event date. The judged week is 
          +the complete week before the week containing `as_of`,         
       99 +so any date in the following week selects it. Errors: `400 {"a
          +s_of": ["…"]}` for a malformed or blank date, one             
      100 +outside 2000-01-01..2100-12-31, or one later than `latest_even
          +t_date` (beyond the data, empty weeks would read as a         
      101 +real drop); `404 {"detail": "Account not found."}`.           
      102  
      107 -| Status | When | Body |                                      
      108 -|---|---|---|                                                 
      109 -| 400 | `as_of` is malformed, blank, outside 2000-01-01..2100-
          -12-31, or later than `latest_event_date` | `{"as_of": ["…"]}` 
          -|                                                             
      110 -| 404 | Unknown account | `{"detail": "Account not found."}` |
      111 -                                                              
      112 -Later dates are rejected on purpose: beyond the newest data th
          -e empty weeks would read as a real drop in activity.          
      113 -                                                              
      114 -Example (`/api/accounts/12/activity/`, locations and history s
          -hortened):                                                    
      115 -                                                              
      103  ```json
      104  {
      105    "account": {"id": 12, "name": "Redline Tire & Service", "tim
           ezone": "America/Los_Angeles"},
     ...
      118  ```
      119  
      120  - `headline` is numbers only: no status for the account as a w
           hole (see below).
      134 -- `usual` and `delta_pct` are `null` without enough history (a
          -nd `delta_pct` when `usual` is 0), never a division error.    
      135 -- `status` is `below`, `above`, `normal` or `not_enough_data`.
          - Locations are sorted below-usual first, largest              
      136 -  shortfall first, then by name.                              
      137 -- `history` lists the exact weekly counts `usual` is the media
          -n of, oldest first. Each location's median is computed        
      138 -  from this list, so the explanation and the number cannot dis
          -agree.                                                        
      139 -- `calls`, `leads` and `appointments` are this week's counts b
          -y event type.                                                 
      140 -- Numbers are rounded to one decimal. The Swagger UI documents
          - every field.                                                 
      121 +- `usual` and `delta_pct` are `null` without enough history (`
          +delta_pct` also when `usual` is 0), never a division error.   
      122 +- `status` is `below`, `above`, `normal` or `not_enough_data`.
          + Locations are sorted below-usual first (largest              
      123 +  shortfall first), then by name.                             
      124 +- `history` holds the exact weekly counts `usual` is the media
          +n of, oldest first. The median is computed from this          
      125 +  list, so the explanation and the number cannot disagree.    
      126 +- Numbers are rounded to one decimal. Swagger UI documents eve
          +ry field.                                                     
      127  
      128  ## How the weekly comparison works
      129  
      144 -All rules live in [`backend/activity/services.py`](backend/act
          -ivity/services.py) and are independent of the API layer.      
      130 +All rules are in [`backend/activity/services.py`](backend/acti
          +vity/services.py).                                            
      131  
      146 -1. **Weeks** run Monday to Sunday in the account's own IANA ti
          -mezone (UTC timestamps become local dates first).             
      147 -   Weeks are calendar dates, not 168-hour blocks, so DST chang
          -es are safe. For 8 events in the seed the local week          
      148 -   differs from the UTC week.                                 
      149 -2. **Judged week:** the last complete week before the week con
          -taining `as_of`. A partial week is never judged or            
      150 -   used in a baseline.                                        
      132 +1. **Weeks** run Monday to Sunday in the account's own timezon
          +e. UTC timestamps become local dates first, and weeks         
      133 +   are calendar dates rather than 168-hour blocks, so DST is s
          +afe. For 8 seed events the local week differs from the UTC    
      134 +   week.                                                      
      135 +2. **Judged week:** the last complete week before the week con
          +taining `as_of`. A partial week is never judged or used       
      136 +   in a baseline.                                             
      137  3. **Counted value:** all events (calls + leads + appointments
           ) per location per week.
      138  4. **Usual week:** the median of up to the 8 weeks before the 
           judged week. A location's history starts the week after
      153 -   its first event (that week may be partial), and empty weeks
          - after that count as 0. Fewer than 4 history weeks gives      
      154 -   `not_enough_data`. A usual week of 0 with enough history is
          - valid: 0 events is `normal`, any event is `above`.           
      155 -5. **Status** (locations only). With `usual` as the expected c
          -ount, a Poisson tail test decides: `below` if                 
      156 -   P(X ≤ count) < 0.025, `above` if P(X ≥ count) < 0.025, othe
          -rwise `normal`. In words: the count would be this low         
      157 -   (or high) less than 2.5% of the time in a normal week. It i
          -s an indication of where to look, not a diagnosis.            
      158 -6. **Account headline:** this week against the median of the a
          -ccount's own weekly totals, with the percentage               
      159 -   change. It has no status. The same rule over-flags account 
          -totals, because locations of one account move together        
      160 -   (their weekly variance is up to 2.3 times the mean), so sho
          -wing the numbers is the honest choice.                        
      139 +   its first event, and empty weeks after that count as 0. Few
          +er than 4 history weeks gives `not_enough_data`. A usual      
      140 +   week of 0 with enough history is valid: 0 events is `normal
          +`, any event is `above`.                                      
      141 +5. **Status** (locations only): `below` if P(X ≤ count) < 0.02
          +5 under a Poisson distribution with mean `usual`, `above`     
      142 +   if P(X ≥ count) < 0.025, otherwise `normal`. That is, the c
          +ount would be this low (or high) less than 2.5% of the        
      143 +   time in a normal week. It points at where to look; it is no
          +t a diagnosis.                                                
      144 +6. **Account headline:** this week against the median of the a
          +ccount's own weekly totals, plus the percentage change,       
      145 +   with no status. The same test over-flags account totals bec
          +ause a customer's locations move together (weekly             
      146 +   variance up to 2.3 times the mean).                        
      147  
      148  `WINDOW_WEEKS = 8`, `MIN_HISTORY_WEEKS = 4` and `TAIL_PROBABIL
           ITY = 0.025` are constants at the top of the file.
      149 +`below` fires when the count is at most:                      
      150  
      164 -Resulting thresholds (`below` when the count is at most):     
      165 -                                                              
      151  | usual | 3.5 | 4.5 | 5.5 | 6.5 | 8 | 10 | 15 | 30 |
      152  |---|---|---|---|---|---|---|---|---|
      153  | flag if ≤ | none | 0 | 0 | 1 | 2 | 3 | 7 | 19 |
      154  
      170 -A location with a usual week below about 3.7 can never be flag
          -ged: one quiet week is not strong evidence at that            
      171 -volume.                                                       
      155 +A location with a usual week below about 3.7 can never be flag
          +ged: one quiet week is weak evidence at that volume.          
      156  
      173 -### Why a Poisson tail test                                   
      157 +**Why a Poisson tail test.** Weekly counts per location are sm
          +all (about 4 to 10) with variance close to the mean, the      
      158 +Poisson signature. A back-test over the 17 judged weeks from 2
          +026-03-30 to 2026-07-20 (1,173 location-weeks) counted        
      159 +the flags each rule raised:                                   
      160  
      175 -Weekly counts per location are small (about 4 to 10) and their
          - variance is roughly equal to their mean, which is the        
      176 -Poisson signature. A back-test over the 17 judged weeks from 2
          -026-03-30 to 2026-07-20 (69 locations, 1,173                  
      177 -location-weeks) compared rules:                               
      178 -                                                              
      179 -| Rule | Flags | Per week |                                   
      161 +| Rule | Flags observed | Per week |                          
      162  |---|---|---|
      163  | Poisson tail, 0.025 (used) | 22 (1.9%) | 1.3 (max 3) |
      164  | count ≤ 50% of usual (usual ≥ 3) | 126 (10.7%) | 7.4 |
      165  | count ≤ 60% of usual (usual ≥ 5) | 160 (13.6%) | 9.4 |
      166  
      185 -Simple percentage rules would hand a customer a long, mostly n
          -oise list every Monday. With the Poisson rule the             
      186 -default week gives 1 below, 1 above and 67 normal locations. T
          -here is no ground truth, so a flag is not                     
      187 -claimed to be a real problem; expect roughly one flag per Mond
          -ay across all 69 locations.                                   
      167 +Percentage rules would give a customer a much longer list ever
          +y Monday. At the default `as_of` the used rule gives 1        
      168 +below, 1 above and 67 normal locations. There is no ground tru
          +th, so these are flags the rule raised, not confirmed         
      169 +problems, false positives or misses.                          
      170  
      189 -### Why the median of 8 weeks                                 
      171 +**Why the median of 8 weeks.**                                
      172 +- *Median, not mean:* one extreme week must not become "normal
          +". After the Metro Collision spike a mean baseline would      
      173 +  flag most locations as below usual for weeks (see below).   
      174 +- *8 weeks* is about two months: long enough to absorb a few o
          +dd weeks (holiday, outage, campaign), short enough to         
      175 +  follow a location that really changed. The median stays stea
          +dy while fewer than 4 of the 8 weeks are inflated.            
      176 +- *At least 4 weeks:* with fewer, a median is mostly noise, so
          + the location shows "Not enough history".                     
      177  
      191 -- **Median, not mean:** one extreme week must not become "norm
          -al". See the Metro Collision spike below, where a             
      192 -  mean would have flagged most locations as below usual for th
          -e next seven weeks.                                           
      193 -- **8 weeks:** about two months. That is long enough to absorb
          - a few odd weeks (holiday, outage, campaign) and              
      194 -  short enough to follow a location that has genuinely changed
          -. The median stays honest as long as fewer than 4 of          
      195 -  the 8 weeks are inflated.                                   
      196 -- **At least 4 weeks:** with fewer, a median is mostly noise, 
          -so the location is marked "Not enough history" instead        
      197 -  of guessing.                                                
      178 +Both numbers are judgment calls: there is no labelled data to 
          +tune them against.                                            
      179  
      199 -Both numbers are judgment calls: there is no labelled data to 
          -tune them against. They are named constants.                  
      200 -                                                              
      180  ## The Metro Collision spike
      181  
      203 -On Wednesday 2026-06-03, Metro Collision Centers (account 6) r
          -ecorded 805 events in one day. A normal day for that          
      204 -account has a median of 10 (95th percentile 22, maximum 28). T
          -he week of June 1 shows 881 events against a usual            
      205 -66 (+1,234.8%) and all 15 locations "above usual". I inspected
          - the original data before deciding anything; the              
      206 -events were not modified.                                     
      182 +On Wednesday 2026-06-03, Metro Collision Centers (account 6) r
          +ecorded 805 events in one day, against a median day           
      183 +of 10 (95th percentile 22, maximum 28). The week of June 1 sho
          +ws 881 events against a usual 66 (+1,234.8%) with all 15      
      184 +locations "above usual". The original events were inspected an
          +d never modified.                                             
      185  
      186  **Evidence**
      209 -- All 805 events fall on one local day, spread across the whol
          -e business day, in all 15 locations (42 to 69 each).          
      210 -- They look like ordinary traffic at about 80 times the volume
          -: 60% calls, 26% leads and 14% appointments (rest of the      
      211 -  account: 61%, 23% and 16%); the same call outcomes and durat
          -ions. Statistical tests could not tell the mix from the       
      212 -  rest of the account (χ² 3.7 for event types on 2 degrees of 
          -freedom, 1.0 for call outcomes, 16.3 for locations on 14).    
      213 -- They are not a replay or a duplicate dump: 798 of the 805 ti
          -mestamps are distinct and the row ids are interleaved         
      214 -  with other accounts' events in time order.                  
      215 -- Nothing like it exists elsewhere: no other account has a day
          - above 28 events, and no other location-week is more          
      216 -  than 3 times that location's median.                        
      187 +- All 805 fall on one local day, across the business day and a
          +ll 15 locations (42 to 69 each).                              
      188 +- They look like ordinary traffic at about 80 times the volume
          +: 60% calls, 26% leads, 14% appointments (rest of the         
      189 +  account: 61%, 23%, 16%), with the same call outcomes and dur
          +ations. Tests could not tell the mix from the rest of         
      190 +  the account (χ² 3.7 for event types on 2 degrees of freedom,
          + 1.0 for call outcomes, 16.3 for locations on 14).            
      191 +- Not a replay: 798 of the 805 timestamps are distinct, and ro
          +w ids are interleaved with other accounts' events in time     
      192 +  order. Nothing similar exists elsewhere: no other account ha
          +s a day above 28 events, and no other location-week is        
      193 +  more than 3 times its median.                               
      194 +- **Unknown:** the cause. A real campaign, bot traffic, a test
          + fixture or a data feed problem look alike, because the       
      195 +  data has no source field.                                   
      196  
      218 -**What we do not know:** the cause. A real campaign, bot traff
          -ic, a test fixture or a data feed problem all look            
      219 -alike here, because the data has no source or campaign field. 
      197 +**Decision: keep the events and document the limitation.** Not
          +hing proves they are invalid, and removing them needs a       
      198 +threshold rule with its own product questions. Simulating thei
          +r exclusion on a copy of the database (dropping the day,      
      199 +or capping it to a normal day):                               
      200 +- The 15 "above usual" flags for that week disappear (14 in th
          +e capped run, where the 12 kept events leave one location     
      201 +  above). No "below usual" flag changes and no other account i
          +s affected.                                                   
      202 +- Later weeks barely move: the account's usual week stays betw
          +een 66 and 73.5 in every scenario. Deleting the day even      
      203 +  distorts later baselines, since it makes that week unusually
          + low.                                                         
      204 +- **The median protects later comparisons.** Over the seven co
          +mplete weeks after the spike, a mean baseline would flag 56   
      205 +  of 105 Metro Collision location-weeks as below usual (accoun
          +t usual about 170 instead of 66 to 73). The median flags 1.   
      206  
      221 -**Decision: keep the events and document the limitation.** Not
          -hing proves they are invalid, and removing them would         
      222 -need a threshold rule with its own product questions. I simula
          -ted excluding them on a copy of the database (never on        
      223 -the real data), by dropping the day and by capping it to a nor
          -mal day:                                                      
      224 -- The 15 "above usual" flags for that week disappear (14 in th
          -e capped run, where the 12 events kept happen to leave        
      225 -  one location above). No "below usual" flag changes in any sc
          -enario, and no other account is affected.                     
      226 -- Later weeks barely move: the account's usual week stays betw
          -een 66 and 73.5 in every scenario. Dropping the whole day     
      227 -  even distorts later baselines (it makes that week unusually 
          -low), which is a reason not to clean data by deleting.        
      228 -- The median is what protects later comparisons. Over the seve
          -n complete weeks after the spike, a mean baseline would       
      229 -  flag 56 of 105 Metro Collision location-weeks as below usual
          -, and the account's usual week would be about 170             
      230 -  instead of 66 to 73. The median flags 1.                    
      207 +The dashboard shows the exact percentage (+1,234.8%) and the w
          +eek is accurate: it was a very busy week. The expandable      
      208 +weekly history on each location gives the context, so there is
          + no extra wording. A sustained campaign covering 4 or more    
      209 +of the 8 weeks would move the median.                         
      210  
      232 -**Limits:** a sustained campaign covering 4 or more of the 8 w
          -eeks would move the median, and the dashboard still           
      233 -shows the large percentage (+1,234.8%) as computed. The week i
          -tself is accurate: it was a very busy week.                   
      234 -                                                              
      211  ## Frontend
      212  
      237 -- One page: account picker, week navigator (previous, next, La
          -test), the account's numbers, and a location table.           
      238 -- **URL state:** `?account=6&as_of=2026-07-27`, written with `
          -history.replaceState`. Invalid values fall back to            
      239 -  defaults. Week navigation sends `as_of` to the API (the Mond
          -ay after the shown week) and never goes past                  
      240 -  `latest_event_date`. Previous is disabled on an empty week, 
          -because nothing older exists.                                 
      241 -- **Popovers** (ⓘ) explain the usual week, the change and the 
          -statuses. They open on click, tap, Enter or Space, close      
      242 -  on Escape, outside click or when focus leaves, and are a bot
          -tom sheet on phones.                                          
      213 +- One page: account picker, week navigator (previous, next, La
          +test), the account's numbers and a location table.            
      214 +- **URL state:** `?account=6&as_of=2026-07-27` via `history.re
          +placeState`; invalid values fall back to defaults. Week       
      215 +  navigation sends `as_of` (the Monday after the shown week), 
          +never passes `latest_event_date`, and disables Previous       
      216 +  on an empty week because nothing older exists.              
      217 +- **Popovers** (ⓘ) explain the usual week, the change and the 
          +statuses. They open on click, tap, Enter or Space; close      
      218 +  on Escape, outside click or lost focus; and are a bottom she
          +et on phones.                                                 
      219  - **Expandable rows** show this week by event type and the wee
           kly counts behind the usual week, with the median.
      244 -- States: loading, errors with a retry, an account without eve
          -nts, and locations without enough history. An                 
      245 -  out-of-range `as_of` from a bookmark shows a plain-language 
          -message with a "Show latest week" button.                     
      246 -- Timezones are shown as friendly names ("Pacific Time"). Ligh
          -t and dark themes follow the operating system.                
      220 +- **Single-location accounts** also show the location table: t
          +he headline has no status, so the location row is the         
      221 +  only place a drop can be flagged.                           
      222 +- States: loading, errors with retry, accounts without events,
          + locations without enough history, and a plain-language       
      223 +  message with "Show latest week" for an out-of-range bookmark
          +ed date. Timezones read "Pacific Time", not the IANA name.    
      224 +  Light and dark themes follow the operating system.          
      225  
      226  ## Assumptions
      227  
      250 -- "Normal" means a location's own recent history, not an indus
          -try benchmark.                                                
      251 -- The page has no login in this exercise, so it has an account
          - picker and the API has no authentication.                    
      252 -- "Now" is the `as_of` parameter (default: the latest event), 
          -not the wall clock, because the data ends on 2026-07-27.      
      253 -- `latest_event_date` is the UTC date of the newest event in t
          -he whole database. It is also the newest allowed `as_of`.     
      254 -- Only below-usual is highlighted; above-usual is shown for co
          -ntext.                                                        
      255 -- A location appears once it has an event; a location with no 
          -events at all does not exist in the data.                     
      228 +- "Normal" is a location's own recent history, not an industry
          + benchmark.                                                   
      229 +- There is no login in this exercise: the page has an account 
          +picker and the API has no authentication.                     
      230 +- "Now" is `as_of` (default: the latest event), not the wall c
          +lock, because the data ends on 2026-07-27.                    
      231 +  `latest_event_date` is the UTC date of the newest event in t
          +he whole database and the newest allowed `as_of`.             
      232 +- Only below-usual is highlighted; above-usual is shown for co
          +ntext. A location exists once it has an event.                
      233  
      257 -## Limitations and risks                                      
      234 +## Limitations                                                
      235  
      259 -- **Statistics:** the Poisson rule assumes independent events,
          - a roughly steady weekly rate and variance near the           
      260 -  mean. Bursts and campaigns break independence (the median li
          -mits the damage). Trends and seasonality are not              
      261 -  modelled; a growing or shrinking location is compared with i
          -ts own recent past.                                           
      262 -- **Silent locations:** a location silent for most of the 8 we
          -eks gets a usual week of 0 and is never flagged.              
      263 -  Event data cannot tell a closed location from a broken one. 
      236 +- **Statistics:** Poisson assumes independent events, a steady
          + weekly rate and variance near the mean. Bursts and           
      237 +  campaigns break independence (the median limits the damage).
          + Trends and seasonality are not modelled.                     
      238 +- **Silent locations:** one silent for most of the 8 weeks get
          +s a usual week of 0 and is never flagged. Event data          
      239 +  cannot tell a closed location from a broken one.            
      240  - **Low volume:** locations with a usual week under about 3.7 
           cannot be flagged.
      265 -- **Noise:** about 1.3 flags per Monday across the 69 seed loc
          -ations is expected even when nothing is wrong.                
      266 -- **Unused fields:** `outcome` and `duration_seconds` are stor
          -ed and validated but not used by the metric or returned       
      267 -  by the API, which reports counts by event type only. Nulls (
          -3% of outcomes) are kept as null.                             
      268 -- **Large percentages:** very large changes (like +1,234.8%) a
          -re shown as computed, with no softer wording.                 
      269 -- **Not production-ready:** development settings, no authentic
          -ation, no deployment setup, SQLite only. Swagger UI           
      270 -  needs internet access. Tested in Chrome only (not Firefox or
          - Safari), and not with a screen reader.                       
      271 -- **Out of scope** per the ticket: alerting and notifications,
          - ML and forecasting.                                          
      241 +- **Flag volume:** the back-test observed about 1.3 flags per 
          +Monday across 69 locations. Without ground truth, how many    
      242 +  are real problems is unknown.                               
      243 +- **Unused fields:** `outcome` and `duration_seconds` are stor
          +ed and validated but not used by the metric or returned;      
      244 +  the API reports counts by event type.                       
      245 +- **Not production-ready:** development settings, no authentic
          +ation, no deployment setup, SQLite only. Tested in Chrome     
      246 +  only (not Firefox or Safari), and not with a screen reader. 
          +Out of scope per the ticket: alerting, ML and forecasting.    
      247  
      248  ## Where would an LLM fit?
      249  
      275 -- **Not in deciding what is normal.** That has to be determini
          -stic, auditable and testable. Counts are tiny, so a           
      276 -  statistical rule does the job with no cost, latency or run-t
          -o-run drift, and it can be back-tested, which is how          
      277 -  the rule was chosen and checked.                            
      250 +- **Not in deciding what is normal.** That must be determinist
          +ic, auditable and testable. Counts are tiny, so a statistical 
      251 +  rule works with no cost, latency or run-to-run drift, and it
          + can be back-tested, which is how it was chosen and checked.  
      252  - **A plausible addition, not built: a plain-language summary*
           * of an already-computed result ("3 locations are below
      279 -  usual; Site C had 2 events against a usual 8 to 9"). The mod
          -el would receive only the computed numbers, and a check       
      280 -  would confirm that every number in its text appears in its i
          -nput, with a fixed template as the fallback. Risks:           
      281 -  invented figures, customer data sent to a third party, cost 
          -and latency, non-determinism. It adds no correctness,         
      282 -  so it is out of scope.                                      
      253 +  usual; Site C had 2 events against a usual 8 to 9"). The mod
          +el would receive only the computed numbers, a check would     
      254 +  confirm every number in its text appears in the input, and a
          + fixed template would be the fallback. Risks: invented        
      255 +  figures, customer data sent to a third party, cost, latency,
          + non-determinism. It adds no correctness, so it is out of     
      256 +  scope.                                                      
      257  - **Rejected: explaining why** a location is low. The data has
            no cause signals, so a model could only guess.
      258  - **Where AI is used here:** an AI coding agent built, tested 
           and reviewed this code under supervision, following the
      259    rules in `CLAUDE.md`.
      260  
      261  ## Differences from PLAN.md
      262  
      289 -`PLAN.md` was written before implementation. These later decis
          -ions supersede it (each is recorded in                        
      290 -`ai-log/DECISIONS.md`):                                       
      263 +Later decisions that supersede the plan (each is in `ai-log/DE
          +CISIONS.md`):                                                 
      264  
      265  | PLAN.md | Implemented | Why |
      266  |---|---|---|
      294 -| Account headline has a status | Numbers only: this week, usu
          -al, change | The Poisson rule over-flagged account totals in t
          -he back-test |                                                
      295 -| Single-location accounts show the headline only | They also 
          -show the location table (**not yet confirmed**) | With no head
          -line status, a single location's drop would not be flagged any
          -where |                                                       
      296 -| `as_of` is any valid date | Dates later than the latest even
          -t are rejected with 400 | Empty weeks beyond the data read as 
          -a real drop |                                                 
      297 -| Response without extras | Adds `latest_event_date` and per-l
          -ocation `history`; Swagger UI and OpenAPI schema | Bound the w
          -eek navigation; explain `usual` |                             
      298 -| Date input and "No recent activity (usual: 0)" wording | Wee
          -k navigation; usual 0 shows as `0` with change `—` and "No usu
          -al activity to compare with" | Complete weeks make day selecti
          -on meaningless |                                              
      299 -| Null outcome reported as `unknown` | Not exposed: the API re
          -turns counts by type only | Outcomes do not feed the metric | 
      267 +| Account headline has a status | Numbers only: this week, usu
          +al, change | The Poisson test over-flagged account totals in t
          +he back-test |                                                
      268 +| Single-location accounts show the headline only | They also 
          +show the location table (confirmed) | Without a headline statu
          +s, nothing else would flag a single location's drop |         
      269 +| Any valid `as_of` | Dates after the latest event are rejecte
          +d with 400 | Empty weeks beyond the data read as a real drop |
      270 +| Response without extras | Adds `latest_event_date` and per-l
          +ocation `history`; Swagger UI and OpenAPI schema | Bound week 
          +navigation; explain `usual` |                                 
      271 +| Date input; "No recent activity (usual: 0)" | Week navigatio
          +n; a usual of 0 shows `0` with change `—` | Complete weeks mak
          +e choosing a day meaningless |                                
      272 +| Null outcome reported as `unknown` | Not exposed; counts by 
          +event type only | Outcomes do not feed the metric |           
      273  | "About 800 extra connected calls" on June 3 | 805 mixed even
           ts (calls, leads, appointments) | Corrected by the spike inves
           tigation |
      301 -| One frontend smoke test | 80 frontend tests, plus popovers a
          -nd expandable rows | Behaviour grew during review |           
      274 +| One frontend smoke test | Tests for URL state, navigation, p
          +opovers, rows and states | Behaviour grew during review |     
      275  
      276  ## AI-assisted development log
      277  
      305 -`ai-log/DECISIONS.md` lists every decision, correction and rej
          -ection by the user, with a link to the session where it       
      278 +`ai-log/DECISIONS.md` lists every decision, correction and rej
          +ection by the user, linked to the session where it            
      279  happened. `ai-log/sessions/` holds the full exported conversat
           ions. `CLAUDE.md` holds the working rules given to the
      307 -agent (autonomy, verification, git and logging rules).        
      280 +agent.                                                        

⏺ The three lint warnings are lists that follow a bold line without a blank
  line. I'll fix them and measure how much shorter the README became.

  Ran 2 shell commands (ctrl+o to expand)

⏺ That first pass only cut word count by about 11%, which isn't enough. I'll do
  a tougher second pass—removing duplicate explanations, trimming the spike and
  frontend sections, and merging the plan-differences rows. · summary

  Read 1 file (ctrl+o to expand)

⏺ Write(README.md)
  ⎿  Added 62 lines, removed 96 lines
      35  |---|---|
      36  | `/?account=12` | The default week: one location (Site C) belo
          w usual |
      37  | `/?account=6&as_of=2026-06-08` | The Metro Collision burst we
          ek ([see below](#the-metro-collision-spike)) |
      38 -| `/?account=6&as_of=2026-04-20` | Two locations below usual | 
      38  | `/?account=6&as_of=2026-02-16` | Every location has too littl
          e history |
      39  | `/?account=20` | An account with no events |
      40  
     ...
      58  npm run typecheck && npm test && npm run build
      59  ```
      60  
      62 -Backend tests cover the weekly rules (DST weeks, Phoenix and UT
         -C accounts, events whose week differs between UTC and          
      63 -local time, zero weeks, short histories, a burst not hiding an 
         -outage), the import (ids, duplicates, `--replace`,             
      64 -rollback), the API contract and a back-test on the real seed. F
         -rontend tests cover URL state, week navigation,                
      65 -popovers, expandable rows and the loading, error and empty stat
         -es.                                                            
      61 +Backend tests cover the weekly rules (DST, Phoenix and UTC acco
         +unts, UTC-versus-local weeks, zero weeks, short                
      62 +histories), the import, the API contract and a back-test on the
         + real seed. Frontend tests cover URL state, week               
      63 +navigation, popovers, expandable rows and the loading, error an
         +d empty states.                                                
      64  
      65  ## Architecture
      66  
      67  ```text
      70 -seed.sql ──import_seed──▶ SQLite ──ORM──▶ activity/services.py 
         -──▶ DRF views ──▶ /api/… ──▶ React page                        
      71 - schema.sql                               weekly rules, no HTTP
         -     serializers   (Vite proxy)                                
      72 -```                                                            
      73 -                                                               
      74 -```text                                                        
      68  backend/activity/models.py       Account, Location, ActivityEve
          nt (constraints, one index)
      69  backend/activity/services.py     the metric: weeks, baseline, s
          tatus. No request/response code
      70  backend/activity/serializers.py, views.py   API contract and Op
          enAPI annotations
      71  backend/activity/management/commands/import_seed.py
      79 -frontend/src/                    App (state, URL, fetching), We
         -ekNav, HeadlinePanel, LocationTable,                           
      80 -                                 LocationDetail, InfoPopover, E
         -mptyState, helpers                                             
      72 +frontend/src/                    App (state, URL, fetching) and
         + the components, plus small helpers                            
      73  ai-log/                          decisions and full AI session 
          exports
      74  ```
      75  
      76  `Location` is normalized out of the seed's `location` string: i
          t is the unit the feature reports on, and names like
      77  `Site A` are only unique within an account. `event_type` and `o
          utcome` stay as text with `TextChoices` and database
      86 -check constraints (an outcome must fit its event type; a durati
         -on only for calls). There is one index,                        
      87 -`(location, occurred_at)`. Duplicate-looking events are kept, s
         -o they have no unique constraint.                              
      78 +check constraints. There is one index, `(location, occurred_at)
         +`. Duplicate-looking events are kept, so they have no          
      79 +unique constraint.                                             
      80  
      81  ## API
      82  
     ...
       87  | `GET /api/accounts/` | `[{id, name, timezone}]`, sorted by n
           ame |
       88  | `GET /api/accounts/{id}/activity/?as_of=YYYY-MM-DD` | The we
           ekly comparison. `as_of` is optional |
       89  
       98 -`as_of` defaults to the latest event date. The judged week is 
          -the complete week before the week containing `as_of`,         
       99 -so any date in the following week selects it. Errors: `400 {"a
          -s_of": ["…"]}` for a malformed or blank date, one             
      100 -outside 2000-01-01..2100-12-31, or one later than `latest_even
          -t_date` (beyond the data, empty weeks would read as a         
      101 -real drop); `404 {"detail": "Account not found."}`.           
       90 +`as_of` defaults to the latest event date. The judged week is 
          +the complete week before the week containing `as_of`.         
       91 +Errors: `400 {"as_of": ["…"]}` for a malformed or blank date, 
          +one outside 2000-01-01..2100-12-31, or one later than         
       92 +`latest_event_date` (beyond the data, empty weeks would read a
          +s a real drop); `404 {"detail": "Account not found."}`.       
       93  
       94  ```json
       95  {
     ...
      108  }
      109  ```
      110  
      120 -- `headline` is numbers only: no status for the account as a w
          -hole (see below).                                             
      111 +- `headline` is numbers only, with no status for the account a
          +s a whole.                                                    
      112  - `usual` and `delta_pct` are `null` without enough history (`
           delta_pct` also when `usual` is 0), never a division error.
      113  - `status` is `below`, `above`, `normal` or `not_enough_data`.
            Locations are sorted below-usual first (largest
      114    shortfall first), then by name.
      124 -- `history` holds the exact weekly counts `usual` is the media
          -n of, oldest first. The median is computed from this          
      125 -  list, so the explanation and the number cannot disagree.    
      126 -- Numbers are rounded to one decimal. Swagger UI documents eve
          -ry field.                                                     
      115 +- `history` holds the exact weekly counts `usual` is the media
          +n of, oldest first; the median is computed from this list.    
      116  
      117  ## How the weekly comparison works
      118  
      119  All rules are in [`backend/activity/services.py`](backend/acti
           vity/services.py).
      120  
      132 -1. **Weeks** run Monday to Sunday in the account's own timezon
          -e. UTC timestamps become local dates first, and weeks         
      133 -   are calendar dates rather than 168-hour blocks, so DST is s
          -afe. For 8 seed events the local week differs from the UTC    
      134 -   week.                                                      
      135 -2. **Judged week:** the last complete week before the week con
          -taining `as_of`. A partial week is never judged or used       
      136 -   in a baseline.                                             
      137 -3. **Counted value:** all events (calls + leads + appointments
          -) per location per week.                                      
      138 -4. **Usual week:** the median of up to the 8 weeks before the 
          -judged week. A location's history starts the week after       
      121 +1. **Weeks** run Monday to Sunday in the account's own timezon
          +e. UTC timestamps become local dates, and weeks are           
      122 +   calendar dates rather than 168-hour blocks, so DST is safe.
          + The judged week is the last complete week before the         
      123 +   week containing `as_of`; a partial week is never judged or 
          +used in a baseline.                                           
      124 +2. **Counted value:** all events (calls + leads + appointments
          +) per location per week.                                      
      125 +3. **Usual week:** the median of up to the 8 weeks before the 
          +judged week. A location's history starts the week after       
      126     its first event, and empty weeks after that count as 0. Few
           er than 4 history weeks gives `not_enough_data`. A usual
      140 -   week of 0 with enough history is valid: 0 events is `normal
          -`, any event is `above`.                                      
      141 -5. **Status** (locations only): `below` if P(X ≤ count) < 0.02
          -5 under a Poisson distribution with mean `usual`, `above`     
      142 -   if P(X ≥ count) < 0.025, otherwise `normal`. That is, the c
          -ount would be this low (or high) less than 2.5% of the        
      127 +   of 0 with enough history is valid: 0 events is `normal`, an
          +y event is `above`.                                           
      128 +4. **Status** (locations only): `below` if P(X ≤ count) < 0.02
          +5 under a Poisson distribution with mean `usual`, `above`     
      129 +   if P(X ≥ count) < 0.025, otherwise `normal`. That is, a cou
          +nt this low (or high) would happen less than 2.5% of the      
      130     time in a normal week. It points at where to look; it is no
           t a diagnosis.
      144 -6. **Account headline:** this week against the median of the a
          -ccount's own weekly totals, plus the percentage change,       
      145 -   with no status. The same test over-flags account totals bec
          -ause a customer's locations move together (weekly             
      131 +5. **Account headline:** this week against the median of the a
          +ccount's own weekly totals, plus the percentage change,       
      132 +   with no status: the same test over-flags account totals bec
          +ause a customer's locations move together (weekly             
      133     variance up to 2.3 times the mean).
      134  
      135  `WINDOW_WEEKS = 8`, `MIN_HISTORY_WEEKS = 4` and `TAIL_PROBABIL
           ITY = 0.025` are constants at the top of the file.
     ...
      139  |---|---|---|---|---|---|---|---|---|
      140  | flag if ≤ | none | 0 | 0 | 1 | 2 | 3 | 7 | 19 |
      141  
      155 -A location with a usual week below about 3.7 can never be flag
          -ged: one quiet week is weak evidence at that volume.          
      156 -                                                              
      142  **Why a Poisson tail test.** Weekly counts per location are sm
           all (about 4 to 10) with variance close to the mean, the
      143  Poisson signature. A back-test over the 17 judged weeks from 2
           026-03-30 to 2026-07-20 (1,173 location-weeks) counted
      144  the flags each rule raised:
     ...
      149  | count ≤ 50% of usual (usual ≥ 3) | 126 (10.7%) | 7.4 |
      150  | count ≤ 60% of usual (usual ≥ 5) | 160 (13.6%) | 9.4 |
      151  
      167 -Percentage rules would give a customer a much longer list ever
          -y Monday. At the default `as_of` the used rule gives 1        
      168 -below, 1 above and 67 normal locations. There is no ground tru
          -th, so these are flags the rule raised, not confirmed         
      169 -problems, false positives or misses.                          
      152 +At the default `as_of` the used rule gives 1 below, 1 above an
          +d 67 normal locations. There is no ground truth, so these     
      153 +are flags the rule raised, not confirmed problems, false posit
          +ives or misses.                                               
      154  
      171 -**Why the median of 8 weeks.**                                
      155 +**Why the median of 8 weeks.** The median keeps one extreme we
          +ek from becoming "normal" (a mean would have flagged most     
      156 +Metro Collision locations as below usual for weeks, see below)
          +. Eight weeks is about two months: long enough to absorb a    
      157 +few odd weeks, short enough to follow a location that really c
          +hanged, and the median stays steady while fewer than 4        
      158 +of the 8 are inflated. A minimum of 4 weeks keeps a median fro
          +m being mostly noise. Both numbers are judgment calls;        
      159 +there is no labelled data to tune them against.               
      160  
      173 -- *Median, not mean:* one extreme week must not become "normal
          -". After the Metro Collision spike a mean baseline would      
      174 -  flag most locations as below usual for weeks (see below).   
      175 -- *8 weeks* is about two months: long enough to absorb a few o
          -dd weeks (holiday, outage, campaign), short enough to         
      176 -  follow a location that really changed. The median stays stea
          -dy while fewer than 4 of the 8 weeks are inflated.            
      177 -- *At least 4 weeks:* with fewer, a median is mostly noise, so
          - the location shows "Not enough history".                     
      178 -                                                              
      179 -Both numbers are judgment calls: there is no labelled data to 
          -tune them against.                                            
      180 -                                                              
      161  ## The Metro Collision spike
      162  
      163  On Wednesday 2026-06-03, Metro Collision Centers (account 6) r
           ecorded 805 events in one day, against a median day
     ...
      166  
      167  **Evidence**
      168  
      189 -- All 805 fall on one local day, across the business day and a
          -ll 15 locations (42 to 69 each).                              
      190 -- They look like ordinary traffic at about 80 times the volume
          -: 60% calls, 26% leads, 14% appointments (rest of the         
      191 -  account: 61%, 23%, 16%), with the same call outcomes and dur
          -ations. Tests could not tell the mix from the rest of         
      192 -  the account (χ² 3.7 for event types on 2 degrees of freedom,
          - 1.0 for call outcomes, 16.3 for locations on 14).            
      193 -- Not a replay: 798 of the 805 timestamps are distinct, and ro
          -w ids are interleaved with other accounts' events in time     
      194 -  order. Nothing similar exists elsewhere: no other account ha
          -s a day above 28 events, and no other location-week is        
      169 +- One local day, spread across the business day and all 15 loc
          +ations (42 to 69 each).                                       
      170 +- Ordinary traffic at about 80 times the volume: 60% calls, 26
          +% leads, 14% appointments (rest of the account: 61%, 23%,     
      171 +  16%), with the same call outcomes and durations. Tests could
          + not tell the mix from the rest of the account (χ² 3.7 for    
      172 +  event types on 2 degrees of freedom, 1.0 for call outcomes, 
          +16.3 for locations on 14).                                    
      173 +- Not a replay: 798 of 805 timestamps are distinct and row ids
          + are interleaved with other accounts' events in time          
      174 +  order. Nothing similar exists elsewhere: no other account ha
          +s a day above 28 events and no other location-week is         
      175    more than 3 times its median.
      196 -- **Unknown:** the cause. A real campaign, bot traffic, a test
          - fixture or a data feed problem look alike, because the       
      197 -  data has no source field.                                   
      176 +- **Unknown:** the cause. A real campaign, bot traffic, a test
          + fixture or a feed problem look alike, because the data       
      177 +  has no source field.                                        
      178  
      179  **Decision: keep the events and document the limitation.** Not
           hing proves they are invalid, and removing them needs a
      180  threshold rule with its own product questions. Simulating thei
           r exclusion on a copy of the database (dropping the day,
     ...
      182  
      183  - The 15 "above usual" flags for that week disappear (14 in th
           e capped run, where the 12 kept events leave one location
      184    above). No "below usual" flag changes and no other account i
           s affected.
      205 -- Later weeks barely move: the account's usual week stays betw
          -een 66 and 73.5 in every scenario. Deleting the day even      
      185 +- Later weeks barely move: the account's usual stays between 6
          +6 and 73.5 in every scenario. Deleting the day even           
      186    distorts later baselines, since it makes that week unusually
            low.
      187  - **The median protects later comparisons.** Over the seven co
           mplete weeks after the spike, a mean baseline would flag 56
      188    of 105 Metro Collision location-weeks as below usual (accoun
           t usual about 170 instead of 66 to 73). The median flags 1.
      189  
      210 -The dashboard shows the exact percentage (+1,234.8%) and the w
          -eek is accurate: it was a very busy week. The expandable      
      211 -weekly history on each location gives the context, so there is
          - no extra wording. A sustained campaign covering 4 or more    
      212 -of the 8 weeks would move the median.                         
      190 +The dashboard shows the exact percentage, and the expandable w
          +eekly history on each location gives the context. A           
      191 +sustained campaign covering 4 or more of the 8 weeks would mov
          +e the median.                                                 
      192  
      193  ## Frontend
      194  
      216 -- One page: account picker, week navigator (previous, next, La
          -test), the account's numbers and a location table.            
      217 -- **URL state:** `?account=6&as_of=2026-07-27` via `history.re
          -placeState`; invalid values fall back to defaults. Week       
      218 -  navigation sends `as_of` (the Monday after the shown week), 
          -never passes `latest_event_date`, and disables Previous       
      219 -  on an empty week because nothing older exists.              
      220 -- **Popovers** (ⓘ) explain the usual week, the change and the 
          -statuses. They open on click, tap, Enter or Space; close      
      221 -  on Escape, outside click or lost focus; and are a bottom she
          -et on phones.                                                 
      195 +- **URL state:** `?account=6&as_of=2026-07-27` via `history.re
          +placeState`; invalid values fall back to defaults.            
      196 +- **Week navigation** (previous, next, Latest) sends `as_of` (
          +the Monday after the shown week), never passes                
      197 +  `latest_event_date`, and disables Previous on an empty week 
          +because nothing older exists.                                 
      198 +- **Popovers** (ⓘ) explain the usual week, the change and the 
          +statuses. They open on click, tap, Enter or Space, close      
      199 +  on Escape, outside click or lost focus, and are a bottom she
          +et on phones.                                                 
      200  - **Expandable rows** show this week by event type and the wee
           kly counts behind the usual week, with the median.
      201  - **Single-location accounts** also show the location table: t
           he headline has no status, so the location row is the
      202    only place a drop can be flagged.
      225 -- States: loading, errors with retry, accounts without events,
          - locations without enough history, and a plain-language       
      226 -  message with "Show latest week" for an out-of-range bookmark
          -ed date. Timezones read "Pacific Time", not the IANA name.    
      227 -  Light and dark themes follow the operating system.          
      203 +- Loading, error (with retry), empty-account and not-enough-hi
          +story states. Light and dark themes follow the OS.            
      204  
      229 -## Assumptions                                                
      205 +## Assumptions and limitations                                
      206  
      231 -- "Normal" is a location's own recent history, not an industry
          - benchmark.                                                   
      232 -- There is no login in this exercise: the page has an account 
          -picker and the API has no authentication.                     
      233 -- "Now" is `as_of` (default: the latest event), not the wall c
          -lock, because the data ends on 2026-07-27.                    
      234 -  `latest_event_date` is the UTC date of the newest event in t
          -he whole database and the newest allowed `as_of`.             
      235 -- Only below-usual is highlighted; above-usual is shown for co
          -ntext. A location exists once it has an event.                
      236 -                                                              
      237 -## Limitations                                                
      238 -                                                              
      207 +- "Normal" is a location's own recent history, not an industry
          + benchmark. "Now" is `as_of` (default: the latest event),     
      208 +  not the wall clock, because the data ends on 2026-07-27. `la
          +test_event_date` is the UTC date of the newest event in       
      209 +  the whole database and the newest allowed `as_of`.          
      210 +- There is no login: the page has an account picker and the AP
          +I has no authentication.                                      
      211  - **Statistics:** Poisson assumes independent events, a steady
            weekly rate and variance near the mean. Bursts and
      212    campaigns break independence (the median limits the damage).
            Trends and seasonality are not modelled.
      241 -- **Silent locations:** one silent for most of the 8 weeks get
          -s a usual week of 0 and is never flagged. Event data          
      242 -  cannot tell a closed location from a broken one.            
      243 -- **Low volume:** locations with a usual week under about 3.7 
          -cannot be flagged.                                            
      213 +- **Silent locations:** one silent for most of the 8 weeks get
          +s a usual of 0 and is never flagged. Event data cannot tell   
      214 +  a closed location from a broken one. Locations with a usual 
          +under about 3.7 cannot be flagged at all.                     
      215  - **Flag volume:** the back-test observed about 1.3 flags per 
           Monday across 69 locations. Without ground truth, how many
      216    are real problems is unknown.
      246 -- **Unused fields:** `outcome` and `duration_seconds` are stor
          -ed and validated but not used by the metric or returned;      
      247 -  the API reports counts by event type.                       
      217 +- **Unused fields:** `outcome` and `duration_seconds` are stor
          +ed and validated but not used by the metric or returned.      
      218  - **Not production-ready:** development settings, no authentic
           ation, no deployment setup, SQLite only. Tested in Chrome
      249 -  only (not Firefox or Safari), and not with a screen reader. 
          -Out of scope per the ticket: alerting, ML and forecasting.    
      219 +  only, and not with a screen reader. Out of scope per the tic
          +ket: alerting, ML and forecasting.                            
      220  
      221  ## Where would an LLM fit?
      222  
      223  - **Not in deciding what is normal.** That must be determinist
           ic, auditable and testable. Counts are tiny, so a statistical
      224    rule works with no cost, latency or run-to-run drift, and it
            can be back-tested, which is how it was chosen and checked.
      225  - **A plausible addition, not built: a plain-language summary*
           * of an already-computed result ("3 locations are below
      256 -  usual; Site C had 2 events against a usual 8 to 9"). The mod
          -el would receive only the computed numbers, a check would     
      226 +  usual; Site C had 2 events against a usual 8 to 9"). The mod
          +el would see only the computed numbers, a check would         
      227    confirm every number in its text appears in the input, and a
            fixed template would be the fallback. Risks: invented
      228    figures, customer data sent to a third party, cost, latency,
            non-determinism. It adds no correctness, so it is out of
      229    scope.
      230  - **Rejected: explaining why** a location is low. The data has
            no cause signals, so a model could only guess.
      261 -- **Where AI is used here:** an AI coding agent built, tested 
          -and reviewed this code under supervision, following the       
      262 -  rules in `CLAUDE.md`.                                       
      231  
      232  ## Differences from PLAN.md
      233  
     ...
      235  
      236  | PLAN.md | Implemented | Why |
      237  |---|---|---|
      270 -| Account headline has a status | Numbers only: this week, usu
          -al, change | The Poisson test over-flagged account totals in t
          -he back-test |                                                
      271 -| Single-location accounts show the headline only | They also 
          -show the location table (confirmed) | Without a headline statu
          -s, nothing else would flag a single location's drop |         
      272 -| Any valid `as_of` | Dates after the latest event are rejecte
          -d with 400 | Empty weeks beyond the data read as a real drop |
      273 -| Response without extras | Adds `latest_event_date` and per-l
          -ocation `history`; Swagger UI and OpenAPI schema | Bound week 
          -navigation; explain `usual` |                                 
      274 -| Date input; "No recent activity (usual: 0)" | Week navigatio
          -n; a usual of 0 shows `0` with change `—` | Complete weeks mak
          -e choosing a day meaningless |                                
      275 -| Null outcome reported as `unknown` | Not exposed; counts by 
          -event type only | Outcomes do not feed the metric |           
      238 +| Account headline has a status | Numbers only | The Poisson t
          +est over-flagged account totals |                             
      239 +| Single-location accounts show the headline only | They also 
          +show the location table (confirmed) | Nothing else would flag 
          +a single location's drop |                                    
      240 +| Any valid `as_of`; date input | Dates after the latest event
          + are rejected (400); week navigation | Empty weeks beyond the 
          +data read as a real drop; complete weeks make choosing a day m
          +eaningless |                                                  
      241 +| Response without extras | Adds `latest_event_date`, per-loca
          +tion `history`, Swagger UI and OpenAPI schema | Bound navigati
          +on; explain `usual` |                                         
      242 +| Null outcome reported as `unknown`; usual 0 shown as "No rec
          +ent activity" | Outcomes not exposed; a usual of 0 shows `0` w
          +ith change `—` | Outcomes do not feed the metric |            
      243  | "About 800 extra connected calls" on June 3 | 805 mixed even
           ts (calls, leads, appointments) | Corrected by the spike inves
           tigation |
      277 -| One frontend smoke test | Tests for URL state, navigation, p
          -opovers, rows and states | Behaviour grew during review |     
      244  
      245  ## AI-assisted development log
      246  
      247  `ai-log/DECISIONS.md` lists every decision, correction and rej
           ection by the user, linked to the session where it
      282 -happened. `ai-log/sessions/` holds the full exported conversat
          -ions. `CLAUDE.md` holds the working rules given to the        
      283 -agent.                                                        
      248 +happened; `ai-log/sessions/` holds the full exported conversat
          +ions; `CLAUDE.md` holds the working rules given to the        
      249 +agent. An AI coding agent built, tested and reviewed this code
          + under that supervision.                                      

⏺ The README is now much shorter. Next the decision log: the three new decisions
  from this turn, plus a tidy of my earlier audit row, which still says the 08
  export doesn't exist.

  Ran 1 shell command (ctrl+o to expand)

⏺ The README is trimmed to 249 lines (2,373 words), down from 307/3,017. Now
  I'll verify decision-log references, README links/anchors, and run the
  README's own test commands against the repo. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ All references check out except the three new rows I just added, which point
  to the 09 export that won't exist until this session is exported—I'll note
  that in the summary. Next, I'll verify the README's check commands still run
  correctly against the repo. · summary

  Ran 1 shell command (ctrl+o to expand)

⏺ Everything passes and your database hash is unchanged. Committing the README
  and the log separately, then pushing.

  Ran 1 shell command (ctrl+o to expand)

⏺ The README is shorter, and the single-location and spike decisions are
  recorded and pushed in two documentation-only commits. One thing is not done:
  three log rows cite an export that doesn't exist yet. I didn't start another
  phase or submit anything.

  Commits on origin/main

  - 604ad23 docs: shorten README and describe back-test results as observed
    flags.
  - 44661a3 docs(ai-log): record README cleanup and single-location
    confirmation.

  README changes

  - Length: it went from 307 lines and 3,017 words to 249 lines and 2,373 words.
    About a fifth was cut, mostly duplicated explanations, a few table rows,
    and the plan-differences list, which is now six rows.
  - Kept: the setup steps, the technical decisions, the limitations, and the
    Metro Collision findings (evidence, the keep decision, and why the median
    protects later weeks).
  - Test counts removed: the README now lists the commands without numbers.
  - Back-test wording: the results are described as flags the rules raised, and
    the text says they are not confirmed problems, false positives or misses.
  - Spike: the exact +1,234.8% stays, the expandable history is named as the
    context, and there is no new wording or UI change.
  - Single-location accounts: the README says they show the location table
    (confirmed), in the Frontend section and the plan-differences table.

  Decision log

  I added three rows: the single-location confirmation (which closes the earlier
  "to be confirmed" row), the spike decision, and the README cleanup. I also
  updated my earlier audit row, which still said the 08 export didn't exist.

  Verification

  - 08 export: it is your commit b317e7c and is pushed. It contains the spike,
    week-navigation and M5 conversations, so the nine rows that cite it resolve.
  - All references: a script checked every row's reference. Of the nine files
    cited, eight exist and are tracked in git, every export is cited at least
    once, and all 42 rows have the right number of columns.
  - README links: both internal anchors and the one file link resolve.
  - README commands: run against the repo, the backend suite passes, spectacular
    --validate exits 0, and the frontend type-check, tests and build pass. This
    was not a fresh-clone run, because the setup steps are unchanged from the
    earlier clean-environment check. Your db.sqlite3 hash is unchanged.

  Still needs attention

  - One unresolved reference: the three rows from this turn cite
    sessions/2026-10-29-09-docs-cleanup.md, which does not exist yet. Those
    decisions came after the 08 export, so citing 08 would have been wrong.
    Please run /export to that exact name and commit it, and every reference
    will resolve. I can rerun the check afterwards.
  - README length: it is shorter but still long. Cutting the thresholds table or
    the plan-differences table would trim it further, at some cost in detail.
  - Remaining risks: these are unchanged from my last summary: Chrome only, no
    screen reader, development settings and no CI.