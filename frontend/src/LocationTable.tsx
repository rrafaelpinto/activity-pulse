import { Fragment, useState } from "react";
import { formatCount, formatDelta, formatUsual } from "./format";
import { InfoPopover } from "./InfoPopover";
import { LocationDetail } from "./LocationDetail";
import type { LocationActivity, Status } from "./types";

const STATUS: Record<Status, { icon: string; label: string }> = {
  below: { icon: "▼", label: "Below usual" },
  above: { icon: "▲", label: "Above usual" },
  normal: { icon: "", label: "Normal" },
  not_enough_data: { icon: "", label: "Not enough history" },
};

function summary(locations: LocationActivity[]): string {
  const below = locations.filter((l) => l.status === "below").length;
  const noHistory = locations.filter((l) => l.status === "not_enough_data").length;
  const parts = [
    below === 0
      ? "No location is below its usual activity."
      : `${below} ${below === 1 ? "location" : "locations"} may need attention.`,
  ];
  if (noHistory > 0) {
    parts.push(
      `${noHistory} ${noHistory === 1 ? "location has" : "locations have"} too little history to compare.`,
    );
  }
  return parts.join(" ");
}

const COLUMNS = 8;

function StatusHelp() {
  return (
    <InfoPopover label="About the location statuses">
      <p>Each location is compared with its own usual week.</p>
      <ul>
        <li><strong>Below usual</strong>: unusually low for that location. It may need attention.</li>
        <li><strong>Above usual</strong>: unusually high. Shown for context, not highlighted.</li>
        <li><strong>Normal</strong>: close enough to the usual week.</li>
        <li><strong>Not enough history</strong>: fewer than 4 completed weeks to compare with.</li>
      </ul>
      <p>
        "Unusually" means a count this extreme would happen less than 2.5% of the time in a normal
        week. It shows where to look, not why.
      </p>
    </InfoPopover>
  );
}

export function LocationTable({ locations }: { locations: LocationActivity[] }) {
  const [expanded, setExpanded] = useState<ReadonlySet<number>>(new Set());
  if (locations.length === 0) return null;
  const needsAttention = locations.some((l) => l.status === "below");

  function toggle(id: number) {
    setExpanded((current) => {
      const next = new Set(current);
      if (!next.delete(id)) next.add(id);
      return next;
    });
  }

  return (
    <section className="card" aria-labelledby="locations-title">
      <div className="card-header">
        <div className="title-with-info">
          <h2 id="locations-title">Locations</h2>
          <StatusHelp />
        </div>
        <p className={needsAttention ? "attention-summary has-attention" : "attention-summary"} role="status">
          {needsAttention && <span className="summary-dot" aria-hidden="true" />}
          {summary(locations)}
        </p>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">Location</th>
              <th scope="col" className="num">This week</th>
              <th scope="col" className="num">Usual</th>
              <th scope="col" className="num hide-small">Change</th>
              <th scope="col">Status</th>
              <th scope="col" className="num breakdown hide-small" title="Calls received">Calls</th>
              <th scope="col" className="num breakdown hide-small" title="Leads created">Leads</th>
              <th scope="col" className="num breakdown hide-small" title="Appointments set">Appts</th>
            </tr>
          </thead>
          <tbody>
            {locations.map((location) => {
              const status = STATUS[location.status];
              const isOpen = expanded.has(location.id);
              const detailId = `location-${location.id}-detail`;
              return (
                <Fragment key={location.id}>
                  <tr data-status={location.status} className={isOpen ? "is-open" : undefined}>
                    <th scope="row">
                      <button
                        type="button"
                        className="row-toggle"
                        aria-expanded={isOpen}
                        aria-controls={isOpen ? detailId : undefined}
                        onClick={() => toggle(location.id)}
                      >
                        <svg className="chevron" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
                          <path d="m6 3 5 5-5 5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        {location.name}
                      </button>
                    </th>
                    <td className="num value">{formatCount(location.this_week)}</td>
                    <td className="num">{formatUsual(location.usual)}</td>
                    <td className="num change hide-small">{formatDelta(location.delta_pct)}</td>
                    <td>
                      <span className={`status status-${location.status}`}>
                        {status.icon && <span className="status-icon" aria-hidden="true">{status.icon}</span>}
                        {status.label}
                      </span>
                    </td>
                    <td className="num breakdown hide-small">{formatCount(location.calls)}</td>
                    <td className="num breakdown hide-small">{formatCount(location.leads)}</td>
                    <td className="num breakdown hide-small">{formatCount(location.appointments)}</td>
                  </tr>
                  {isOpen && (
                    <tr id={detailId} className="detail-row">
                      <td colSpan={COLUMNS}>
                        <LocationDetail location={location} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="footnote">
        Each location is compared with its own median of the 8 weeks before. "Below usual" means this
        week is unusually low for that location. It shows where to look, not why.
      </p>
    </section>
  );
}
