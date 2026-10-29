import { buildSearch, isValidDate, parseUrlState, writeUrlState } from "./urlState";

describe("isValidDate", () => {
  it("accepts real calendar dates only", () => {
    expect(isValidDate("2026-07-27")).toBe(true);
    expect(isValidDate("2024-02-29")).toBe(true);
    expect(isValidDate("2026-02-29")).toBe(false);
    expect(isValidDate("2026-13-01")).toBe(false);
    expect(isValidDate("2026-7-27")).toBe(false);
    expect(isValidDate("20260727")).toBe(false);
    expect(isValidDate("")).toBe(false);
  });
});

describe("parseUrlState", () => {
  it("reads the account and as_of parameters", () => {
    expect(parseUrlState("?account=6&as_of=2026-06-08")).toEqual({ account: 6, asOf: "2026-06-08" });
  });

  it("falls back to null for missing or invalid values", () => {
    expect(parseUrlState("")).toEqual({ account: null, asOf: null });
    expect(parseUrlState("?account=abc&as_of=nope")).toEqual({ account: null, asOf: null });
    expect(parseUrlState("?account=0&as_of=2026-02-30")).toEqual({ account: null, asOf: null });
    expect(parseUrlState("?account=-3")).toEqual({ account: null, asOf: null });
    expect(parseUrlState("?account=1.5")).toEqual({ account: null, asOf: null });
    expect(parseUrlState("?account=99999999999999999999")).toEqual({ account: null, asOf: null });
  });

  it("keeps a valid value when the other one is invalid", () => {
    expect(parseUrlState("?account=6&as_of=bad")).toEqual({ account: 6, asOf: null });
    expect(parseUrlState("?account=x&as_of=2026-06-08")).toEqual({ account: null, asOf: "2026-06-08" });
  });
});

describe("buildSearch and writeUrlState", () => {
  it("round-trips", () => {
    const state = { account: 12, asOf: "2026-07-27" };
    expect(buildSearch(state)).toBe("?account=12&as_of=2026-07-27");
    expect(parseUrlState(buildSearch(state))).toEqual(state);
  });

  it("omits empty values", () => {
    expect(buildSearch({ account: null, asOf: null })).toBe("");
    expect(buildSearch({ account: 3, asOf: null })).toBe("?account=3");
  });

  it("replaces the URL without adding history entries", () => {
    window.history.replaceState(null, "", "/");
    const before = window.history.length;
    writeUrlState({ account: 4, asOf: "2026-05-04" });
    writeUrlState({ account: 5, asOf: "2026-05-11" });
    expect(window.location.search).toBe("?account=5&as_of=2026-05-11");
    expect(window.history.length).toBe(before);
  });
});
