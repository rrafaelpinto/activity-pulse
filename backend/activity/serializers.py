from datetime import date

from rest_framework import serializers

from activity.models import Account

# as_of is a calendar date; bounds keep date arithmetic far from datetime.min/max.
AS_OF_MIN = date(2000, 1, 1)
AS_OF_MAX = date(2100, 12, 31)


class ActivityQuerySerializer(serializers.Serializer):
    """Validates the query string of the activity endpoint."""

    as_of = serializers.DateField(required=False, input_formats=["%Y-%m-%d"])

    def to_internal_value(self, data):
        # DRF treats an empty value as "not provided"; an explicit empty as_of is a client mistake.
        if data.get("as_of") == "":
            raise serializers.ValidationError({"as_of": ["This field may not be blank."]})
        return super().to_internal_value(data)

    def validate_as_of(self, value):
        if not AS_OF_MIN <= value <= AS_OF_MAX:
            raise serializers.ValidationError(f"Date must be between {AS_OF_MIN} and {AS_OF_MAX}.")
        return value


class RoundedFloatField(serializers.FloatField):
    """Floats with one decimal; None is passed through by the serializer."""

    def to_representation(self, value):
        return round(float(value), 1)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "name", "timezone"]


class HeadlineSerializer(serializers.Serializer):
    """Numbers only: no status for the account as a whole."""

    this_week = serializers.IntegerField(source="current")
    usual = RoundedFloatField(allow_null=True)
    delta_pct = RoundedFloatField(allow_null=True)


class LocationActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField(source="location_id")
    name = serializers.CharField()
    this_week = serializers.IntegerField(source="assessment.current")
    usual = RoundedFloatField(source="assessment.usual", allow_null=True)
    delta_pct = RoundedFloatField(source="assessment.delta_pct", allow_null=True)
    status = serializers.CharField(source="assessment.status")
    calls = serializers.IntegerField()
    leads = serializers.IntegerField()
    appointments = serializers.IntegerField()


class AccountActivitySerializer(serializers.Serializer):
    as_of = serializers.DateField()
    week = serializers.SerializerMethodField()
    headline = HeadlineSerializer()
    locations = LocationActivitySerializer(many=True)

    def get_week(self, report):
        return {"start": report.week_start.isoformat(), "end": report.week_end.isoformat()}
