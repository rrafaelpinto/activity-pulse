import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "./App";
import type { Account, ActivityResponse, LocationActivity } from "./types";

const ACCOUNTS: Account[] = [
  { id: 1, name: "Alpha Dental", timezone: "America/Chicago" },
  { id: 2, name: "Beta Roofing", timezone: "America/Phoenix" },
  { id: 3, name: "Gamma Spa", timezone: "UTC" },
];

function location(overrides: Partial<LocationActivity> = {}): LocationActivity {
  return {
    id: 1,
    name: "Site A",
    this_week: 8,
    usual: 8,
    delta_pct: 0,
    status: "normal",
    calls: 4,
    leads: 3,
    appointments: 1,
    ...overrides,
  };
}

function activity(overrides: Partial<ActivityResponse> = {}): ActivityResponse {
  return {
    account: ACCOUNTS[0],
    as_of: "2026-07-27",
    latest_event_date: "2026-07-27",
    week: { start: "2026-07-20", end: "2026-07-26" },
    headline: { this_week: 54, usual: 56, delta_pct: -3.6 },
    locations: [location()],
    ...overrides,
  };
}

type Handler = (url: string) => { status?: number; body: unknown } | Promise<{ status?: number; body: unknown }>;

/** Installs a fetch mock that honours AbortSignal like the real one. Returns the list of URLs requested. */
function mockApi(handler: Handler) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: { signal?: AbortSignal }) => {
      calls.push(url);
      return new Promise((resolve, reject) => {
        const abort = () => reject(new DOMException("Aborted", "AbortError"));
        if (init?.signal?.aborted) return abort();
        init?.signal?.addEventListener("abort", abort);
        Promise.resolve(handler(url)).then(({ status = 200, body }) =>
          resolve({ ok: status >= 200 && status < 300, status, json: async () => body }),
        );
      });
    }),
  );
  return calls;
}

function api(activityFor: (accountId: number, asOf: string | null) => { status?: number; body: unknown }) {
  return mockApi((url) => {
    if (url === "/api/accounts/") return { body: ACCOUNTS };
    const match = url.match(/^\/api\/accounts\/(\d+)\/activity\/(?:\?as_of=(.+))?$/);
    if (!match) throw new Error(`unexpected url ${url}`);
    return activityFor(Number(match[1]), match[2] ?? null);
  });
}

beforeEach(() => {
  window.history.replaceState(null, "", "/");
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("loading and default view", () => {
  it("loads the first account at the latest date and writes both to the URL", async () => {
    const calls = api(() => ({ body: activity() }));
    render(<App />);

    expect(screen.getByText("Loading accounts…")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: /Week of Jul 20 – Jul 26, 2026/ })).toBeInTheDocument();
    expect(calls).toEqual(["/api/accounts/", "/api/accounts/1/activity/"]);
    expect(screen.getByLabelText("Account")).toHaveValue("1");
    expect(screen.getByLabelText("As of")).toHaveValue("2026-07-27");
    expect(screen.getByText("Data through Jul 27, 2026")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Weekly activity" })).toBeInTheDocument();
    await waitFor(() => expect(window.location.search).toBe("?account=1&as_of=2026-07-27"));
  });

  it("shows the account headline as numbers only, without a status", async () => {
    api(() => ({ body: activity() }));
    render(<App />);

    const headline = await screen.findByRole("region", { name: /Week of/ });
    expect(within(headline).getByText("This week")).toBeInTheDocument();
    expect(within(headline).getByText("54")).toBeInTheDocument();
    expect(within(headline).getByText("Usual week")).toBeInTheDocument();
    expect(within(headline).getByText("56")).toBeInTheDocument();
    expect(within(headline).getByText("−3.6%")).toBeInTheDocument();
    expect(within(headline).queryByText(/below usual|above usual|normal|attention/i)).not.toBeInTheDocument();
  });

  it("shows a friendly timezone label instead of the IANA identifier", async () => {
    api(() => ({ body: activity() })); // account 1 is America/Chicago
    render(<App />);

    expect(await screen.findByText(/Monday to Sunday · Central Time/)).toBeInTheDocument();
    expect(screen.queryByText(/America\/Chicago/)).not.toBeInTheDocument();
  });
});

describe("locations needing attention", () => {
  const flagged = activity({
    locations: [
      location({ id: 2, name: "Site C", this_week: 2, usual: 8.5, delta_pct: -76.5, status: "below" }),
      location({ id: 1, name: "Site A" }),
      location({ id: 3, name: "Site B", this_week: 12, usual: 6, delta_pct: 100, status: "above" }),
    ],
  });

  it("marks a below-usual location and counts it in the summary", async () => {
    api(() => ({ body: flagged }));
    render(<App />);

    expect(await screen.findByText("1 location may need attention.")).toBeInTheDocument();
    const row = screen.getByRole("row", { name: /Site C/ });
    expect(row).toHaveAttribute("data-status", "below");
    expect(within(row).getByText("Below usual")).toBeInTheDocument();
    // The status chip and the summary line say it once each; there is no extra label in the row.
    expect(screen.queryByText("May need attention")).not.toBeInTheDocument();
    expect(within(row).getByText("2")).toBeInTheDocument();
    expect(within(row).getByText("8.5")).toBeInTheDocument();
    expect(within(row).getByText("−76.5%")).toBeInTheDocument();
  });

  it("does not highlight normal or above-usual locations", async () => {
    api(() => ({ body: flagged }));
    render(<App />);
    await screen.findByText("1 location may need attention.");

    expect(screen.getByRole("row", { name: /Site A/ })).toHaveAttribute("data-status", "normal");
    expect(screen.getByRole("row", { name: /Site B/ })).toHaveAttribute("data-status", "above");
    expect(within(screen.getByRole("row", { name: /Site B/ })).getByText("Above usual")).toBeInTheDocument();
    expect(screen.getAllByText(/may need attention/i)).toHaveLength(1); // only the summary line
  });

  it("keeps the order given by the API (below-usual first)", async () => {
    api(() => ({ body: flagged }));
    render(<App />);
    await screen.findByText("1 location may need attention.");

    const names = screen.getAllByRole("rowheader").map((cell) => cell.textContent);
    expect(names).toEqual(["Site C", "Site A", "Site B"]);
  });

  it("says so when nothing needs attention", async () => {
    api(() => ({ body: activity() }));
    render(<App />);
    expect(await screen.findByText("No location is below its usual activity.")).toBeInTheDocument();
  });

  it("pluralizes the summary", async () => {
    api(() => ({
      body: activity({
        locations: [
          location({ id: 1, name: "Site A", status: "below", this_week: 0, usual: 9, delta_pct: -100 }),
          location({ id: 2, name: "Site B", status: "below", this_week: 1, usual: 9, delta_pct: -88.9 }),
        ],
      }),
    }));
    render(<App />);
    expect(await screen.findByText("2 locations may need attention.")).toBeInTheDocument();
  });

  it("still shows the location status for a single-location account", async () => {
    api(() => ({
      body: activity({
        locations: [location({ name: "Only Site", status: "below", this_week: 1, usual: 9, delta_pct: -88.9 })],
      }),
    }));
    render(<App />);
    expect(await screen.findByText("1 location may need attention.")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /Only Site/ })).toHaveAttribute("data-status", "below");
  });
});

describe("insufficient history and empty accounts", () => {
  it("explains a location without enough history and shows no baseline", async () => {
    api(() => ({
      body: activity({
        locations: [
          location({ id: 1, name: "New Site", this_week: 4, usual: null, delta_pct: null, status: "not_enough_data" }),
        ],
      }),
    }));
    render(<App />);

    const row = await screen.findByRole("row", { name: /New Site/ });
    expect(within(row).getByText("Not enough history")).toBeInTheDocument();
    expect(within(row).getAllByText("—")).toHaveLength(2); // usual and change
    expect(screen.getByText(/1 location has too little history to compare\./)).toBeInTheDocument();
    expect(within(row).queryByText(/Below usual/)).not.toBeInTheDocument();
  });

  it("explains an account headline without enough history", async () => {
    api(() => ({ body: activity({ headline: { this_week: 5, usual: null, delta_pct: null } }) }));
    render(<App />);
    expect(await screen.findByText("Needs at least 4 weeks of history")).toBeInTheDocument();
    const headline = screen.getByRole("region", { name: /Week of/ });
    expect(within(headline).getByText("5")).toBeInTheDocument();
    expect(within(headline).getAllByText("\u2014")).toHaveLength(2); // usual and change
  });

  it("explains a zero usual without dividing by it", async () => {
    api(() => ({ body: activity({ headline: { this_week: 3, usual: 0, delta_pct: null } }) }));
    render(<App />);
    expect(await screen.findByText("No usual activity to compare with")).toBeInTheDocument();
  });

  it("shows an empty-state message for an account without activity", async () => {
    api(() =>
      ({
        body: activity({ headline: { this_week: 0, usual: null, delta_pct: null }, locations: [] }),
      }),
    );
    render(<App />);

    expect(await screen.findByRole("heading", { name: "No activity recorded yet" })).toBeInTheDocument();
    expect(
      screen.getByText(/Nothing has been recorded for Alpha Dental up to the week of Jul 20 – Jul 26, 2026\./),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Locations" })).not.toBeInTheDocument();
    expect(screen.queryByText("This week")).not.toBeInTheDocument();
  });

  it("handles an empty account list", async () => {
    mockApi(() => ({ body: [] }));
    render(<App />);
    expect(await screen.findByText("No accounts available.")).toBeInTheDocument();
  });
});

describe("URL state", () => {
  it("restores the account and date from the URL after a reload", async () => {
    window.history.replaceState(null, "", "/?account=2&as_of=2026-06-08");
    const calls = api((id) => ({ body: activity({ account: ACCOUNTS[id - 1], as_of: "2026-06-08" }) }));
    render(<App />);

    await screen.findByRole("heading", { name: /Week of/ });
    expect(calls).toContain("/api/accounts/2/activity/?as_of=2026-06-08");
    expect(calls).not.toContain("/api/accounts/1/activity/");
    expect(screen.getByLabelText("Account")).toHaveValue("2");
    expect(screen.getByLabelText("As of")).toHaveValue("2026-06-08");
    expect(window.location.search).toBe("?account=2&as_of=2026-06-08");
  });

  it("ignores invalid parameters and normalizes the URL", async () => {
    window.history.replaceState(null, "", "/?account=abc&as_of=nope");
    const calls = api(() => ({ body: activity() }));
    render(<App />);

    await screen.findByRole("heading", { name: /Week of/ });
    expect(calls).toEqual(["/api/accounts/", "/api/accounts/1/activity/"]);
    await waitFor(() => expect(window.location.search).toBe("?account=1&as_of=2026-07-27"));
  });

  it("falls back to the first account when the URL names an unknown one", async () => {
    window.history.replaceState(null, "", "/?account=999");
    const calls = api(() => ({ body: activity() }));
    render(<App />);

    await screen.findByRole("heading", { name: /Week of/ });
    expect(calls.at(-1)).toBe("/api/accounts/1/activity/");
    await waitFor(() => expect(window.location.search).toBe("?account=1&as_of=2026-07-27"));
  });

  it("updates the URL when the account changes and keeps the date", async () => {
    window.history.replaceState(null, "", "/?account=1&as_of=2026-06-08");
    const calls = api((id, asOf) => ({ body: activity({ account: ACCOUNTS[id - 1], as_of: asOf ?? "2026-07-27" }) }));
    render(<App />);
    await screen.findByRole("heading", { name: /Week of/ });

    await userEvent.selectOptions(screen.getByLabelText("Account"), "3");

    await waitFor(() => expect(calls.at(-1)).toBe("/api/accounts/3/activity/?as_of=2026-06-08"));
    await waitFor(() => expect(window.location.search).toBe("?account=3&as_of=2026-06-08"));
  });
});

describe("as-of date", () => {
  it("limits the date picker to the latest available date", async () => {
    api(() => ({ body: activity({ latest_event_date: "2026-07-27" }) }));
    render(<App />);
    await screen.findByRole("heading", { name: /Week of/ });
    expect(screen.getByLabelText("As of")).toHaveAttribute("max", "2026-07-27");
    expect(screen.getByLabelText("As of")).toHaveAttribute("min", "2000-01-01");
  });

  it("loads a historical week and updates the URL", async () => {
    const calls = api((_id, asOf) => ({
      body: asOf
        ? activity({ as_of: asOf, week: { start: "2026-06-01", end: "2026-06-07" } })
        : activity(),
    }));
    render(<App />);
    await screen.findByRole("heading", { name: /Week of Jul 20/ });

    fireEvent.change(screen.getByLabelText("As of"), { target: { value: "2026-06-08" } });

    expect(await screen.findByRole("heading", { name: /Week of Jun 1 – Jun 7, 2026/ })).toBeInTheDocument();
    expect(calls.at(-1)).toBe("/api/accounts/1/activity/?as_of=2026-06-08");
    await waitFor(() => expect(window.location.search).toBe("?account=1&as_of=2026-06-08"));
  });

  it("clamps a date typed past the maximum instead of requesting it", async () => {
    const calls = api(() => ({ body: activity() }));
    render(<App />);
    await screen.findByRole("heading", { name: /Week of/ });
    const before = calls.length;

    fireEvent.change(screen.getByLabelText("As of"), { target: { value: "2026-10-29" } });

    await waitFor(() => expect(screen.getByLabelText("As of")).toHaveValue("2026-07-27"));
    expect(calls.slice(before).some((url) => url.includes("2026-10-29"))).toBe(false);
  });

  it("ignores incomplete date input", async () => {
    const calls = api(() => ({ body: activity() }));
    render(<App />);
    await screen.findByRole("heading", { name: /Week of/ });
    const before = calls.length;

    fireEvent.change(screen.getByLabelText("As of"), { target: { value: "" } });

    expect(calls.length).toBe(before);
    expect(screen.getByLabelText("As of")).toHaveValue("2026-07-27");
  });

  it("returns to the latest date with the Latest button", async () => {
    window.history.replaceState(null, "", "/?account=1&as_of=2026-06-08");
    const calls = api((_id, asOf) => ({ body: activity({ as_of: asOf ?? "2026-07-27" }) }));
    render(<App />);
    await screen.findByRole("heading", { name: /Week of/ });
    const latest = screen.getByRole("button", { name: "Latest" });
    expect(latest).toBeEnabled();

    await userEvent.click(latest);

    await waitFor(() => expect(calls.at(-1)).toBe("/api/accounts/1/activity/"));
    await waitFor(() => expect(window.location.search).toBe("?account=1&as_of=2026-07-27"));
    await waitFor(() => expect(screen.getByRole("button", { name: "Latest" })).toBeDisabled());
  });

  it("offers the latest week when a bookmarked date is past the data", async () => {
    window.history.replaceState(null, "", "/?account=1&as_of=2026-10-29");
    const calls = api((_id, asOf) =>
      asOf
        ? {
            status: 400,
            body: { as_of: ["as_of cannot be later than the latest available event date (2026-07-27)."] },
          }
        : { body: activity() },
    );
    render(<App />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("That date is after the latest available data (Jul 27, 2026).");
    expect(alert).not.toHaveTextContent("as_of"); // no developer wording in the UI
    await userEvent.click(screen.getByRole("button", { name: "Show latest week" }));

    expect(await screen.findByRole("heading", { name: /Week of Jul 20/ })).toBeInTheDocument();
    expect(calls.at(-1)).toBe("/api/accounts/1/activity/");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("loading and errors", () => {
  it("shows a loading state while the weekly activity is fetched", async () => {
    let release: (value: { body: unknown }) => void = () => {};
    mockApi((url) =>
      url === "/api/accounts/" ? { body: ACCOUNTS } : new Promise((resolve) => (release = resolve)),
    );
    render(<App />);

    expect(await screen.findByText("Loading weekly activity…")).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveAttribute("aria-busy", "true");
    release({ body: activity() });
    expect(await screen.findByRole("heading", { name: /Week of/ })).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveAttribute("aria-busy", "false");
  });

  it("uses plain words for any other rejected date", async () => {
    api(() => ({ status: 400, body: { as_of: ["Date must be between 2000-01-01 and 2100-12-31."] } }));
    render(<App />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("That date isn't available. Try another date.");
    expect(screen.getByRole("button", { name: "Show latest week" })).toBeInTheDocument();
  });

  it("shows a server error and recovers with Try again", async () => {
    let fail = true;
    api(() => (fail ? { status: 500, body: {} } : { body: activity() }));
    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Request failed (500).");
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: /Week of/ })).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows the API's message for an unknown account", async () => {
    api(() => ({ status: 404, body: { detail: "Account not found." } }));
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Account not found.");
  });

  it("shows a friendly message when the API is unreachable and retries the account list", async () => {
    let reachable = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (!reachable) throw new TypeError("Failed to fetch");
        return { ok: true, status: 200, json: async () => (url === "/api/accounts/" ? ACCOUNTS : activity()) };
      }),
    );
    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not reach the server");
    reachable = true;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: /Week of/ })).toBeInTheDocument();
  });

  it("ignores a slow response for a previous selection", async () => {
    const releases: Record<number, (value: { body: unknown }) => void> = {};
    mockApi((url) => {
      if (url === "/api/accounts/") return { body: ACCOUNTS };
      const id = Number(url.match(/accounts\/(\d+)\//)![1]);
      return new Promise((resolve) => (releases[id] = resolve));
    });
    render(<App />);
    await waitFor(() => expect(releases[1]).toBeDefined());

    await userEvent.selectOptions(screen.getByLabelText("Account"), "2");
    await waitFor(() => expect(releases[2]).toBeDefined());
    releases[2]({ body: activity({ headline: { this_week: 222, usual: 200, delta_pct: 11 }, account: ACCOUNTS[1] }) });
    expect(await screen.findByText("222")).toBeInTheDocument();

    releases[1]({ body: activity({ headline: { this_week: 111, usual: 100, delta_pct: 11 } }) });
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.getByText("222")).toBeInTheDocument();
    expect(screen.queryByText("111")).not.toBeInTheDocument();
  });
});
