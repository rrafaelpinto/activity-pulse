import { formatCount, formatDate, formatDelta, formatUsual, formatWeekRange } from "./format";

describe("formatWeekRange", () => {
  it("shows the year once for a week inside one year", () => {
    expect(formatWeekRange("2026-07-20", "2026-07-26")).toBe("Jul 20 – Jul 26, 2026");
  });

  it("shows both years when the week spans New Year", () => {
    expect(formatWeekRange("2025-12-29", "2026-01-04")).toBe("Dec 29, 2025 – Jan 4, 2026");
  });

  it("does not shift the day for any local timezone", () => {
    expect(formatDate("2026-03-08")).toBe("Mar 8, 2026");
    expect(formatDate("2026-01-01")).toBe("Jan 1, 2026");
  });
});

describe("number formatting", () => {
  it("formats usual weeks", () => {
    expect(formatUsual(null)).toBe("—");
    expect(formatUsual(8.5)).toBe("8.5");
    expect(formatUsual(66)).toBe("66");
    expect(formatUsual(0)).toBe("0");
  });

  it("formats changes with a sign and a real minus", () => {
    expect(formatDelta(null)).toBe("—");
    expect(formatDelta(-76.5)).toBe("−76.5%");
    expect(formatDelta(1234.8)).toBe("+1,234.8%");
    expect(formatDelta(0)).toBe("0%");
  });

  it("groups thousands", () => {
    expect(formatCount(881)).toBe("881");
    expect(formatCount(12626)).toBe("12,626");
  });
});
