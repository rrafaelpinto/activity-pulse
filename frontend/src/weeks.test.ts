import type { ActivityResponse } from "./types";
import { addDays, canGoNext, canGoPrevious, nextAsOf, previousAsOf } from "./weeks";

const week = { start: "2026-07-13", end: "2026-07-19" };

function data(overrides: Partial<ActivityResponse> = {}): ActivityResponse {
  return {
    account: { id: 1, name: "A", timezone: "UTC" },
    as_of: "2026-07-20",
    latest_event_date: "2026-07-27",
    week,
    headline: { this_week: 1, usual: 1, delta_pct: 0 },
    locations: [
      { id: 1, name: "S", this_week: 1, usual: 1, delta_pct: 0, status: "normal", calls: 1, leads: 0, appointments: 0, history: [] },
    ],
    ...overrides,
  };
}

describe("addDays", () => {
  it("crosses month, year and leap-day boundaries", () => {
    expect(addDays("2026-07-26", 8)).toBe("2026-08-03");
    expect(addDays("2026-12-28", 8)).toBe("2027-01-05");
    expect(addDays("2028-02-27", 3)).toBe("2028-03-01");
    expect(addDays("2026-03-01", -1)).toBe("2026-02-28");
  });
});

describe("week navigation dates", () => {
  it("shows the previous week with the Monday of the displayed week", () => {
    expect(previousAsOf(week)).toBe("2026-07-13"); // the API judges the week before it: Jul 6 - 12
  });

  it("shows the next week with the Monday two weeks after the displayed week's Monday", () => {
    expect(nextAsOf(week)).toBe("2026-07-27"); // the API judges Jul 20 - 26
  });

  it("allows the next week while its as_of is not after the latest event date", () => {
    expect(canGoNext(data({ latest_event_date: "2026-07-27" }))).toBe(true);
    expect(canGoNext(data({ latest_event_date: "2026-07-26" }))).toBe(false);
    expect(canGoNext(data({ week: { start: "2026-07-20", end: "2026-07-26" } }))).toBe(false); // latest week
  });

  it("cannot go forward without data", () => {
    expect(canGoNext(data({ latest_event_date: null }))).toBe(false);
  });

  it("cannot go back from an empty week, because nothing is older", () => {
    expect(canGoPrevious(data())).toBe(true);
    expect(canGoPrevious(data({ locations: [] }))).toBe(false);
  });
});
