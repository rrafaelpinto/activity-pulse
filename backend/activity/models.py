from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def validate_iana_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        raise ValidationError(f"{value!r} is not a valid IANA timezone.")


# Which outcomes are valid for which event type (used by a database check constraint).
CALL_OUTCOMES = ("connected", "missed", "voicemail")
LEAD_OUTCOMES = ("open", "converted")
APPOINTMENT_OUTCOMES = ("completed", "no_show")


class Account(models.Model):
    # Ids come from the seed data and are preserved on import.
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=120)
    industry = models.CharField(max_length=60)
    timezone = models.CharField(max_length=60, validators=[validate_iana_timezone])
    created_at = models.DateTimeField()

    def __str__(self):
        return self.name


class Location(models.Model):
    """A site/branch. Names such as "Site A" are only unique within an account."""

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=80)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["account", "name"], name="location_unique_name_per_account"),
        ]

    def __str__(self):
        return f"{self.account_id}/{self.name}"


class ActivityEvent(models.Model):
    class EventType(models.TextChoices):
        CALL = "call_received"
        LEAD = "lead_created"
        APPOINTMENT = "appointment_set"

    class Outcome(models.TextChoices):
        CONNECTED = "connected"
        MISSED = "missed"
        VOICEMAIL = "voicemail"
        OPEN = "open"
        CONVERTED = "converted"
        COMPLETED = "completed"
        NO_SHOW = "no_show"

    # Ids come from the seed data and are preserved on import.
    id = models.IntegerField(primary_key=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    occurred_at = models.DateTimeField()  # stored as UTC
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    outcome = models.CharField(max_length=40, choices=Outcome.choices, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["location", "occurred_at"], name="event_location_occurred_idx"),
        ]
        # Deliberately no uniqueness on (location, event_type, occurred_at):
        # apparent duplicates in the seed are kept.
        constraints = [
            models.CheckConstraint(
                condition=Q(event_type__in=["call_received", "lead_created", "appointment_set"]),
                name="event_type_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(outcome__isnull=True)
                    | (Q(event_type="call_received") & Q(outcome__in=CALL_OUTCOMES))
                    | (Q(event_type="lead_created") & Q(outcome__in=LEAD_OUTCOMES))
                    | (Q(event_type="appointment_set") & Q(outcome__in=APPOINTMENT_OUTCOMES))
                ),
                name="event_outcome_valid_for_type",
            ),
            models.CheckConstraint(
                condition=Q(duration_seconds__isnull=True)
                | (Q(event_type="call_received") & Q(duration_seconds__gt=0)),
                name="event_duration_only_for_calls",
            ),
        ]

    def __str__(self):
        return f"{self.event_type}@{self.occurred_at:%Y-%m-%d %H:%M}"
