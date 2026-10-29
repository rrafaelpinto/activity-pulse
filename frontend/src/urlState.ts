export interface UrlState {
  account: number | null;
  /** YYYY-MM-DD, or null for "latest available". */
  asOf: string | null;
}

export function isValidDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return (
    date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day
  );
}

/** Reads ?account=6&as_of=2026-07-27. Anything invalid is dropped so defaults apply. */
export function parseUrlState(search: string): UrlState {
  const params = new URLSearchParams(search);
  const account = params.get("account");
  const asOf = params.get("as_of");
  return {
    account: account !== null && /^[1-9]\d{0,9}$/.test(account) ? Number(account) : null,
    asOf: asOf !== null && isValidDate(asOf) ? asOf : null,
  };
}

export function buildSearch(state: UrlState): string {
  const params = new URLSearchParams();
  if (state.account !== null) params.set("account", String(state.account));
  if (state.asOf !== null) params.set("as_of", state.asOf);
  const query = params.toString();
  return query ? `?${query}` : "";
}

/** Keeps the URL in step with the view without adding history entries. */
export function writeUrlState(state: UrlState): void {
  const target = `${window.location.pathname}${buildSearch(state)}${window.location.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (target !== current) window.history.replaceState(null, "", target);
}
