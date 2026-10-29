import { formatCount, formatDelta, formatUsual } from "./format";
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

export function LocationTable({ locations }: { locations: LocationActivity[] }) {
  if (locations.length === 0) return null;
  const below = locations.some((l) => l.status === "below");

  return (
    <section className="card" aria-labelledby="locations-title">
      <h2 id="locations-title">Locations</h2>
      <p className={below ? "attention-summary needs-attention" : "attention-summary"} role="status">
        {summary(locations)}
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">Location</th>
              <th scope="col" className="num">This week</th>
              <th scope="col" className="num">Usual</th>
              <th scope="col" className="num hide-small">Change</th>
              <th scope="col">Status</th>
              <th scope="col" className="num hide-small" title="Calls received">Calls</th>
              <th scope="col" className="num hide-small" title="Leads created">Leads</th>
              <th scope="col" className="num hide-small" title="Appointments set">Appts</th>
            </tr>
          </thead>
          <tbody>
            {locations.map((location) => {
              const status = STATUS[location.status];
              return (
                <tr key={location.id} data-status={location.status}>
                  <th scope="row">{location.name}</th>
                  <td className="num">{formatCount(location.this_week)}</td>
                  <td className="num">{formatUsual(location.usual)}</td>
                  <td className="num hide-small">{formatDelta(location.delta_pct)}</td>
                  <td>
                    <span className={`badge badge-${location.status}`}>
                      {status.icon && <span aria-hidden="true">{status.icon} </span>}
                      {status.label}
                    </span>
                    {location.status === "below" && (
                      <span className="attention-note hide-small"> May need attention</span>
                    )}
                  </td>
                  <td className="num hide-small">{formatCount(location.calls)}</td>
                  <td className="num hide-small">{formatCount(location.leads)}</td>
                  <td className="num hide-small">{formatCount(location.appointments)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="muted footnote">
        Compared with each location's own median of the 8 weeks before. "Below usual" means this
        week is unusually low for that location. It shows where to look, not why.
      </p>
    </section>
  );
}
