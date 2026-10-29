export type Status = "below" | "normal" | "above" | "not_enough_data";

export interface Account {
  id: number;
  name: string;
  timezone: string;
}

export interface Headline {
  this_week: number;
  usual: number | null;
  delta_pct: number | null;
}

export interface WeekCount {
  week_start: string;
  count: number;
}

export interface LocationActivity {
  id: number;
  name: string;
  this_week: number;
  usual: number | null;
  delta_pct: number | null;
  status: Status;
  calls: number;
  leads: number;
  appointments: number;
  /** The weekly counts the usual week is the median of, oldest first. */
  history: WeekCount[];
}

export interface ActivityResponse {
  account: Account;
  as_of: string;
  latest_event_date: string | null;
  week: { start: string; end: string };
  headline: Headline;
  locations: LocationActivity[];
}
