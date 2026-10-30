# AI-Assisted Development Reflection

## How I worked with Claude Code

I used Claude Code with Claude Sonnet 5.5 (High effort) as my main implementation tool. It helped me write code, run tests, investigate data, and review implementation results.

I worked in small milestones, reviewing the results before moving to the next step. I kept the original plan in `PLAN.md`, recorded important decisions in `ai-log/DECISIONS.md`, and saved the actual Claude Code sessions in `ai-log/sessions/`.

I wanted to use the agent to move faster, but not delegate every technical or product decision to it. Some of the most valuable parts of this exercise came from questioning the results and changing the original approach.

## Decisions that made a difference

### 1. Changing the account-level classification

Initially, the plan was to classify both individual locations and account totals using the same Poisson-based rule.

During validation, we found that account totals had more variation than the statistical model expected. Keeping the original approach could have produced misleading signals for customers.

I decided to keep the statistical classification at the location level and show only the numerical comparison for the account as a whole.

This was an important reminder that a solution can be mathematically correct but still not appropriate for the data being analyzed.

### 2. Investigating the Metro Collision spike

One of the most interesting findings was a spike of 805 events on June 3, 2026, affecting all 15 locations of Metro Collision Centers.

At first, I questioned whether these records were duplicated or whether something had gone wrong during data ingestion. The investigation showed that 798 events had distinct timestamps, with different seconds, and the events were distributed across locations and event types.

This made a simple duplicate import less likely, but it did not prove that all events represented real customer activity.

We considered a possible marketing campaign or another coordinated event, but there was not enough information to confirm the cause. I decided to keep the original data and avoid introducing arbitrary cleanup rules.

I would still discuss a few questions with the Product Owner:

- Was there a marketing campaign, migration, or unusual operational event on June 3?
- Should unusually high activity also be highlighted, or should the dashboard focus only on drops?
- How can we distinguish real inactivity from missing or delayed event ingestion?

The main lesson for me was not to change data just because the resulting numbers look unusual. First, I need evidence that something is actually wrong.

### 3. Improving the dashboard interaction

The first dashboard was functional, but it allowed users to choose any date, even though the comparison always used complete weeks.

After reviewing the interface, I realized that daily navigation was misleading. I replaced it with week navigation and added expandable location details showing the event breakdown and the historical counts used in the baseline.

I also decided to allow multiple locations to remain expanded, making it easier to compare their histories.

This improvement was not about adding more features. It was about making the existing calculations easier to understand and trust.

## What I Would Improve for a Production Project

For this take-home, I intentionally kept the Claude Code harness simple. The goal was to have clear instructions, a lightweight planning process, meaningful tests, and a reliable record of AI interactions, without spending too much time building tooling around a small project.

For a production project, I would invest more in the repository's engineering guidelines and automated checks.

I would extend `CLAUDE.md` with clearer conventions for project structure, separation of responsibilities, API contracts, database migrations, error handling, and testing. I would also define rules for avoiding unnecessary abstractions, keeping business logic outside views, and documenting significant architectural decisions.

I would introduce reusable agent skills for specific review tasks, such as:

- **Code and PR review:** check changes against repository conventions, architectural boundaries, API compatibility, and test expectations.
- **Database performance:** identify potential N+1 queries, inefficient ORM usage, missing indexes, and unnecessary database access.
- **Test quality:** review coverage of critical business rules and edge cases, identify weak assertions, and check coverage reports without treating a percentage as the only quality metric.
- **Security review:** check permissions, input validation, sensitive data handling, and common Django/DRF security risks.

These checks should complement CI and human review, not replace them. I would also avoid running every skill on every change. The checks should be selected based on the files changed and the risks involved.

The main lesson is that a good AI development harness should make the agent's work more consistent and easier to verify. But the harness itself must remain proportional to the project's size and complexity.

## What I learned

Claude Code was useful for implementing changes quickly, exploring alternatives, and running verification across the backend and frontend. It also helped investigate edge cases that would have taken more time to explore manually.

However, I found that passing tests was not enough to determine whether the product behavior was right. The account-level classification passed its technical checks, but the underlying statistical assumption was not appropriate for aggregated activity. The Metro Collision data was another case where an unusual result required investigation instead of an immediate fix.

I also learned the importance of giving the agent clear objectives while keeping room to review its proposed solutions. Working in small steps made it easier to identify problems, change direction, and avoid unnecessary complexity.

If I had more time, I would spend it validating the statistical assumptions against different activity patterns rather than adding more features.

For me, the main takeaway is that AI-assisted development works best when the agent handles implementation and verification, while I remain responsible for questioning assumptions, making product decisions, and deciding what is ready to deliver.
