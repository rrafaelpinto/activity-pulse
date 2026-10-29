import { formatWeekRange } from "./format";
import type { ActivityResponse } from "./types";

export function EmptyState({ data }: { data: ActivityResponse }) {
  return (
    <section className="card empty-state" aria-labelledby="empty-title">
      <svg className="empty-icon" viewBox="0 0 48 48" width="48" height="48" aria-hidden="true">
        <rect x="6" y="10" width="36" height="32" rx="6" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <path d="M6 20h36M16 6v8M32 6v8" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        <path d="M14 33h5l3-6 4 10 3-4h5" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <h2 id="empty-title">No activity recorded yet</h2>
      <p>
        Nothing has been recorded for {data.account.name} up to the week of{" "}
        {formatWeekRange(data.week.start, data.week.end)}. Once calls, leads or appointments come in,
        you'll see how each location compares with its usual week.
      </p>
    </section>
  );
}
