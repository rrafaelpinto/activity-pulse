import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase

from activity.management.commands.import_seed import db_event_rows
from activity.models import Account, ActivityEvent, Location

REPO_DIR = Path(settings.BASE_DIR).parent
SCHEMA = REPO_DIR / "schema.sql"

ACCOUNTS_SQL = (
    "INSERT INTO accounts (id, name, industry, timezone, created_at) "
    "VALUES (1, 'Alpha', 'Dental', 'America/Chicago', '2025-01-01 12:00:00');\n"
    "INSERT INTO accounts (id, name, industry, timezone, created_at) "
    "VALUES (2, 'Beta', 'Spa', 'America/Phoenix', '2025-01-01 12:00:00');\n"
)


def event_sql(i, account_id, location, event_type, ts, duration="NULL", outcome="NULL"):
    outcome = outcome if outcome == "NULL" else f"'{outcome}'"
    return (
        "INSERT INTO activity_events (id, account_id, location, event_type, occurred_at, "
        f"duration_seconds, outcome) VALUES ({i}, {account_id}, '{location}', '{event_type}', "
        f"'{ts}', {duration}, {outcome});\n"
    )


GOOD_EVENTS = [
    event_sql(10, 1, "Site A", "call_received", "2026-02-02 10:00:00", 120, "connected"),
    event_sql(11, 1, "Site A", "call_received", "2026-02-02 10:00:00", 120, "connected"),  # duplicate kept
    event_sql(12, 1, "Site B", "lead_created", "2026-02-02 11:00:00"),  # null outcome
    event_sql(13, 2, "Site A", "appointment_set", "2026-02-03 09:30:00", outcome="no_show"),
]
GOOD_SEED = ACCOUNTS_SQL + "".join(GOOD_EVENTS)
# A call can't have the outcome "converted": the database CHECK constraint must reject it.
BAD_SEED = ACCOUNTS_SQL + "".join(
    GOOD_EVENTS[:2] + [event_sql(14, 1, "Site C", "call_received", "2026-02-04 10:00:00", 60, "converted")]
)
BAD_TZ_SEED = ACCOUNTS_SQL.replace("America/Phoenix", "Mars/Olympus") + "".join(GOOD_EVENTS)


class ImportTestCase(TransactionTestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def write_seed(self, sql, name="seed.sql"):
        path = self.tmp / name
        path.write_text(sql)
        return path

    def run_import(self, seed, replace=False, schema=SCHEMA):
        args = ["--schema", str(schema), "--seed", str(seed)]
        if replace:
            args.append("--replace")
        out = StringIO()
        call_command("import_seed", *args, stdout=out)
        return out.getvalue()

    def snapshot(self):
        return (
            list(Account.objects.order_by("id").values_list("id", "name", "timezone", "created_at")),
            list(Location.objects.order_by("id").values_list("id", "account_id", "name")),
            db_event_rows(),
        )


class SmallSeedImportTests(ImportTestCase):
    def test_imports_rows_preserving_ids_and_values(self):
        self.run_import(self.write_seed(GOOD_SEED))

        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(ActivityEvent.objects.count(), 4)
        self.assertEqual(set(ActivityEvent.objects.values_list("id", flat=True)), {10, 11, 12, 13})
        # "Site A" exists in both accounts: two locations, plus Alpha's Site B.
        self.assertEqual(Location.objects.count(), 3)
        lead = ActivityEvent.objects.get(id=12)
        self.assertIsNone(lead.outcome)
        self.assertIsNone(lead.duration_seconds)
        self.assertEqual(lead.occurred_at.isoformat(), "2026-02-02T11:00:00+00:00")
        self.assertEqual(ActivityEvent.objects.get(id=13).location.account_id, 2)

    def test_duplicate_events_are_kept(self):
        self.run_import(self.write_seed(GOOD_SEED))
        self.assertEqual(ActivityEvent.objects.filter(id__in=[10, 11]).count(), 2)

    def test_refuses_to_run_on_a_non_empty_database_without_replace(self):
        seed = self.write_seed(GOOD_SEED)
        self.run_import(seed)
        before = self.snapshot()

        with self.assertRaisesMessage(CommandError, "--replace"):
            self.run_import(seed)

        self.assertEqual(self.snapshot(), before)

    def test_replace_is_repeatable_and_idempotent(self):
        seed = self.write_seed(GOOD_SEED)
        self.run_import(seed)
        first = self.snapshot()

        self.run_import(seed, replace=True)
        self.run_import(seed, replace=True)

        self.assertEqual(self.snapshot(), first)

    def test_replace_swaps_old_data_for_the_new_seed(self):
        self.run_import(self.write_seed(GOOD_SEED))
        smaller = ACCOUNTS_SQL + GOOD_EVENTS[0]

        self.run_import(self.write_seed(smaller, "small.sql"), replace=True)

        self.assertEqual(ActivityEvent.objects.count(), 1)
        self.assertEqual(Location.objects.count(), 1)


class ImportRollbackTests(ImportTestCase):
    def test_constraint_violation_rolls_back_a_fresh_import(self):
        with self.assertRaisesMessage(CommandError, "rolled back"):
            self.run_import(self.write_seed(BAD_SEED))

        self.assertEqual(Account.objects.count(), 0)
        self.assertEqual(Location.objects.count(), 0)
        self.assertEqual(ActivityEvent.objects.count(), 0)

    def test_failed_replace_keeps_the_previous_data_intact(self):
        self.run_import(self.write_seed(GOOD_SEED))
        before = self.snapshot()

        with self.assertRaisesMessage(CommandError, "rolled back"):
            self.run_import(self.write_seed(BAD_SEED, "bad.sql"), replace=True)

        self.assertEqual(self.snapshot(), before)

    def test_invalid_timezone_is_rejected_and_rolled_back(self):
        self.run_import(self.write_seed(GOOD_SEED))
        before = self.snapshot()

        with self.assertRaisesMessage(CommandError, "rolled back"):
            self.run_import(self.write_seed(BAD_TZ_SEED, "tz.sql"), replace=True)

        self.assertEqual(self.snapshot(), before)

    def test_verification_failure_rolls_back_a_replace(self):
        """If rows silently go missing, the post-load verification must abort and restore the old data."""
        self.run_import(self.write_seed(GOOD_SEED))
        before = self.snapshot()
        real_bulk_create = ActivityEvent.objects.bulk_create

        def lossy_bulk_create(objs, *args, **kwargs):
            return real_bulk_create(list(objs)[:-1], *args, **kwargs)

        with mock.patch.object(ActivityEvent.objects, "bulk_create", side_effect=lossy_bulk_create):
            with self.assertRaisesMessage(CommandError, "Event count mismatch"):
                self.run_import(self.write_seed(GOOD_SEED, "again.sql"), replace=True)

        self.assertEqual(self.snapshot(), before)

    def test_changed_row_content_is_caught_by_verification(self):
        real_bulk_create = ActivityEvent.objects.bulk_create

        def corrupting_bulk_create(objs, *args, **kwargs):
            objs = list(objs)
            objs[0].outcome = "missed"  # same count, different content
            return real_bulk_create(objs, *args, **kwargs)

        with mock.patch.object(ActivityEvent.objects, "bulk_create", side_effect=corrupting_bulk_create):
            with self.assertRaisesMessage(CommandError, "differ from the source"):
                self.run_import(self.write_seed(GOOD_SEED))

        self.assertEqual(ActivityEvent.objects.count(), 0)

    def test_missing_or_broken_seed_files_do_not_touch_the_database(self):
        self.run_import(self.write_seed(GOOD_SEED))
        before = self.snapshot()

        with self.assertRaisesMessage(CommandError, "Could not read seed files"):
            self.run_import(self.tmp / "nope.sql", replace=True)
        with self.assertRaisesMessage(CommandError, "Could not read seed files"):
            self.run_import(self.write_seed("INSERT INTO nowhere VALUES (1);", "broken.sql"), replace=True)

        self.assertEqual(self.snapshot(), before)


class RealSeedImportTests(ImportTestCase):
    """Runs against the real seed.sql and checks it against an independent read of the source."""

    SEED = REPO_DIR / "seed.sql"

    def source(self, sql):
        con = sqlite3.connect(":memory:")
        self.addCleanup(con.close)
        con.executescript(SCHEMA.read_text() + self.SEED.read_text())
        return con.execute(sql).fetchall()

    def test_real_seed_is_imported_completely(self):
        self.run_import(self.SEED)

        self.assertEqual(Account.objects.count(), 20)
        self.assertEqual(Location.objects.count(), 69)
        self.assertEqual(ActivityEvent.objects.count(), 12626)
        # Original ids are preserved (the seed uses 1..12626 with no gaps).
        self.assertEqual(
            set(ActivityEvent.objects.values_list("id", flat=True)), set(range(1, 12627))
        )

    def test_real_seed_nulls_and_duplicates_are_preserved(self):
        self.run_import(self.SEED)

        for field, sql in [
            ("outcome", "SELECT COUNT(*) FROM activity_events WHERE outcome IS NULL"),
            ("duration_seconds", "SELECT COUNT(*) FROM activity_events WHERE duration_seconds IS NULL"),
        ]:
            expected = self.source(sql)[0][0]
            self.assertEqual(ActivityEvent.objects.filter(**{f"{field}__isnull": True}).count(), expected)
        duplicate_groups = self.source(
            "SELECT COUNT(*) FROM (SELECT 1 FROM activity_events "
            "GROUP BY account_id, location, event_type, occurred_at HAVING COUNT(*) > 1)"
        )[0][0]
        self.assertEqual(duplicate_groups, 12)
        # Same grouping in the imported data: nothing was deduplicated.
        from django.db.models import Count

        imported_groups = (
            ActivityEvent.objects.values("location", "event_type", "occurred_at")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
            .count()
        )
        self.assertEqual(imported_groups, duplicate_groups)

    def test_real_seed_per_account_event_counts_match_the_source(self):
        self.run_import(self.SEED)

        expected = dict(self.source("SELECT account_id, COUNT(*) FROM activity_events GROUP BY account_id"))
        actual = {}
        for event in ActivityEvent.objects.select_related("location"):
            actual[event.location.account_id] = actual.get(event.location.account_id, 0) + 1
        self.assertEqual(actual, expected)
        # Quiet Harbor Spa (account 20) has no events and therefore no locations.
        self.assertEqual(Account.objects.get(id=20).locations.count(), 0)

    def test_real_seed_replace_is_repeatable(self):
        self.run_import(self.SEED)
        first = self.snapshot()

        self.run_import(self.SEED, replace=True)

        self.assertEqual(self.snapshot(), first)
