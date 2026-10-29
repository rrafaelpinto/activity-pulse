from datetime import date

from rest_framework import serializers

from activity import services
from activity.models import Account

# as_of is a calendar date; bounds keep date arithmetic far from datetime.min/max.
AS_OF_MIN = date(2000, 1, 1)
AS_OF_MAX = date(2100, 12, 31)


class ActivityQuerySerializer(serializers.Serializer):
    """Validates the query string of the activity endpoint."""

    as_of = serializers.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        help_text=(
            "YYYY-MM-DD, interpreted in the account's timezone. The judged week is the complete week "
            "before the week containing this date. Defaults to the latest event date; later dates "
            "are rejected."
        ),
    )

    def to_internal_value(self, data):
        # DRF treats an empty value as "not provided"; an explicit empty as_of is a client mistake.
        if data.get("as_of") == "":
            raise serializers.ValidationError({"as_of": ["This field may not be blank."]})
        return super().to_internal_value(data)

    def validate_as_of(self, value):
        if not AS_OF_MIN <= value <= AS_OF_MAX:
            raise serializers.ValidationError(f"Date must be between {AS_OF_MIN} and {AS_OF_MAX}.")
        # Past the newest data, the empty recent weeks would read as a real drop in activity.
        latest = services.latest_event_date()
        if latest is not None and value > latest:
            raise serializers.ValidationError(
                f"as_of cannot be later than the latest available event date ({latest})."
            )
        return value


class RoundedFloatField(serializers.FloatField):
    """Floats with one decimal; None is passed through by the serializer."""

    def to_representation(self, value):
        return round(float(value), 1)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "name", "timezone"]


USUAL_HELP = "Median of the up to 8 weeks before the judged week; null without 4 weeks of history."
DELTA_HELP = "Percentage change of this_week against usual, one decimal; null when usual is null or 0."


class WeekSerializer(serializers.Serializer):
    start = serializers.DateField(source="week_start", help_text="Monday of the judged week (account's timezone).")
    end = serializers.DateField(source="week_end", help_text="Sunday of the judged week.")


class HeadlineSerializer(serializers.Serializer):
    """Numbers only: no status for the account as a whole."""

    this_week = serializers.IntegerField(source="current", help_text="Events in the judged week, all locations.")
    usual = RoundedFloatField(allow_null=True, help_text="Median of the account's own weekly totals over the same window; null without 4 weeks of history.")
    delta_pct = RoundedFloatField(allow_null=True, help_text=DELTA_HELP)


class WeekCountSerializer(serializers.Serializer):
    week_start = serializers.DateField(help_text="Monday of that week (account's timezone).")
    count = serializers.IntegerField(help_text="Events in that week; 0 for a week without activity.")


class LocationActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField(source="location_id")
    name = serializers.CharField()
    this_week = serializers.IntegerField(source="assessment.current", help_text="Events in the judged week.")
    usual = RoundedFloatField(source="assessment.usual", allow_null=True, help_text=USUAL_HELP)
    delta_pct = RoundedFloatField(source="assessment.delta_pct", allow_null=True, help_text=DELTA_HELP)
    status = serializers.ChoiceField(
        source="assessment.status",
        choices=[services.BELOW, services.NORMAL, services.ABOVE, services.NOT_ENOUGH_DATA],
        help_text=(
            "below/above: this_week is unusually low/high against usual (Poisson tail, p < 0.025); "
            "below may need attention. not_enough_data: fewer than 4 weeks of history."
        ),
    )
    calls = serializers.IntegerField(help_text="call_received events in the judged week.")
    leads = serializers.IntegerField(help_text="lead_created events in the judged week.")
    appointments = serializers.IntegerField(help_text="appointment_set events in the judged week.")
    history = WeekCountSerializer(
        many=True,
        help_text=(
            "The weekly counts that usual is the median of, oldest first: up to 8 weeks before the "
            "judged week, starting the week after the location's first event. Fewer than 4 means "
            "usual is null."
        ),
    )


class AccountActivitySerializer(serializers.Serializer):
    """Response of the activity endpoint. Locations are sorted below-usual first."""

    account = AccountSerializer()
    as_of = serializers.DateField(help_text="The date used; defaults to the latest event date.")
    latest_event_date = serializers.DateField(
        allow_null=True,
        help_text="Latest event date in the data (UTC) and the maximum allowed as_of; null if there are no events.",
    )
    week = WeekSerializer(source="*")
    headline = HeadlineSerializer()
    locations = LocationActivitySerializer(many=True)


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class AsOfErrorSerializer(serializers.Serializer):
    as_of = serializers.ListField(child=serializers.CharField())
