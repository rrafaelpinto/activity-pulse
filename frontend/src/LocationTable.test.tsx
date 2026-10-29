import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocationTable } from "./LocationTable";
import type { LocationActivity } from "./types";

const HISTORY = [9, 8, 10, 7, 6, 9, 8, 11].map((count, i) => ({
  week_start: ["2026-05-25", "2026-06-01", "2026-06-08", "2026-06-15", "2026-06-22", "2026-06-29", "2026-07-06", "2026-07-13"][i],
  count,
}));

function location(overrides: Partial<LocationActivity> = {}): LocationActivity {
  return {
    id: 1,
    name: "Site C",
    this_week: 2,
    usual: 8.5,
    delta_pct: -76.5,
    status: "below",
    calls: 1,
    leads: 1,
    appointments: 0,
    history: HISTORY,
    ...overrides,
  };
}

const toggle = (name: string) => screen.getByRole("button", { name });

describe("expandable location rows", () => {
  it("starts collapsed, with the toggle announcing its state", () => {
    render(<LocationTable locations={[location()]} />);

    expect(toggle("Site C")).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText(/against a usual week/)).not.toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(2); // header + one location
  });

  it("explains the status with this week's numbers", async () => {
    render(<LocationTable locations={[location()]} />);

    await userEvent.click(toggle("Site C"));

    expect(toggle("Site C")).toHaveAttribute("aria-expanded", "true");
    expect(
      screen.getByText("2 events this week against a usual week of 8.5 (−76.5%). That is unusually low for this location."),
    ).toBeInTheDocument();
  });

  it("shows this week's activity by event type", async () => {
    render(<LocationTable locations={[location({ calls: 12, leads: 3, appointments: 1 })]} />);
    await userEvent.click(toggle("Site C"));

    const byType = screen.getByRole("region", { name: "Site C: this week by event type" });
    expect(within(byType).getByText("Calls").nextSibling).toHaveTextContent("12");
    expect(within(byType).getByText("Leads").nextSibling).toHaveTextContent("3");
    expect(within(byType).getByText("Appointments").nextSibling).toHaveTextContent("1");
  });

  it("lists the weekly counts the usual week is the median of, oldest first", async () => {
    render(<LocationTable locations={[location()]} />);
    await userEvent.click(toggle("Site C"));

    const weeks = screen.getByRole("region", { name: "Site C: weekly counts behind the usual week" });
    const items = within(weeks).getAllByRole("term").map((term) => [term.textContent, term.nextSibling?.textContent]);
    expect(items).toEqual([
      ["May 25", "9"], ["Jun 1", "8"], ["Jun 8", "10"], ["Jun 15", "7"],
      ["Jun 22", "6"], ["Jun 29", "9"], ["Jul 6", "8"], ["Jul 13", "11"],
    ]);
    expect(within(weeks).getByText(/Median of the last 8 weeks: 8\.5\. Weeks without activity count as 0\./)).toBeInTheDocument();
  });

  it("shows weeks with no activity as zero", async () => {
    const history = [{ week_start: "2026-06-29", count: 0 }, { week_start: "2026-07-06", count: 5 }, { week_start: "2026-07-13", count: 0 }, { week_start: "2026-06-22", count: 3 }];
    render(<LocationTable locations={[location({ history, usual: 1.5 })]} />);
    await userEvent.click(toggle("Site C"));
    expect(screen.getByText(/Median of 4 weeks: 1\.5/)).toBeInTheDocument();
    expect(screen.getAllByText("0")).not.toHaveLength(0);
  });

  it("collapses again and keeps other rows independent", async () => {
    render(<LocationTable locations={[location(), location({ id: 2, name: "Site D", this_week: 9, usual: 9, delta_pct: 0, status: "normal" })]} />);

    await userEvent.click(toggle("Site C"));
    await userEvent.click(toggle("Site D"));
    expect(screen.getAllByText(/events? this week against/)).toHaveLength(2);
    expect(screen.getByText(/9 events this week against a usual week of 9 \(0%\)\. That is within its normal range\./)).toBeInTheDocument();

    await userEvent.click(toggle("Site C"));
    expect(toggle("Site C")).toHaveAttribute("aria-expanded", "false");
    expect(screen.getAllByText(/events? this week against/)).toHaveLength(1);
  });

  it("opens with the keyboard", async () => {
    render(<LocationTable locations={[location()]} />);
    toggle("Site C").focus();

    await userEvent.keyboard("{Enter}");
    expect(toggle("Site C")).toHaveAttribute("aria-expanded", "true");
    await userEvent.keyboard(" ");
    expect(toggle("Site C")).toHaveAttribute("aria-expanded", "false");
  });

  it("connects the toggle to the detail row it opens", async () => {
    render(<LocationTable locations={[location()]} />);
    await userEvent.click(toggle("Site C"));
    const detail = document.getElementById(toggle("Site C").getAttribute("aria-controls")!);
    expect(detail).toHaveTextContent("this week against a usual week");
  });

  it("uses singular wording for a single event", async () => {
    render(<LocationTable locations={[location({ this_week: 1, usual: 0, delta_pct: null, status: "above" })]} />);
    await userEvent.click(toggle("Site C"));
    expect(screen.getByText(/^1 event this week against a usual week of 0\./)).toBeInTheDocument();
    expect(screen.queryByText(/\(—\)|\(0%\)/)).not.toBeInTheDocument();
  });

  it("explains a missing baseline instead of showing numbers that are not there", async () => {
    const history = [{ week_start: "2026-07-06", count: 4 }, { week_start: "2026-07-13", count: 6 }];
    render(<LocationTable locations={[location({ usual: null, delta_pct: null, status: "not_enough_data", history, this_week: 5 })]} />);
    await userEvent.click(toggle("Site C"));

    expect(
      screen.getByText(/5 events this week\. There is not enough history yet to work out a usual week: it needs at least 4 completed weeks and this location has 2\./),
    ).toBeInTheDocument();
    expect(screen.getByText(/Weeks before the location's first activity are not counted\./)).toBeInTheDocument();
    expect(screen.queryByText(/Median of/)).not.toBeInTheDocument();
  });

  it("says so when a location has no earlier weeks at all", async () => {
    render(<LocationTable locations={[location({ usual: null, delta_pct: null, status: "not_enough_data", history: [] })]} />);
    await userEvent.click(toggle("Site C"));
    expect(screen.getByText("No earlier weeks yet.")).toBeInTheDocument();
  });
});

describe("status help", () => {
  it("explains all four statuses in a popover next to the Locations title", async () => {
    render(<LocationTable locations={[location()]} />);

    await userEvent.click(screen.getByRole("button", { name: "About the location statuses" }));

    const help = screen.getByText(/Each location is compared with its own usual week\./).parentElement!;
    for (const label of ["Below usual", "Above usual", "Normal", "Not enough history"]) {
      expect(within(help).getByText(label)).toBeInTheDocument();
    }
    expect(within(help).getByText(/less than 2\.5% of the time/)).toBeInTheDocument();
  });
});
