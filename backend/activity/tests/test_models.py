from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from activity.models import Account, ActivityEvent, Location

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)


def make_location(account_id=1, name="Site A", tz="America/Chicago"):
    account, _ = Account.objects.get_or_create(
        id=account_id,
        defaults={"name": f"Account {account_id}", "industry": "Test", "timezone": tz, "created_at": NOW},
    )
    return Location.objects.get_or_create(account=account, name=name)[0]


def make_event(location, event_id, event_type, outcome=None, duration=None):
    return ActivityEvent.objects.create(
        id=event_id,
        location=location,
        event_type=event_type,
        occurred_at=NOW,
        outcome=outcome,
        duration_seconds=duration,
    )


class EventConstraintTests(TestCase):
    def setUp(self):
        self.location = make_location()

    def assert_rejected(self, **kwargs):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_event(self.location, 1, **kwargs)

    def test_valid_outcomes_per_type_are_accepted(self):
        valid = [
            ("call_received", "connected", 60),
            ("call_received", "missed", None),
            ("call_received", "voicemail", 30),
            ("lead_created", "open", None),
            ("lead_created", "converted", None),
            ("appointment_set", "completed", None),
            ("appointment_set", "no_show", None),
        ]
        for i, (event_type, outcome, duration) in enumerate(valid, start=1):
            make_event(self.location, i, event_type, outcome, duration)
        self.assertEqual(ActivityEvent.objects.count(), len(valid))

    def test_null_outcome_and_null_duration_are_accepted(self):
        make_event(self.location, 1, "call_received")
        make_event(self.location, 2, "lead_created")
        self.assertEqual(ActivityEvent.objects.filter(outcome__isnull=True).count(), 2)

    def test_unknown_event_type_is_rejected(self):
        self.assert_rejected(event_type="email_sent")

    def test_outcome_must_match_event_type(self):
        self.assert_rejected(event_type="call_received", outcome="converted")
        self.assert_rejected(event_type="lead_created", outcome="missed")
        self.assert_rejected(event_type="appointment_set", outcome="connected")

    def test_unknown_outcome_is_rejected(self):
        self.assert_rejected(event_type="call_received", outcome="bogus")

    def test_duration_only_allowed_for_calls(self):
        self.assert_rejected(event_type="lead_created", duration=30)
        self.assert_rejected(event_type="appointment_set", duration=30)

    def test_call_duration_must_be_positive(self):
        self.assert_rejected(event_type="call_received", duration=0)

    def test_exact_duplicate_events_are_allowed(self):
        make_event(self.location, 1, "call_received", "connected", 60)
        make_event(self.location, 2, "call_received", "connected", 60)
        self.assertEqual(ActivityEvent.objects.count(), 2)


class LocationAndAccountTests(TestCase):
    def test_location_name_is_unique_within_an_account(self):
        location = make_location(1, "Site A")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Location.objects.create(account=location.account, name="Site A")

    def test_same_location_name_is_allowed_in_different_accounts(self):
        make_location(1, "Site A")
        make_location(2, "Site A")
        self.assertEqual(Location.objects.filter(name="Site A").count(), 2)

    def test_timezone_must_be_a_valid_iana_name(self):
        for tz in ("UTC", "America/Phoenix", "America/Los_Angeles"):
            Account(id=1, name="a", industry="i", timezone=tz, created_at=NOW).full_clean()
        for tz in ("Mars/Olympus", "CST", ""):
            with self.assertRaises(ValidationError, msg=tz):
                Account(id=1, name="a", industry="i", timezone=tz, created_at=NOW).full_clean()
