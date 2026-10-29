from types import SimpleNamespace

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from activity import services
from activity.models import Account
from activity.serializers import (
    AccountActivitySerializer,
    AccountSerializer,
    ActivityQuerySerializer,
    AsOfErrorSerializer,
    ErrorSerializer,
)


@extend_schema(summary="List accounts", responses=AccountSerializer(many=True))
@api_view(["GET", "HEAD"])
def account_list(request):
    accounts = Account.objects.order_by("name", "id")
    return Response(AccountSerializer(accounts, many=True).data)


@extend_schema(
    summary="Weekly activity of an account",
    description=(
        "Compares the last complete local week with the median of the up to 8 weeks before it, for "
        "the account (numbers only) and for each location (with a status)."
    ),
    parameters=[ActivityQuerySerializer],
    responses={
        200: AccountActivitySerializer,
        400: AsOfErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["GET", "HEAD"])
def account_activity(request, account_id):
    query = ActivityQuerySerializer(data=request.query_params)
    if not query.is_valid():
        raise ValidationError(query.errors)
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        raise NotFound("Account not found.")

    report = services.activity_report(account, query.validated_data.get("as_of"))
    payload = SimpleNamespace(
        account=account, latest_event_date=services.latest_event_date(), **vars(report)
    )
    return Response(AccountActivitySerializer(payload).data)
