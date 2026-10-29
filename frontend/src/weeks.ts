import type { ActivityResponse } from "./types";

/**
 * Week navigation on top of the API's as_of rule: the judged week is the complete week before the
 * week containing as_of. So a week is shown with any date of the week after it; Mondays are used.
 */

export function addDays(day: string, days: number): string {
  const [year, month, d] = day.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, d + days)).toISOString().slice(0, 10);
}

/** as_of that shows the week before the displayed one. */
export function previousAsOf(week: ActivityResponse["week"]): string {
  return week.start;
}

/** as_of that shows the week after the displayed one (it may be later than the data allows). */
export function nextAsOf(week: ActivityResponse["week"]): string {
  return addDays(week.end, 8);
}

/** Nothing exists before the first recorded activity, so an empty week is the oldest one to show. */
export function canGoPrevious(data: ActivityResponse): boolean {
  return data.locations.length > 0;
}

/** The API rejects an as_of past the latest event, so the newest week is the last one reachable. */
export function canGoNext(data: ActivityResponse): boolean {
  return data.latest_event_date !== null && nextAsOf(data.week) <= data.latest_event_date;
}
