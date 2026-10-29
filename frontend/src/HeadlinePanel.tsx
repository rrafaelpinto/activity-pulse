import { formatCount, formatDelta, formatUsual, formatWeekRange } from "./format";
import type { ActivityResponse } from "./types";

/** The account-wide numbers for the judged week. Numbers only: no status for the account. */
export function HeadlinePanel({ data }: { data: ActivityResponse }) {
  const { headline, week, account, locations } = data;
  const hasActivity = locations.length > 0;

  return (
    <section className="card headline" aria-labelledby="headline-title">
      <h2 id="headline-title">Week of {formatWeekRange(week.start, week.end)}</h2>
      <p className="muted">
        All locations, Monday to Sunday ({account.timezone})
      </p>

      {!hasActivity ? (
        <p className="empty">No activity recorded for this account up to this week.</p>
      ) : (
        <>
          <p className="big-number" aria-label={`${headline.this_week} events this week`}>
            {formatCount(headline.this_week)} <span>events this week</span>
          </p>
          {headline.usual === null ? (
            <p className="muted">
              Not enough history yet to show a usual week (at least 4 earlier weeks are needed).
            </p>
          ) : (
            <p className="comparison">
              Usual week: <strong>{formatUsual(headline.usual)}</strong>
              {headline.delta_pct !== null ? (
                <>
                  {" · "}
                  <strong>{formatDelta(headline.delta_pct)}</strong> vs usual
                </>
              ) : (
                <span className="muted"> (no usual activity to compare with)</span>
              )}
            </p>
          )}
        </>
      )}
    </section>
  );
}
