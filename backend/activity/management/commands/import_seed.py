import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from activity.models import Account, ActivityEvent, Location, validate_iana_timezone

DEFAULT_DIR = Path(settings.BASE_DIR).parent


def parse_utc(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def load_source(schema_path, seed_path):
    """Run schema.sql + seed.sql in an in-memory SQLite and return plain rows.

    Letting SQLite parse the seed avoids hand-parsing SQL. Both files are
    repository-owned inputs, not user data.
    """
    source = sqlite3.connect(":memory:")
    try:
        source.executescript(Path(schema_path).read_text())
        source.executescript(Path(seed_path).read_text())
        accounts = source.execute(
            "SELECT id, name, industry, timezone, created_at FROM accounts ORDER BY id"
        ).fetchall()
        events = source.execute(
            "SELECT id, account_id, location, event_type, occurred_at, duration_seconds, outcome "
            "FROM activity_events ORDER BY id"
        ).fetchall()
    except (sqlite3.Error, OSError) as exc:
        raise CommandError(f"Could not read seed files: {exc}") from exc
    finally:
        source.close()
    return accounts, events


def db_event_rows():
    """The imported events in the same shape and order as the source rows."""
    return [
        (
            e.id,
            e.location.account_id,
            e.location.name,
            e.event_type,
            e.occurred_at,
            e.duration_seconds,
            e.outcome,
        )
        for e in ActivityEvent.objects.select_related("location").order_by("id")
    ]


def expected_event_rows(events):
    return [(i, a, loc, t, parse_utc(ts), dur, out) for i, a, loc, t, ts, dur, out in events]


class Command(BaseCommand):
    help = (
        "Import schema.sql/seed.sql into the Django models, preserving original ids and every row. "
        "Refuses to run on a non-empty database unless --replace is given. All-or-nothing."
    )

    def add_arguments(self, parser):
        parser.add_argument("--schema", default=str(DEFAULT_DIR / "schema.sql"))
        parser.add_argument("--seed", default=str(DEFAULT_DIR / "seed.sql"))
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing accounts, locations and events before importing.",
        )

    def handle(self, *args, schema, seed, replace, **options):
        accounts, events = load_source(schema, seed)

        already_loaded = (
            Account.objects.exists() or Location.objects.exists() or ActivityEvent.objects.exists()
        )
        if already_loaded and not replace:
            raise CommandError("Database already contains data. Re-run with --replace to reload it.")

        try:
            with transaction.atomic():
                if already_loaded:
                    ActivityEvent.objects.all().delete()
                    Location.objects.all().delete()
                    Account.objects.all().delete()
                self._load(accounts, events)
                self._verify(accounts, events)
        except (DatabaseError, ValidationError) as exc:
            raise CommandError(f"Import failed and was rolled back: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {Account.objects.count()} accounts, {Location.objects.count()} locations, "
                f"{ActivityEvent.objects.count()} events."
            )
        )

    def _load(self, accounts, events):
        for _id, _name, _industry, tz, _created in accounts:
            validate_iana_timezone(tz)
        Account.objects.bulk_create(
            Account(id=i, name=n, industry=ind, timezone=tz, created_at=parse_utc(c))
            for i, n, ind, tz, c in accounts
        )

        # Locations only exist as strings on events. Derive them and give them explicit ids in
        # sorted order: autoincrement is not reset by a delete, so relying on it would change
        # location ids on every --replace.
        pairs = sorted({(account_id, location) for _i, account_id, location, *_ in events})
        location_ids = {pair: n for n, pair in enumerate(pairs, start=1)}
        Location.objects.bulk_create(
            Location(id=location_ids[(a, name)], account_id=a, name=name) for a, name in pairs
        )

        ActivityEvent.objects.bulk_create(
            ActivityEvent(
                id=i,
                location_id=location_ids[(account_id, location)],
                event_type=event_type,
                occurred_at=parse_utc(occurred_at),
                duration_seconds=duration,
                outcome=outcome,
            )
            for i, account_id, location, event_type, occurred_at, duration, outcome in events
        )

    def _verify(self, accounts, events):
        """Compare what is in the database with the source; raise to roll back on any difference."""
        if Account.objects.count() != len(accounts):
            raise CommandError(
                f"Account count mismatch: {Account.objects.count()} imported, {len(accounts)} in source."
            )
        if ActivityEvent.objects.count() != len(events):
            raise CommandError(
                f"Event count mismatch: {ActivityEvent.objects.count()} imported, {len(events)} in source."
            )
        expected_locations = {(a, loc) for _i, a, loc, *_ in events}
        if Location.objects.count() != len(expected_locations):
            raise CommandError("Location count mismatch between database and source.")
        if db_event_rows() != expected_event_rows(events):
            raise CommandError("Imported events differ from the source rows.")
