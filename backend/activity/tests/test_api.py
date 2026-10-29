from collections import Counter
from datetime import date, datetime, timezone
from io import StringIO

from django.core.management import call_command
from rest_framework.test import APITestCase

from activity.models import Location
from activity.tests.factories import EventFactory, add_account

UTC = timezone.utc
FIRST = date(2026, 3, 2)  # a Monday

LOCATION_KEYS = {
    "id", "name", "this_week", "usual", "delta_pct", "status", "calls", "leads", "appointments",
}


def activity_url(account_id, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"/api/accounts/{account_id}/activity/" + (f"?{query}" if query else "")


class AccountListTests(APITestCase):
    def test_lists_accounts_by_name_with_the_picker_fields_only(self):
        add_account(2, "America/Phoenix", name="Zeta")
        add_account(1, "America/Chicago", name="Alpha")

        response = self.client.get("/api/accounts/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            [
                {"id": 1, "name": "Alpha", "timezone": "America/Chicago"},
                {"id": 2, "name": "Zeta", "timezone": "America/Phoenix"},
            ],
        )

    def test_empty_database_gives_an_empty_list(self):
        response = self.client.get("/api/accounts/")
        self.assertEqual((response.status_code, response.json()), (200, []))


class ActivityResponseTests(APITestCase):
    def setUp(self):
        self.account = add_account(1, "America/Chicago", name="Alpha")
        self.steady = Location.objects.create(account=self.account, name="Steady")
        self.dropped = Location.objects.create(account=self.account, name="Dropped")
        # Nine weeks (03-02 .. 04-27), then the judged week 05-04.
        EventFactory.weekly(self.steady, [10] * 9 + [10], FIRST)
        EventFactory.weekly(self.dropped, [10] * 9 + [1], FIRST)
        EventFactory.weekly(self.dropped, [2] * 10, FIRST, "lead_created")  # per-type counts

    def get(self, **params):
        return self.client.get(activity_url(1, **params))

    def test_response_shape(self):
        data = self.get(as_of="2026-05-11").json()

        self.assertEqual(set(data), {"account", "as_of", "week", "headline", "locations"})
        self.assertEqual(data["account"], {"id": 1, "name": "Alpha", "timezone": "America/Chicago"})
        self.assertEqual(data["as_of"], "2026-05-11")
        self.assertEqual(data["week"], {"start": "2026-05-04", "end": "2026-05-10"})
        for location in data["locations"]:
            self.assertEqual(set(location), LOCATION_KEYS)

    def test_headline_is_numbers_only(self):
        headline = self.get(as_of="2026-05-11").json()["headline"]

        self.assertEqual(set(headline), {"this_week", "usual", "delta_pct"})  # no status
        # Account weekly totals: steady 10 + dropped 12 = 22 in history; judged week 10 + 3 = 13.
        self.assertEqual(headline["this_week"], 13)
        self.assertEqual(headline["usual"], 22.0)
        self.assertEqual(headline["delta_pct"], -40.9)

    def test_locations_carry_status_and_are_sorted_below_first(self):
        locations = self.get(as_of="2026-05-11").json()["locations"]

        self.assertEqual(
            [(loc["name"], loc["status"]) for loc in locations],
            [("Dropped", "below"), ("Steady", "normal")],
        )
        dropped = locations[0]
        self.assertEqual(
            (dropped["this_week"], dropped["usual"], dropped["delta_pct"]), (3, 12.0, -75.0)
        )
        self.assertEqual((dropped["calls"], dropped["leads"], dropped["appointments"]), (1, 2, 0))

    def test_default_as_of_is_the_latest_event_date(self):
        EventFactory.add(self.steady, datetime(2026, 5, 12, 15, 0, tzinfo=UTC))  # Tuesday of week 05-11

        data = self.get().json()

        self.assertEqual(data["as_of"], "2026-05-12")
        self.assertEqual(data["week"], {"start": "2026-05-04", "end": "2026-05-10"})

    def test_as_of_is_echoed_in_canonical_form(self):
        self.assertEqual(self.get(as_of="2026-5-11").json()["as_of"], "2026-05-11")

    def test_numbers_are_rounded_to_one_decimal(self):
        odd = Location.objects.create(account=self.account, name="Odd")
        EventFactory.weekly(odd, [3] * 9 + [4], FIRST)  # usual 3, judged 4: +33.333...%
        row = next(l for l in self.get(as_of="2026-05-11").json()["locations"] if l["name"] == "Odd")
        self.assertEqual((row["usual"], row["this_week"], row["delta_pct"]), (3.0, 4, 33.3))

    def test_location_without_enough_history_has_null_baseline(self):
        newcomer = Location.objects.create(account=self.account, name="Newcomer")
        EventFactory.weekly(newcomer, [4, 4], date(2026, 4, 20))  # first week + 1 history week

        locations = self.get(as_of="2026-05-04").json()["locations"]  # judged week 04-27

        new = next(l for l in locations if l["name"] == "Newcomer")
        self.assertEqual(new["status"], "not_enough_data")
        self.assertIsNone(new["usual"])
        self.assertIsNone(new["delta_pct"])
        self.assertEqual(new["this_week"], 4)

    def test_zero_baseline_has_null_delta_not_a_division_error(self):
        quiet = Location.objects.create(account=self.account, name="Quiet")
        EventFactory.add(quiet, datetime(2026, 3, 3, 12, 0, tzinfo=UTC))  # one event, then silence

        quiet_row = next(l for l in self.get(as_of="2026-05-11").json()["locations"] if l["name"] == "Quiet")

        self.assertEqual((quiet_row["this_week"], quiet_row["usual"], quiet_row["status"]), (0, 0.0, "normal"))
        self.assertIsNone(quiet_row["delta_pct"])

    def test_account_without_events_returns_an_empty_report(self):
        add_account(2, name="Quiet Harbor")
        EventFactory.add(self.steady, datetime(2026, 5, 12, 15, 0, tzinfo=UTC))  # gives a default as_of

        data = self.client.get(activity_url(2)).json()

        self.assertEqual(data["locations"], [])
        self.assertEqual(data["headline"], {"this_week": 0, "usual": None, "delta_pct": None})
        self.assertEqual(data["account"]["name"], "Quiet Harbor")

    def test_as_of_before_any_data_returns_an_empty_report(self):
        data = self.get(as_of="2025-01-06").json()
        self.assertEqual(data["locations"], [])
        self.assertEqual(data["headline"]["this_week"], 0)

    def test_account_timezone_decides_the_week(self):
        phoenix = add_account(3, "America/Phoenix", name="Phoenix")
        utc = add_account(4, "UTC", name="Utc")
        moment = datetime(2026, 3, 9, 6, 30, tzinfo=UTC)  # Sunday 23:30 in Phoenix, Monday in UTC
        for account in (phoenix, utc):
            EventFactory.add(Location.objects.create(account=account, name="Site A"), moment)

        in_phoenix = self.client.get(activity_url(3, as_of="2026-03-09")).json()
        in_utc = self.client.get(activity_url(4, as_of="2026-03-09")).json()

        self.assertEqual(in_phoenix["headline"]["this_week"], 1)
        self.assertEqual(in_utc["headline"]["this_week"], 0)


class ValidationAndErrorTests(APITestCase):
    def setUp(self):
        add_account(1)

    def test_unknown_account_is_404_json(self):
        response = self.client.get(activity_url(999))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Account not found."})

    def test_absurdly_large_account_id_is_404_not_500(self):
        response = self.client.get(activity_url("9" * 30))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Account not found."})

    def test_non_numeric_account_id_is_404(self):
        self.assertEqual(self.client.get("/api/accounts/abc/activity/").status_code, 404)

    def test_invalid_as_of_values_are_400_with_a_field_error(self):
        cases = {
            "abc": "wrong format",
            "2026-02-30": "wrong format",
            "2026-13-01": "wrong format",
            "20260727": "wrong format",
            "2026-07-27T10:00": "wrong format",
            "1999-12-31": "between",
            "2101-01-01": "between",
            "0001-01-01": "between",
            "9999-12-31": "between",
        }
        for value, expected in cases.items():
            response = self.client.get(activity_url(1, as_of=value))
            self.assertEqual(response.status_code, 400, value)
            self.assertEqual(list(response.json()), ["as_of"], value)
            self.assertIn(expected, response.json()["as_of"][0], value)

    def test_blank_as_of_is_rejected_rather_than_ignored(self):
        response = self.client.get("/api/accounts/1/activity/?as_of=")
        self.assertEqual(response.status_code, 400)
        self.assertIn("blank", response.json()["as_of"][0])

    def test_as_of_bounds_are_inclusive(self):
        for value in ("2000-01-01", "2100-12-31"):
            self.assertEqual(self.client.get(activity_url(1, as_of=value)).status_code, 200, value)

    def test_unknown_query_parameters_are_ignored(self):
        self.assertEqual(self.client.get(activity_url(1, page=3)).status_code, 200)

    def test_api_is_read_only(self):
        for url in ("/api/accounts/", activity_url(1)):
            for method in ("post", "put", "patch", "delete"):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 405, f"{method} {url}")
                self.assertEqual(response["Content-Type"], "application/json")

    def test_head_and_options_are_supported(self):
        for url in ("/api/accounts/", activity_url(1)):
            head = self.client.head(url)
            self.assertEqual((head.status_code, head.content), (200, b""), url)
            self.assertEqual(self.client.options(url).status_code, 200, url)

    def test_no_authentication_is_required(self):
        for url in ("/api/accounts/", activity_url(1)):
            self.assertEqual(self.client.get(url).status_code, 200)


class SeedApiTests(APITestCase):
    """The endpoints against the real seed data."""

    @classmethod
    def setUpTestData(cls):
        call_command("import_seed", stdout=StringIO())

    def activity(self, account_id, **params):
        response = self.client.get(activity_url(account_id, **params))
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_all_twenty_accounts_are_listed(self):
        accounts = self.client.get("/api/accounts/").json()
        self.assertEqual(len(accounts), 20)
        self.assertEqual(accounts[0]["name"], "Beacon Home Security")
        self.assertEqual([a["name"] for a in accounts], sorted(a["name"] for a in accounts))

    def test_default_week_flags_exactly_the_locations_the_plan_expects(self):
        statuses = Counter()
        flagged = []
        for account in self.client.get("/api/accounts/").json():
            data = self.activity(account["id"])
            self.assertEqual(data["week"], {"start": "2026-07-20", "end": "2026-07-26"})
            self.assertNotIn("status", data["headline"])
            for location in data["locations"]:
                statuses[location["status"]] += 1
                if location["status"] != "normal":
                    flagged.append((account["id"], location["name"], location["status"]))
        self.assertEqual(statuses, Counter(normal=67, below=1, above=1))
        self.assertEqual(sorted(flagged), [(12, "Site C", "below"), (15, "Site C", "above")])

    def test_redline_tire_flagged_location_numbers(self):
        data = self.activity(12)
        self.assertEqual(data["locations"][0]["name"], "Site C")  # below-usual comes first
        site_c = data["locations"][0]
        self.assertEqual((site_c["this_week"], site_c["usual"], site_c["status"]), (2, 8.5, "below"))
        self.assertEqual(site_c["delta_pct"], -76.5)
        self.assertEqual(data["account"]["timezone"], "America/Los_Angeles")

    def test_metro_collision_burst_week_headline(self):
        data = self.activity(6, as_of="2026-06-08")
        self.assertEqual(data["week"], {"start": "2026-06-01", "end": "2026-06-07"})
        self.assertEqual((data["headline"]["this_week"], data["headline"]["usual"]), (881, 66.0))
        self.assertEqual(len(data["locations"]), 15)
        self.assertTrue(all(loc["status"] in ("above", "normal") for loc in data["locations"]))

    def test_outage_stays_flagged_when_the_burst_is_in_the_baseline(self):
        data = self.activity(6, as_of="2026-07-06")  # judged week 06-29
        site_g = next(loc for loc in data["locations"] if loc["name"] == "Site G")
        self.assertEqual((site_g["this_week"], site_g["usual"], site_g["status"]), (0, 4.5, "below"))

    def test_quiet_harbor_spa_has_no_events(self):
        data = self.activity(20)
        self.assertEqual(data["locations"], [])
        self.assertEqual(data["headline"], {"this_week": 0, "usual": None, "delta_pct": None})

    def test_every_account_and_week_answers_with_a_consistent_shape(self):
        for account in self.client.get("/api/accounts/").json():
            for as_of in ("2026-02-09", "2026-04-13", "2026-07-27"):
                data = self.activity(account["id"], as_of=as_of)
                self.assertEqual(set(data), {"account", "as_of", "week", "headline", "locations"})
                for location in data["locations"]:
                    self.assertEqual(set(location), LOCATION_KEYS)
