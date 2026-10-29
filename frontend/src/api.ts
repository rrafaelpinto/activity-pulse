import type { Account, ActivityResponse } from "./types";

export class ApiError extends Error {
  readonly status: number;
  /** Set when the server rejected the as_of query parameter. */
  readonly field?: "as_of";

  constructor(status: number, message: string, field?: "as_of") {
    super(message);
    this.status = status;
    this.field = field;
  }
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, { signal, headers: { Accept: "application/json" } });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "Could not reach the server. Is the API running?");
  }
  if (response.ok) return (await response.json()) as T;

  let body: { detail?: string; as_of?: string[] } = {};
  try {
    body = await response.json();
  } catch {
    // Not JSON: fall through to the generic message.
  }
  if (response.status === 400 && body.as_of?.length) {
    throw new ApiError(400, body.as_of[0], "as_of");
  }
  throw new ApiError(response.status, body.detail ?? `Request failed (${response.status}).`);
}

export function fetchAccounts(signal?: AbortSignal): Promise<Account[]> {
  return getJson<Account[]>("/api/accounts/", signal);
}

/** asOf null asks for the API default: the latest available date. */
export function fetchActivity(
  accountId: number,
  asOf: string | null,
  signal?: AbortSignal,
): Promise<ActivityResponse> {
  const query = asOf ? `?as_of=${encodeURIComponent(asOf)}` : "";
  return getJson<ActivityResponse>(`/api/accounts/${accountId}/activity/${query}`, signal);
}
