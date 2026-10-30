# AI-Assisted Development Reflection

## Tools and records

Claude Code with Claude Sonnet 5.5 (High effort) was the implementation agent, used for code authoring, test execution, data investigation, and implementation reviews. Significant product and technical decisions were reviewed and approved by the candidate. The original plan is in `PLAN.md`; actual Claude Code exchanges are preserved in `ai-log/sessions/`, and `ai-log/DECISIONS.md` records corrections, decisions, and rejected approaches.

This reflection highlights selected interventions rather than reconstructing prompts or presenting summaries as verbatim transcripts.

## Specific interventions

**Account-level statistical classification.** The initial plan applied Poisson-based statuses to both locations and account totals. Back-testing showed that aggregate account counts varied more than the model assumed. The candidate approved changing the account headline to a numeric comparison while retaining classifications for individual locations, where the rule was better supported by the data.

**Unusual activity in Metro Collision Centers.** The June 3, 2026 burst contained 805 events across 15 locations. Inspection found 798 distinct timestamps, which argued against a simple duplicate dump, but distinct seconds alone cannot rule out repeated ingestion or synthetic traffic. A campaign or coordinated operational event was plausible, not established. The candidate chose to preserve all original events and their exact percentage changes, and to expose historical weekly counts so readers can inspect the baseline. Questions to take to the Product Owner include whether a campaign, migration, or source-system incident occurred that day; whether unusually high volume needs a separate product treatment; and how to distinguish genuine inactivity from delayed or missing data.

**Week-based interaction.** A daily date picker implied daily precision even though the calculation always judges complete Monday–Sunday weeks. After review, the interface was changed to week navigation, and expandable location details were added to expose per-type counts and the historical weeks behind each median.

## What this demonstrated

Agent output accelerated implementation and verification but did not replace product judgment. The important interventions came from checking statistical assumptions, investigating surprising data before changing it, and aligning the UI with the actual semantics of the metric. The back-tests report observed flags, not confirmed incidents or false positives, because the dataset has no ground-truth labels.
