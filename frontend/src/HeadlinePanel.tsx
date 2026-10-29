import { formatCount, formatDelta, formatTimezone, formatUsual, formatWeekRange } from "./format";
import type { ActivityResponse } from "./types";

/** The account-wide numbers for the judged week. Numbers only: no status for the account. */
export function HeadlinePanel({ data }: { data: ActivityResponse }) {
  const { headline, week, account } = data;
  const hasUsual = headline.usual !== null;

  let changeCaption = "";
  if (hasUsual) changeCaption = headline.delta_pct === null ? "No usual activity to compare with" : "Compared with the usual week";

  return (
    <section className="card summary" aria-labelledby="summary-title">
      <div className="card-header">
        <div>
          <p className="eyebrow">All locations</p>
          <h2 id="summary-title">Week of {formatWeekRange(week.start, week.end)}</h2>
        </div>
        <p className="meta">Monday to Sunday &middot; {formatTimezone(account.timezone)}</p>
      </div>

      <dl className="stats">
        <div className="stat stat-primary">
          <dt>This week</dt>
          <dd className="stat-value">{formatCount(headline.this_week)}</dd>
          <dd className="stat-caption">Calls, leads and appointments</dd>
        </div>
        <div className="stat">
          <dt>Usual week</dt>
          <dd className="stat-value">{formatUsual(headline.usual)}</dd>
          <dd className="stat-caption">
            {hasUsual ? "Median of the previous 8 weeks" : "Needs at least 4 weeks of history"}
          </dd>
        </div>
        <div className="stat">
          <dt>Change</dt>
          <dd className="stat-value">{formatDelta(headline.delta_pct)}</dd>
          <dd className="stat-caption">{changeCaption}</dd>
        </div>
      </dl>
    </section>
  );
}
