from datetime import datetime, timedelta, timezone

from activity.models import Account, ActivityEvent

UTC = timezone.utc


def add_account(account_id, tz="America/Chicago", name=None):
    return Account.objects.create(
        id=account_id,
        name=name or f"Account {account_id}",
        industry="Test",
        timezone=tz,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


class EventFactory:
    next_id = 1

    @classmethod
    def add(cls, location, moment, event_type="call_received"):
        cls.next_id += 1
        return ActivityEvent.objects.create(
            id=cls.next_id, location=location, event_type=event_type, occurred_at=moment
        )

    @classmethod
    def weekly(cls, location, counts, first_monday, event_type="call_received"):
        """Add counts[i] events on the Wednesday of the i-th week after first_monday."""
        for i, n in enumerate(counts):
            wednesday = datetime.combine(first_monday + timedelta(weeks=i, days=2), datetime.min.time())
            for _ in range(n):
                cls.add(location, wednesday.replace(hour=18, tzinfo=UTC), event_type)
