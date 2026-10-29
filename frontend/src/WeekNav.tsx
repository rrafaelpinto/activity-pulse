import { formatWeekRange } from "./format";
import type { ActivityResponse } from "./types";
import { canGoNext, canGoPrevious, nextAsOf, previousAsOf } from "./weeks";

interface Props {
  /** The week on screen; null until the first response arrives. */
  week: ActivityResponse["week"] | null;
  /** The loaded response, or null while loading or after an error: navigation waits for it. */
  data: ActivityResponse | null;
  onSelect: (asOf: string | null) => void;
}

/** Previous / next week and a way back to the latest one. as_of stays the API's own parameter. */
export function WeekNav({ week, data, onSelect }: Props) {
  const atLatest = data !== null && !canGoNext(data);
  return (
    <div className="field week-field">
      <span className="field-label" id="week-label">Week</span>
      <div className="week-controls">
        <div className="week-nav" role="group" aria-labelledby="week-label">
          <button
            type="button"
            aria-label="Previous week"
            disabled={!data || !canGoPrevious(data)}
            onClick={() => data && onSelect(previousAsOf(data.week))}
          >
            <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
              <path d="M10 3 5 8l5 5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <span className="week-range" aria-live="polite">
            {week ? formatWeekRange(week.start, week.end) : "—"}
          </span>
          <button
            type="button"
            aria-label="Next week"
            disabled={!data || !canGoNext(data)}
            onClick={() => data && onSelect(nextAsOf(data.week))}
          >
            <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
              <path d="m6 3 5 5-5 5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
        <button type="button" className="latest" onClick={() => onSelect(null)} disabled={atLatest}>
          Latest
        </button>
      </div>
    </div>
  );
}
