const MINUS = "−";

function parseDay(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function formatDay(value: string, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat("en-US", { ...options, timeZone: "UTC" }).format(parseDay(value));
}

/** "Jul 20 – Jul 26, 2026" (years are shown on both ends only when they differ). */
export function formatWeekRange(start: string, end: string): string {
  const sameYear = start.slice(0, 4) === end.slice(0, 4);
  const first = formatDay(start, sameYear ? { month: "short", day: "numeric" } : { month: "short", day: "numeric", year: "numeric" });
  const last = formatDay(end, { month: "short", day: "numeric", year: "numeric" });
  return `${first} – ${last}`;
}

export function formatDate(value: string): string {
  return formatDay(value, { month: "short", day: "numeric", year: "numeric" });
}

/** "Jul 20" (no year; used where the week is already clear from context). */
export function formatShortDate(value: string): string {
  return formatDay(value, { month: "short", day: "numeric" });
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

/** Usual weeks are medians, so they are whole numbers or end in .5. */
export function formatUsual(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);
}

export function formatDelta(deltaPct: number | null): string {
  if (deltaPct === null) return "—";
  if (deltaPct === 0) return "0%";
  const body = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(Math.abs(deltaPct));
  return `${deltaPct > 0 ? "+" : MINUS}${body}%`;
}

/** "America/Los_Angeles" -> "Pacific Time". Falls back to the city name for unknown zones. */
export function formatTimezone(zone: string): string {
  if (zone === "UTC") return "UTC";
  try {
    const part = new Intl.DateTimeFormat("en-US", { timeZone: zone, timeZoneName: "longGeneric" })
      .formatToParts(new Date())
      .find((p) => p.type === "timeZoneName");
    if (part && !part.value.startsWith("GMT")) return part.value;
  } catch {
    // Unknown zone: use the fallback below.
  }
  return (zone.split("/").pop() ?? zone).replace(/_/g, " ");
}
