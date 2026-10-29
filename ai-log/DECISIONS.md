# Decisions and corrections

Curated record of user decisions, corrections and rejections. Full conversations are in `ai-log/sessions/`.

| Date | Type | Decision / correction | Why | Reference |
|------|------|-----------------------|-----|-----------|
| 2026-10-28 | Decision | Capture logs with manual `/export` into `ai-log/sessions/`; no hooks or scripts. | Reliable and low-maintenance; hooks are unverified in VS Code and add moving parts. | sessions/2026-10-28-01-harness-setup.md |
| 2026-10-28 | Decision | Work directly on `main`; log commits are separate from code commits. | Solo take-home; keeps history simple and logs reviewable on their own. | sessions/2026-10-28-01-harness-setup.md |
| 2026-10-28 | Correction | Do not change global settings (`cleanupPeriodDays` stays default). | Keep the harness scoped to this repository. | sessions/2026-10-28-01-harness-setup.md |
| 2026-10-28 | Correction | `docs/ASSESSMENT.md` is intentionally absent; removed it from the required reading. | Ticket and product background are enough; user supplies any extra requirements. | sessions/2026-10-28-01-harness-setup.md |
| 2026-10-28 | Correction | Rejected the plan for being too long; asked for a short `CLAUDE.md` that doesn't repeat global instructions and tests focused on key behavior and edge cases. | Avoid redundancy and over-testing. | sessions/2026-10-28-01-harness-setup.md |
| 2026-10-28 | Decision | Verify `/export` before building the harness; user ran it and accepted the output. | Logging is the core evidence mechanism, so it was checked first. | sessions/2026-10-28-01-harness-setup.md |
| 2026-10-28 | Decision | Do not start DASH-247 or `PLAN.md` until the harness is committed. | Harness first. | sessions/2026-10-28-01-harness-setup.md |
