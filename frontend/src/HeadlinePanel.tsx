import { formatCount, formatDelta, formatTimezone, formatUsual, formatWeekRange } from "./format";
import { InfoPopover } from "./InfoPopover";
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
          <dt>
            Usual week
            <InfoPopover label="About the usual week">
              <p>
                The median of the up to 8 complete weeks before this one, counting Monday to Sunday
                in the account's time zone. Each location uses its own history.
              </p>
              <p>Weeks without activity count as 0. At least 4 weeks of history are needed.</p>
            </InfoPopover>
          </dt>
          <dd className="stat-value">{formatUsual(headline.usual)}</dd>
          <dd className="stat-caption">
            {hasUsual ? "Median of the previous 8 weeks" : "Needs at least 4 weeks of history"}
          </dd>
        </div>
        <div className="stat">
          <dt>
            Change
            <InfoPopover label="About the change" align="end">
              <p>
                This week compared with the usual week: (this week − usual) ÷ usual. It shows a dash
                when there is no usual week, or when it is 0.
              </p>
            </InfoPopover>
          </dt>
          <dd className="stat-value">{formatDelta(headline.delta_pct)}</dd>
          <dd className="stat-caption">{changeCaption}</dd>
        </div>
      </dl>
    </section>
  );
}
