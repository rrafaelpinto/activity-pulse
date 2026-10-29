import math
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from io import StringIO
from zoneinfo import ZoneInfo

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from activity import services
from activity.models import Account, ActivityEvent, Location
from activity.tests.factories import EventFactory, add_account
from activity.services import ABOVE, BELOW, NORMAL, NOT_ENOUGH_DATA, assess, classify

UTC = timezone.utc
J = date(2026, 6, 8)  # a Monday, used as the judged week in the pure tests


def weeks_before(n):
    return J - timedelta(weeks=n)


class PoissonTests(SimpleTestCase):
    def test_cdf_matches_closed_forms(self):
        self.assertAlmostEqual(services.poisson_cdf(0, 4.5), math.exp(-4.5))
        self.assertAlmostEqual(services.poisson_cdf(2, 8), math.exp(-8) * (1 + 8 + 32))
        self.assertEqual(services.poisson_cdf(-1, 5), 0.0)
        self.assertAlmostEqual(services.poisson_cdf(200, 5), 1.0)

    def test_thresholds_match_the_plan_table(self):
        """PLAN.md section 3: the largest count flagged as below, per usual value."""
        expected = {3.5: None, 4.5: 0, 5.5: 0, 6.5: 1, 8: 2, 10: 3, 15: 7, 30: 19}
        for usual, largest_flagged in expected.items():
            flagged = [c for c in range(0, 80) if classify(usual, c) == BELOW]
            self.assertEqual(max(flagged, default=None), largest_flagged, f"usual={usual}")
            # Everything up to the threshold is flagged, nothing above it.
            self.assertEqual(flagged, list(range(0, (-1 if largest_flagged is None else largest_flagged) + 1)), f"usual={usual}")

    def test_a_zero_week_is_only_flaggable_from_a_usual_of_about_3_7(self):
        self.assertEqual(classify(3.5, 0), NORMAL)
        self.assertEqual(classify(3.7, 0), BELOW)

    def test_upper_tail_is_above(self):
        self.assertEqual(classify(3.5, 50), ABOVE)
        self.assertEqual(classify(8, 8), NORMAL)
        self.assertEqual(classify(8, 15), ABOVE)  # P(X >= 15 | 8) is about 0.02
        self.assertEqual(classify(8, 14), NORMAL)

    def test_zero_baseline_is_never_below(self):
        self.assertEqual(classify(0, 0), NORMAL)
        self.assertEqual(classify(0, 3), ABOVE)


class AssessTests(SimpleTestCase):
    def counts(self, **by_weeks_before):
        return {weeks_before(int(k[1:])): v for k, v in by_weeks_before.items()}

    def test_fewer_than_four_history_weeks_is_not_enough_data(self):
        # First event 4 weeks back: history weeks are J-3, J-2, J-1 only.
        result = assess(self.counts(w3=5, w2=5, w1=5), weeks_before(4), J)
        self.assertEqual(result.status, NOT_ENOUGH_DATA)
        self.assertIsNone(result.usual)
        self.assertIsNone(result.delta_pct)

    def test_exactly_four_history_weeks_is_enough(self):
        result = assess({**self.counts(w4=5, w3=5, w2=5, w1=5), J: 5}, weeks_before(5), J)
        self.assertEqual(result.usual, 5)
        self.assertEqual(result.status, NORMAL)

    def test_location_first_seen_in_the_judged_week_has_no_history(self):
        result = assess({J: 3}, J, J)
        self.assertEqual((result.current, result.status), (3, NOT_ENOUGH_DATA))

    def test_empty_weeks_after_first_event_count_as_zero(self):
        # Four active weeks and four silent weeks: median of [10,10,10,10,0,0,0,0] is 5.
        counts = self.counts(w4=10, w3=10, w2=10, w1=10)
        result = assess(counts, weeks_before(20), J)
        self.assertEqual(result.usual, 5)

    def test_weeks_before_the_first_event_are_not_zeros(self):
        # First event 6 weeks back: only J-5..J-1 are history, so J-8..J-6 must not drag the median down.
        counts = self.counts(w6=100, w5=10, w4=10, w3=10, w2=10, w1=10)
        result = assess(counts, weeks_before(6), J)
        self.assertEqual(result.usual, 10)

    def test_the_first_event_week_itself_is_excluded(self):
        counts = self.counts(w6=999, w5=10, w4=10, w3=10, w2=10, w1=10)
        self.assertEqual(assess(counts, weeks_before(6), J).usual, 10)

    def test_only_the_last_eight_weeks_count(self):
        counts = self.counts(w9=1000, w8=6, w7=6, w6=6, w5=6, w4=6, w3=6, w2=6, w1=6)
        self.assertEqual(assess(counts, weeks_before(30), J).usual, 6)

    def test_median_of_an_even_number_of_weeks_is_the_midpoint(self):
        counts = self.counts(w8=4, w7=4, w6=4, w5=4, w4=7, w3=7, w2=7, w1=7)
        self.assertEqual(assess(counts, weeks_before(30), J).usual, 5.5)

    def test_zero_baseline_with_enough_history_is_a_real_baseline(self):
        history = self.counts(w9=1)  # first event long ago, then silence
        quiet = assess(history, weeks_before(9), J)
        self.assertEqual((quiet.usual, quiet.status), (0, NORMAL))
        self.assertIsNone(quiet.delta_pct)  # no percentage against zero
        woke = assess({**history, J: 3}, weeks_before(9), J)
        self.assertEqual((woke.usual, woke.status), (0, ABOVE))

    def test_median_keeps_a_burst_week_from_hiding_an_outage(self):
        # Prior weeks include a 57-event burst; the median stays 4.5 and a zero week is still flagged.
        history = [4, 3, 7, 5, 57, 4, 5, 3]
        counts = {weeks_before(8 - i): n for i, n in enumerate(history)}
        result = assess(counts, weeks_before(20), J)
        self.assertEqual((result.usual, result.current, result.status), (4.5, 0, BELOW))

    def test_delta_pct(self):
        result = assess(self.counts(w4=10, w3=10, w2=10, w1=10, **{}), weeks_before(5), J)
        self.assertEqual(result.delta_pct, -100.0)  # current 0 vs usual 10


class CompareTests(SimpleTestCase):
    def test_compare_has_numbers_only_and_matches_assess(self):
        counts = {weeks_before(n): 6 for n in range(1, 9)}
        comparison = services.compare(counts, weeks_before(20), J)
        self.assertEqual((comparison.current, comparison.usual), (0, 6))
        self.assertFalse(hasattr(comparison, "status"))
        self.assertEqual(comparison.delta_pct, -100.0)
        assessed = assess(counts, weeks_before(20), J)
        self.assertEqual((assessed.current, assessed.usual, assessed.status), (0, 6, BELOW))

    def test_compare_without_enough_history(self):
        comparison = services.compare({J: 7}, weeks_before(2), J)
        self.assertEqual((comparison.current, comparison.usual), (7, None))


class HistoryWeeksTests(SimpleTestCase):
    def test_lists_the_eight_weeks_before_the_judged_week_oldest_first(self):
        counts = {weeks_before(n): n for n in range(1, 12)}
        history = services.history_weeks(counts, weeks_before(20), J)
        self.assertEqual([w.week_start for w in history], [weeks_before(n) for n in range(8, 0, -1)])
        self.assertEqual([w.count for w in history], [8, 7, 6, 5, 4, 3, 2, 1])

    def test_the_judged_week_is_not_part_of_its_own_history(self):
        history = services.history_weeks({J: 99, weeks_before(1): 4}, weeks_before(20), J)
        self.assertNotIn(J, [w.week_start for w in history])

    def test_empty_weeks_after_the_first_event_are_listed_as_zero(self):
        history = services.history_weeks({weeks_before(1): 5}, weeks_before(3), J)
        self.assertEqual([(w.week_start, w.count) for w in history], [
            (weeks_before(2), 0), (weeks_before(1), 5),
        ])

    def test_starts_the_week_after_the_first_event_week(self):
        history = services.history_weeks({weeks_before(4): 3}, weeks_before(4), J)
        self.assertEqual(history[0].week_start, weeks_before(3))

    def test_no_history_when_the_first_event_is_in_the_judged_week(self):
        self.assertEqual(services.history_weeks({J: 2}, J, J), [])

    def test_usual_is_the_median_of_exactly_these_counts(self):
        counts = {weeks_before(n): c for n, c in zip(range(1, 9), [6, 7, 2, 3, 5, 7, 8, 2])}
        history = services.history_weeks(counts, weeks_before(20), J)
        self.assertEqual(services.compare(counts, weeks_before(20), J).usual,
                         services.statistics.median(w.count for w in history))


class LocalWeekTests(SimpleTestCase):
    def week(self, iso_utc, tz):
        moment = datetime.fromisoformat(iso_utc).replace(tzinfo=UTC)
        return services.local_week_start(moment, ZoneInfo(tz))

    def test_sunday_night_local_is_still_the_old_week_although_utc_is_monday(self):
        # 2026-03-09 04:30 UTC is Sunday 23:30 in Chicago (CDT, UTC-5).
        self.assertEqual(self.week("2026-03-09T04:30:00", "America/Chicago"), date(2026, 3, 2))
        self.assertEqual(self.week("2026-03-09T04:30:00", "UTC"), date(2026, 3, 9))

    def test_week_boundary_before_dst_starts_uses_standard_time(self):
        # 2026-03-02 05:30 UTC is Sunday 23:30 in Chicago (CST, UTC-6).
        self.assertEqual(self.week("2026-03-02T05:30:00", "America/Chicago"), date(2026, 2, 23))
        self.assertEqual(self.week("2026-03-02T06:30:00", "America/Chicago"), date(2026, 3, 2))

    def test_the_dst_week_has_events_on_both_sides_of_the_jump(self):
        # DST starts Sunday 2026-03-08 at 02:00 local: 07:59 UTC is 01:59 CST, 08:00 UTC is 03:00 CDT.
        for iso in ("2026-03-08T07:59:00", "2026-03-08T08:00:00", "2026-03-07T12:00:00"):
            self.assertEqual(self.week(iso, "America/Chicago"), date(2026, 3, 2), iso)
        self.assertEqual(self.week("2026-03-09T05:00:00", "America/Chicago"), date(2026, 3, 9))  # Mon 00:00 CDT

    def test_fall_back_boundary(self):
        # DST ends Sunday 2026-11-01. Monday 00:00 CST is 06:00 UTC.
        self.assertEqual(self.week("2026-11-02T05:59:59", "America/Chicago"), date(2026, 10, 26))
        self.assertEqual(self.week("2026-11-02T06:00:00", "America/Chicago"), date(2026, 11, 2))

    def test_phoenix_has_no_dst(self):
        # Phoenix is UTC-7 all year: Monday 00:00 is 07:00 UTC in winter and summer.
        for monday, prev in ((date(2026, 2, 9), date(2026, 2, 2)), (date(2026, 7, 6), date(2026, 6, 29))):
            at = datetime.combine(monday, datetime.min.time(), tzinfo=UTC) + timedelta(hours=7)
            zone = ZoneInfo("America/Phoenix")
            self.assertEqual(services.local_week_start(at, zone), monday)
            self.assertEqual(services.local_week_start(at - timedelta(seconds=1), zone), prev)


class ReportTests(TestCase):
    """activity_report on small hand-built data."""

    FIRST = date(2026, 3, 2)  # Monday

    def setUp(self):
        self.account = add_account(1)

    def location(self, name="Site A", account=None):
        return Location.objects.create(account=account or self.account, name=name)

    def test_judged_week_is_the_complete_week_before_as_of(self):
        loc = self.location()
        EventFactory.weekly(loc, [5] * 10, self.FIRST)  # weeks of 03-02 .. 05-04
        for as_of in (date(2026, 5, 11), date(2026, 5, 13), date(2026, 5, 17)):  # Mon, Wed, Sun
            report = services.activity_report(self.account, as_of)
            self.assertEqual((report.week_start, report.week_end), (date(2026, 5, 4), date(2026, 5, 10)))

    def test_events_in_the_as_of_week_and_later_are_ignored(self):
        loc = self.location()
        EventFactory.weekly(loc, [5] * 8, self.FIRST)  # through week of 04-20
        EventFactory.weekly(loc, [50, 50], date(2026, 4, 27))  # judged week 04-27, then the as_of week
        report = services.activity_report(self.account, date(2026, 5, 4))
        self.assertEqual(report.locations[0].assessment.current, 50)
        self.assertEqual(report.headline.current, 50)  # the 05-04 week (50 more) is not counted

    def test_local_week_boundary_decides_which_week_an_event_counts_in(self):
        loc = self.location()
        EventFactory.weekly(loc, [5] * 5, self.FIRST)  # 03-02 .. 03-30
        # Sunday 23:30 Chicago time on 2026-03-08 is 04:30 UTC on Monday 03-09: still the 03-02 week.
        EventFactory.add(loc, datetime(2026, 3, 9, 4, 30, tzinfo=UTC))
        report = services.activity_report(self.account, date(2026, 3, 9))  # judged week: 03-02
        self.assertEqual(report.locations[0].assessment.current, 6)

    def test_account_timezone_is_used_not_utc(self):
        phoenix = add_account(2, "America/Phoenix")
        utc = add_account(3, "UTC")
        moment = datetime(2026, 3, 9, 6, 30, tzinfo=UTC)  # Sun 23:30 in Phoenix (UTC-7); Monday in UTC
        for account in (phoenix, utc):
            EventFactory.add(self.location(account=account), moment)
        self.assertEqual(services.activity_report(phoenix, date(2026, 3, 9)).headline.current, 1)
        self.assertEqual(services.activity_report(utc, date(2026, 3, 9)).headline.current, 0)

    def test_zero_weeks_after_first_event_count_and_trigger_below(self):
        loc = self.location()
        EventFactory.weekly(loc, [10] * 8, self.FIRST)  # 8 steady weeks, then nothing
        report = services.activity_report(self.account, date(2026, 5, 4))  # judged 04-27: zero events
        a = report.locations[0].assessment
        self.assertEqual((a.current, a.usual, a.status), (0, 10, BELOW))

    def test_new_location_is_not_enough_data(self):
        loc = self.location()
        EventFactory.weekly(loc, [8] * 3, self.FIRST)  # first week + 2 history weeks only
        report = services.activity_report(self.account, date(2026, 3, 23))  # judged 03-16
        self.assertEqual(report.locations[0].assessment.status, NOT_ENOUGH_DATA)

    def test_location_first_seen_after_the_judged_week_is_not_listed(self):
        EventFactory.weekly(self.location("Old"), [5] * 6, self.FIRST)
        EventFactory.add(self.location("New"), datetime(2026, 4, 22, 12, tzinfo=UTC))
        report = services.activity_report(self.account, date(2026, 4, 13))  # judged 04-06
        self.assertEqual([loc.name for loc in report.locations], ["Old"])

    def test_location_history_matches_the_baseline_and_keeps_zero_weeks(self):
        loc = self.location()
        EventFactory.weekly(loc, [4, 6, 0, 8, 2, 5, 7, 3, 9], self.FIRST)  # weeks 03-02 .. 04-27
        report = services.activity_report(self.account, date(2026, 5, 4))  # judged 04-27
        item = report.locations[0]
        self.assertEqual(
            [(w.week_start.isoformat(), w.count) for w in item.history],
            [("2026-03-09", 6), ("2026-03-16", 0), ("2026-03-23", 8), ("2026-03-30", 2),
             ("2026-04-06", 5), ("2026-04-13", 7), ("2026-04-20", 3)],
        )
        self.assertEqual(item.assessment.usual, services.statistics.median(w.count for w in item.history))

    def test_location_without_enough_history_still_lists_its_weeks(self):
        loc = self.location()
        EventFactory.weekly(loc, [8] * 3, self.FIRST)
        item = services.activity_report(self.account, date(2026, 3, 23)).locations[0]  # judged 03-16
        self.assertEqual([w.week_start for w in item.history], [date(2026, 3, 9)])
        self.assertIsNone(item.assessment.usual)

    def test_history_is_per_account_week_in_the_account_timezone(self):
        tokyo = add_account(2, "Asia/Tokyo")
        loc = Location.objects.create(account=tokyo, name="Site T")
        # Sunday 23:30 UTC is already Monday 08:30 in Tokyo: it belongs to the next local week.
        EventFactory.add(loc, datetime(2026, 3, 8, 23, 30, tzinfo=UTC))
        EventFactory.weekly(loc, [3] * 6, date(2026, 3, 16))
        item = services.activity_report(tokyo, date(2026, 4, 20)).locations[0]  # judged 04-13
        self.assertEqual(item.history[0].week_start, date(2026, 3, 16))  # first event week is 03-09 (local)

    def test_per_type_counts_for_the_judged_week(self):
        loc = self.location()
        EventFactory.weekly(loc, [1] * 2, self.FIRST)
        monday = date(2026, 3, 16)
        EventFactory.weekly(loc, [2], monday, "call_received")
        EventFactory.weekly(loc, [3], monday, "lead_created")
        EventFactory.weekly(loc, [1], monday, "appointment_set")
        result = services.activity_report(self.account, date(2026, 3, 23)).locations[0]
        self.assertEqual((result.calls, result.leads, result.appointments), (2, 3, 1))
        self.assertEqual(result.assessment.current, 6)

    def test_headline_uses_account_weekly_totals_not_location_medians(self):
        a, b = self.location("A"), self.location("B")
        # Week 0 (03-02) is the first event week; weeks 1-8 are the history; week 9 (05-04) is judged.
        EventFactory.weekly(a, [1, 0, 0, 0, 0, 9, 9, 9, 9, 5], self.FIRST)
        EventFactory.weekly(b, [1, 9, 9, 0, 0, 0, 0, 0, 0, 5], self.FIRST)
        report = services.activity_report(self.account, date(2026, 5, 11))
        medians = {loc.name: loc.assessment.usual for loc in report.locations}
        self.assertEqual(medians, {"A": 4.5, "B": 0})
        # Account weekly totals over the history are [9,9,0,0,9,9,9,9]: median 9, not 4.5 + 0.
        self.assertEqual(report.headline.usual, 9)
        self.assertEqual(report.headline.current, 10)

    def test_headline_without_enough_history_has_no_baseline(self):
        EventFactory.weekly(self.location(), [5] * 3, self.FIRST)  # first week + 2 history weeks
        headline = services.activity_report(self.account, date(2026, 3, 23)).headline
        self.assertEqual((headline.current, headline.usual), (5, None))
        self.assertIsNone(headline.delta_pct)

    def test_headline_carries_numbers_only(self):
        EventFactory.weekly(self.location(), [10] * 9 + [4], self.FIRST)  # judged week far below usual
        report = services.activity_report(self.account, date(2026, 5, 11))
        self.assertFalse(hasattr(report.headline, "status"))
        self.assertEqual((report.headline.current, report.headline.usual), (4, 10))
        self.assertAlmostEqual(report.headline.delta_pct, -60.0)
        self.assertEqual(report.locations[0].assessment.status, NORMAL)  # P(X <= 4 | 10) = 0.029

    def test_account_without_events_has_an_empty_report(self):
        empty = add_account(9, name="Quiet")
        report = services.activity_report(empty, date(2026, 7, 27))
        self.assertEqual(report.locations, [])
        self.assertEqual((report.headline.current, report.headline.usual), (0, None))
        self.assertIsNone(report.headline.delta_pct)

    def test_locations_sort_below_first_by_largest_shortfall_then_by_name(self):
        specs = {"Z low": (10, 3), "A normal": (10, 10), "M lower": (10, 0), "B above": (10, 30)}
        for name, (usual, judged) in specs.items():
            EventFactory.weekly(self.location(name), [usual] * 9 + [judged], self.FIRST)
        report = services.activity_report(self.account, date(2026, 5, 11))  # judged: 05-04
        self.assertEqual(
            [(loc.name, loc.assessment.status) for loc in report.locations],
            [("M lower", BELOW), ("Z low", BELOW), ("A normal", NORMAL), ("B above", ABOVE)],
        )

    def test_default_as_of_is_the_utc_date_of_the_latest_event(self):
        loc = self.location()
        EventFactory.add(loc, datetime(2026, 7, 27, 22, 20, tzinfo=UTC))
        self.assertEqual(services.default_as_of(), date(2026, 7, 27))
        self.assertEqual(services.activity_report(self.account).as_of, date(2026, 7, 27))


class SeedBackTestTests(TestCase):
    """PLAN.md section 3 numbers, reproduced on the real seed data.

    The expected values were computed by a separate reference implementation (SQLite + zoneinfo, ISO
    weeks, lgamma-based Poisson) and agree with the service on every account, location and week.
    """

    JUDGED_WEEKS = [date(2026, 3, 30) + timedelta(weeks=i) for i in range(17)]  # 03-30 .. 07-20

    @classmethod
    def setUpTestData(cls):
        call_command("import_seed", stdout=StringIO())
        cls.accounts = list(Account.objects.order_by("id"))
        cls.reports = {
            (week, account.id): services.activity_report(account, week + timedelta(weeks=1))
            for week in cls.JUDGED_WEEKS
            for account in cls.accounts
        }

    def location_rows(self):
        for (week, account_id), report in self.reports.items():
            for loc in report.locations:
                yield week, account_id, loc

    def find(self, account_id, name, week):
        for loc in self.reports[(week, account_id)].locations:
            if loc.name == name:
                a = loc.assessment
                return a.current, a.usual, a.status
        self.fail(f"{account_id} {name} not in report for {week}")

    def test_back_test_totals(self):
        rows = list(self.location_rows())
        self.assertEqual(len(rows), 1173)  # 69 locations x 17 weeks
        self.assertEqual(Counter(loc.assessment.status for _, _, loc in rows)[NOT_ENOUGH_DATA], 0)
        flags = Counter(week for week, _, loc in rows if loc.assessment.status == BELOW)
        self.assertEqual(sum(flags.values()), 22)
        self.assertEqual(max(flags.values()), 3)
        self.assertAlmostEqual(sum(flags.values()) / 17, 1.29, places=2)
        self.assertEqual(sum(1 for _, _, loc in rows if loc.assessment.status == ABOVE), 45)

    def test_reference_cases_from_the_plan(self):
        d = date
        self.assertEqual(self.find(12, "Site C", d(2026, 7, 20)), (2, 8.5, BELOW))
        self.assertEqual(self.find(6, "Site G", d(2026, 4, 13)), (0, 5.5, BELOW))
        self.assertEqual(self.find(6, "Site G", d(2026, 6, 29)), (0, 4.5, BELOW))  # burst in the window
        self.assertEqual(self.find(18, "Site C", d(2026, 6, 29)), (1, 6, BELOW))
        self.assertEqual(self.find(18, "Site C", d(2026, 7, 13)), (4, 6, NORMAL))
        self.assertEqual(self.find(18, "Site C", d(2026, 6, 22)), (6, 5, NORMAL))
        self.assertEqual(self.find(16, "Site A", d(2026, 7, 20)), (8, 6.5, NORMAL))
        self.assertEqual(self.find(6, "Site M", d(2026, 6, 1)), (50, 3.5, ABOVE))  # the burst week

    def test_default_as_of_result(self):
        self.assertEqual(services.default_as_of(), date(2026, 7, 27))
        report = services.activity_report(Account.objects.get(id=12))
        self.assertEqual((report.week_start, report.week_end), (date(2026, 7, 20), date(2026, 7, 26)))
        statuses = Counter()
        flagged = []
        for account in self.accounts:
            for loc in services.activity_report(account).locations:
                statuses[loc.assessment.status] += 1
                if loc.assessment.status in (BELOW, ABOVE):
                    flagged.append((account.id, loc.name, loc.assessment.status))
        self.assertEqual(statuses, Counter({NORMAL: 67, BELOW: 1, ABOVE: 1}))
        self.assertEqual(sorted(flagged), [(12, "Site C", BELOW), (15, "Site C", ABOVE)])

    def test_account_with_no_events_is_empty(self):
        report = services.activity_report(Account.objects.get(id=20))
        self.assertEqual(report.locations, [])
        self.assertEqual((report.headline.current, report.headline.usual), (0, None))

    def test_burst_week_headline_is_a_number_not_a_status(self):
        headline = self.reports[(date(2026, 6, 1), 6)].headline
        self.assertEqual((headline.current, headline.usual), (881, 66))
        self.assertAlmostEqual(headline.delta_pct, (881 - 66) / 66 * 100)

    def test_headline_has_no_status_for_any_account_or_week(self):
        """The Poisson rule over-flags account totals (variance up to 2.3x the mean), so only
        locations carry a status. Account 6 would have been flagged below in 3 of these 17 weeks."""
        for report in self.reports.values():
            self.assertFalse(hasattr(report.headline, "status"))
        for week in (date(2026, 4, 13), date(2026, 5, 25), date(2026, 7, 13)):
            headline = self.reports[(week, 6)].headline
            self.assertLess(headline.current, headline.usual)  # shown as a drop, not as a flag
        self.assertEqual(
            (self.reports[(date(2026, 4, 13), 6)].headline.current, self.reports[(date(2026, 4, 13), 6)].headline.usual),
            (55, 78.5),
        )

    def test_locations_of_the_same_account_still_get_statuses(self):
        report = self.reports[(date(2026, 4, 13), 6)]
        self.assertTrue(all(hasattr(loc.assessment, "status") for loc in report.locations))
        self.assertIn(BELOW, {loc.assessment.status for loc in report.locations})  # Site G, usual 5.5, got 0

    def test_exactly_eight_seed_events_change_week_between_utc_and_local(self):
        zones = {a.id: ZoneInfo(a.timezone) for a in self.accounts}
        shifted = 0
        for event in ActivityEvent.objects.select_related("location"):
            local = services.local_week_start(event.occurred_at, zones[event.location.account_id])
            shifted += local != services.week_start(event.occurred_at.astimezone(UTC).date())
        self.assertEqual(shifted, 8)
