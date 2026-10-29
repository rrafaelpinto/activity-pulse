# Activity Pulse: DASH-247

Senior AI Engineer take-home. Optimize for judgment, verifiable results and traceable agent direction, not breadth.

## Context
- Read `docs/TICKET.md` and `docs/PRODUCT_BACKGROUND.md` before planning. Extra assessment requirements come from the user in conversation.
- `seed.sql` is 2.4 MB: never print it. Query it or use head/grep.
- Timestamps are UTC. Accounts have an IANA `timezone`; calendar logic must respect it.
- Out of scope: alerting/notifications, ML/forecasting.

## Language
Everything is English: code, comments, docs, commits, PRs, logs.

## Autonomy
- Decide routine implementation details yourself (naming, structure, small refactors, test layout).
- Discuss before material product or architectural choices: baseline definition, metric semantics, stack, data model, new dependencies, scope. Give a recommendation with trade-offs.
- Ticket ambiguities are product questions. State assumptions explicitly; don't resolve them silently.

## Verification
- Test important behavior and edge cases, not everything: timezones/DST, new or sparse locations, zero activity, single vs. multi-location.
- Show real command output before claiming something works.

## Git
- Work on `main`. One focused commit per logical change, clear imperative English message.
- Run verification before committing. Never commit failing or unreviewed work.
- Push to `origin` only after the user approves the increment.
- No AI co-author trailers or "Generated with" lines in commits or PRs.
- No force-push or history rewrites.

## AI log
- Append to `ai-log/DECISIONS.md` whenever the user decides, corrects or rejects something.
- At the end of a session or increment, remind the user to `/export` to `ai-log/sessions/YYYY-MM-DD-NN-<slug>.md`. Never edit exports except with marked `[REDACTED]`.
- Commit log updates separately from code, e.g. `docs(ai-log): ...`.
