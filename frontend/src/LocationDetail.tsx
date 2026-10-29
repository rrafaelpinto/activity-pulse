import { formatCount, formatDelta, formatShortDate, formatUsual } from "./format";
import type { LocationActivity, Status } from "./types";

const VERDICT: Record<Status, string> = {
  below: "That is unusually low for this location.",
  above: "That is unusually high for this location.",
  normal: "That is within its normal range.",
  not_enough_data: "",
};

const MIN_HISTORY_WEEKS = 4; // the API's rule; shown only to explain a missing baseline

function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

function Summary({ location }: { location: LocationActivity }) {
  const events = plural(location.this_week, "event");
  if (location.usual === null) {
    const weeks = location.history.length;
    return (
      <p className="detail-summary">
        {events} this week. There is not enough history yet to work out a usual week: it needs at
        least {MIN_HISTORY_WEEKS} completed weeks and this location has {weeks}.
      </p>
    );
  }
  const change = location.delta_pct === null ? "" : ` (${formatDelta(location.delta_pct)})`;
  return (
    <p className="detail-summary">
      {events} this week against a usual week of {formatUsual(location.usual)}
      {change}. {VERDICT[location.status]}
    </p>
  );
}

/** The numbers behind one location's status: this week by type, and the weeks "usual" comes from. */
export function LocationDetail({ location }: { location: LocationActivity }) {
  const { history } = location;
  return (
    <div className="detail">
      <Summary location={location} />
      <div className="detail-grid">
        <section aria-label={`${location.name}: this week by event type`}>
          <h3>This week by type</h3>
          <dl className="mini-stats">
            <div>
              <dt>Calls</dt>
              <dd>{formatCount(location.calls)}</dd>
            </div>
            <div>
              <dt>Leads</dt>
              <dd>{formatCount(location.leads)}</dd>
            </div>
            <div>
              <dt>Appointments</dt>
              <dd>{formatCount(location.appointments)}</dd>
            </div>
          </dl>
        </section>
        <section aria-label={`${location.name}: weekly counts behind the usual week`}>
          <h3>Weeks behind the usual</h3>
          {history.length === 0 ? (
            <p className="detail-note">No earlier weeks yet.</p>
          ) : (
            <>
              <dl className="mini-stats weeks">
                {history.map((week) => (
                  <div key={week.week_start}>
                    <dt>{formatShortDate(week.week_start)}</dt>
                    <dd>{formatCount(week.count)}</dd>
                  </div>
                ))}
              </dl>
              <p className="detail-note">
                {location.usual === null
                  ? `Weeks before the location's first activity are not counted.`
                  : `Median of ${history.length === 8 ? "the last 8 weeks" : plural(history.length, "week")}: ${formatUsual(location.usual)}. Weeks without activity count as 0.`}
              </p>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
