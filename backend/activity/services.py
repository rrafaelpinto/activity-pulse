"""Weekly activity comparison for one account (DASH-247).

For each location, and for the account as a whole, the judged week's event count is compared with a
baseline: the median of up to the 8 complete local weeks before it. Only locations get a status: a
count far below the baseline (Poisson lower tail) is flagged. The account headline is a numeric
comparison only, because account totals vary more than Poisson allows (locations of one account
move together), so the same rule would over-flag it. See PLAN.md section 3 for the rules and
ai-log/DECISIONS.md for this later change to the headline.

Independent of the API layer: callers pass an account and an optional as_of date.
"""

import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from django.db.models import Max

from activity.models import ActivityEvent, Location

WINDOW_WEEKS = 8
MIN_HISTORY_WEEKS = 4
TAIL_PROBABILITY = 0.025

BELOW = "below"
ABOVE = "above"
NORMAL = "normal"
NOT_ENOUGH_DATA = "not_enough_data"


@dataclass(frozen=True)
class Comparison:
    """The judged week's count next to its baseline. Used as-is for the account headline."""

    current: int
    usual: float | None  # None when there is not enough history

    @property
    def delta_pct(self):
        if not self.usual:
            return None
        return (self.current - self.usual) / self.usual * 100


@dataclass(frozen=True)
class Assessment(Comparison):
    """A location's comparison plus its status."""

    status: str


@dataclass(frozen=True)
class LocationActivity:
    location_id: int
    name: str
    assessment: Assessment
    calls: int
    leads: int
    appointments: int


@dataclass(frozen=True)
class AccountActivity:
    account_id: int
    as_of: date
    week_start: date  # Monday of the judged week, in the account's timezone
    week_end: date  # Sunday of the judged week
    headline: Comparison  # numbers only: no status, see the module docstring
    locations: list[LocationActivity]


def poisson_cdf(k, mean):
    """P(X <= k) for X ~ Poisson(mean), summed term by term (no factorial overflow)."""
    if k < 0:
        return 0.0
    term = math.exp(-mean)
    total = term
    for i in range(1, int(k) + 1):
        term *= mean / i
        total += term
    return min(total, 1.0)


def classify(usual, current):
    """Status of a count against a baseline that is known to be valid (history was sufficient)."""
    if usual == 0:
        return ABOVE if current > 0 else NORMAL
    if poisson_cdf(current, usual) < TAIL_PROBABILITY:
        return BELOW
    if 1 - poisson_cdf(current - 1, usual) < TAIL_PROBABILITY:  # P(X >= current)
        return ABOVE
    return NORMAL


def week_start(day):
    """Monday of the week containing a calendar date."""
    return day - timedelta(days=day.weekday())


def local_week_start(moment, zone):
    """Monday (a local calendar date) of the week containing a moment, in the given timezone."""
    return week_start(moment.astimezone(zone).date())


def compare(weekly_counts, first_week, judged_week):
    """Compare the judged week with the baseline built from earlier weeks (no status).

    weekly_counts maps a Monday to its event count; a missing week means zero events.
    A history starts the week after the first event week (that week may be partial), so weeks
    before then are not zeros. Needs MIN_HISTORY_WEEKS of history inside the window, otherwise
    usual is None.
    """
    current = weekly_counts.get(judged_week, 0)
    window = [judged_week - timedelta(weeks=n) for n in range(WINDOW_WEEKS, 0, -1)]
    history = [w for w in window if w > first_week]
    if len(history) < MIN_HISTORY_WEEKS:
        return Comparison(current, None)
    return Comparison(current, statistics.median(weekly_counts.get(w, 0) for w in history))


def assess(weekly_counts, first_week, judged_week):
    """A location's comparison plus its status (Poisson tails around the baseline)."""
    result = compare(weekly_counts, first_week, judged_week)
    if result.usual is None:
        return Assessment(result.current, None, NOT_ENOUGH_DATA)
    return Assessment(result.current, result.usual, classify(result.usual, result.current))


def latest_event_date():
    """UTC date of the latest event in the database, or None if there are no events."""
    latest = ActivityEvent.objects.aggregate(latest=Max("occurred_at"))["latest"]
    return latest.astimezone(timezone.utc).date() if latest else None


def default_as_of():
    """The latest event date; today if there are no events."""
    return latest_event_date() or date.today()


def activity_report(account, as_of=None):
    """Judge the last complete local week before the week containing as_of.

    Events from the judged week's end onwards are ignored, so a partial current week is never judged
    or used in a baseline.
    """
    as_of = as_of or default_as_of()
    zone = ZoneInfo(account.timezone)
    judged = week_start(as_of) - timedelta(weeks=1)
    judged_end = datetime.combine(judged + timedelta(weeks=1), time.min, tzinfo=zone)

    events = ActivityEvent.objects.filter(
        location__account=account, occurred_at__lt=judged_end
    ).values_list("location_id", "event_type", "occurred_at")

    weekly = defaultdict(Counter)  # location id -> {week: count}
    account_weekly = Counter()
    judged_types = defaultdict(Counter)  # location id -> {event_type: count} in the judged week
    for location_id, event_type, occurred_at in events:
        week = local_week_start(occurred_at, zone)
        weekly[location_id][week] += 1
        account_weekly[week] += 1
        if week == judged:
            judged_types[location_id][event_type] += 1

    names = dict(Location.objects.filter(id__in=weekly).values_list("id", "name"))
    locations = []
    for location_id, counts in weekly.items():
        types = judged_types[location_id]
        locations.append(
            LocationActivity(
                location_id=location_id,
                name=names[location_id],
                assessment=assess(counts, min(counts), judged),
                calls=types[ActivityEvent.EventType.CALL],
                leads=types[ActivityEvent.EventType.LEAD],
                appointments=types[ActivityEvent.EventType.APPOINTMENT],
            )
        )
    locations.sort(key=_attention_order)

    headline = (
        compare(account_weekly, min(account_weekly), judged) if account_weekly else Comparison(0, None)
    )
    return AccountActivity(
        account_id=account.id,
        as_of=as_of,
        week_start=judged,
        week_end=judged + timedelta(days=6),
        headline=headline,
        locations=locations,
    )


def _attention_order(item):
    """Below-usual first (largest shortfall first), then everything else by name."""
    a = item.assessment
    if a.status == BELOW:
        return (0, a.current - a.usual, item.name)
    return (1, 0, item.name)
