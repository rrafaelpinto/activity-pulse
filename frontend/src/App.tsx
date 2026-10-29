import { useEffect, useState } from "react";
import { ApiError, fetchAccounts, fetchActivity } from "./api";
import { formatDate } from "./format";
import { EmptyState } from "./EmptyState";
import { HeadlinePanel } from "./HeadlinePanel";
import { LocationTable } from "./LocationTable";
import { WeekNav } from "./WeekNav";
import type { Account, ActivityResponse } from "./types";
import { isValidDate, parseUrlState, writeUrlState } from "./urlState";

type Load<T> =
  | { state: "loading" }
  | { state: "error"; error: ApiError }
  | { state: "ready"; data: T };

/** The API's as_of messages are written for developers; the page says it in plain words. */
function friendlyError(error: ApiError): string {
  if (error.field !== "as_of") return error.message;
  const latest = error.message.match(/\((\d{4}-\d{2}-\d{2})\)/)?.[1];
  return latest && isValidDate(latest)
    ? `That date is after the latest available data (${formatDate(latest)}).`
    : "That date isn't available. Try another date.";
}

function toApiError(error: unknown): ApiError {
  return error instanceof ApiError ? error : new ApiError(0, "Something went wrong.");
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export default function App() {
  const [initial] = useState(() => parseUrlState(window.location.search));
  const [accounts, setAccounts] = useState<Load<Account[]>>({ state: "loading" });
  const [accountsAttempt, setAccountsAttempt] = useState(0);
  const [accountId, setAccountId] = useState<number | null>(initial.account);
  // What the user asked for; null means "latest available" and is resolved by the API.
  const [requestedAsOf, setRequestedAsOf] = useState<string | null>(initial.asOf);
  const [activity, setActivity] = useState<Load<ActivityResponse>>({ state: "loading" });
  const [activityAttempt, setActivityAttempt] = useState(0);
  const [maxDate, setMaxDate] = useState<string | null>(null);
  const [shownWeek, setShownWeek] = useState<ActivityResponse["week"] | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setAccounts({ state: "loading" });
    fetchAccounts(controller.signal)
      .then((list) => {
        setAccounts({ state: "ready", data: list });
        setAccountId((current) =>
          current !== null && list.some((a) => a.id === current) ? current : (list[0]?.id ?? null),
        );
      })
      .catch((error) => {
        if (!isAbort(error)) setAccounts({ state: "error", error: toApiError(error) });
      });
    return () => controller.abort();
  }, [accountsAttempt]);

  const accountsReady = accounts.state === "ready";
  useEffect(() => {
    if (!accountsReady || accountId === null) return;
    const controller = new AbortController();
    setActivity({ state: "loading" });
    fetchActivity(accountId, requestedAsOf, controller.signal)
      .then((data) => {
        setActivity({ state: "ready", data });
        setMaxDate(data.latest_event_date);
        setShownWeek(data.week);
      })
      .catch((error) => {
        if (!isAbort(error)) setActivity({ state: "error", error: toApiError(error) });
      });
    return () => controller.abort();
  }, [accountsReady, accountId, requestedAsOf, activityAttempt]);

  const resolvedAsOf = activity.state === "ready" ? activity.data.as_of : null;
  useEffect(() => {
    if (accountId === null) return;
    writeUrlState({ account: accountId, asOf: requestedAsOf ?? resolvedAsOf });
  }, [accountId, requestedAsOf, resolvedAsOf]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <svg className="logo" viewBox="0 0 28 28" width="28" height="28" aria-hidden="true">
            <rect width="28" height="28" rx="7" fill="currentColor" />
            <path d="M5 15h4l2.5-7 4 12 2.5-5H23" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="brand">Activity Pulse</span>
        </div>
      </header>

      <div className="page">
        <div className="page-heading">
          <h1>Weekly activity</h1>
          <p>How each location compares with its usual week.</p>
        </div>

        {accounts.state === "loading" && <p className="state-card" role="status">Loading accounts…</p>}
        {accounts.state === "error" && (
          <div className="alert" role="alert">
            <p>{accounts.error.message}</p>
            <button type="button" onClick={() => setAccountsAttempt((n) => n + 1)}>
              Try again
            </button>
          </div>
        )}
        {accountsReady && accounts.data.length === 0 && <p className="state-card">No accounts available.</p>}

        {accountsReady && accounts.data.length > 0 && (
          <>
            <form className="toolbar" onSubmit={(event) => event.preventDefault()}>
              <div className="field field-account">
                <label htmlFor="account">Account</label>
                <select
                  id="account"
                  value={accountId ?? ""}
                  onChange={(event) => setAccountId(Number(event.target.value))}
                >
                  {accounts.data.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name}
                    </option>
                  ))}
                </select>
              </div>
              <WeekNav
                week={shownWeek}
                data={activity.state === "ready" ? activity.data : null}
                onSelect={setRequestedAsOf}
              />
              {maxDate && <p className="data-note">Data through {formatDate(maxDate)}</p>}
            </form>

            <main aria-busy={activity.state === "loading"}>
              {activity.state === "loading" && (
                <p className="state-card" role="status">Loading weekly activity…</p>
              )}
              {activity.state === "error" && (
                <div className="alert" role="alert">
                  <p>{friendlyError(activity.error)}</p>
                  {activity.error.field === "as_of" ? (
                    <button type="button" onClick={() => setRequestedAsOf(null)}>
                      Show latest week
                    </button>
                  ) : (
                    <button type="button" onClick={() => setActivityAttempt((n) => n + 1)}>
                      Try again
                    </button>
                  )}
                </div>
              )}
              {activity.state === "ready" &&
                (activity.data.locations.length === 0 ? (
                  <EmptyState data={activity.data} />
                ) : (
                  <>
                    <HeadlinePanel data={activity.data} />
                    <LocationTable
                      key={`${activity.data.account.id}-${activity.data.week.start}`}
                      locations={activity.data.locations}
                    />
                  </>
                ))}
            </main>
          </>
        )}
      </div>
    </div>
  );
}
