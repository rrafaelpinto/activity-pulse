from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from activity import services
from activity.models import Account
from activity.serializers import (
    AccountActivitySerializer,
    AccountSerializer,
    ActivityQuerySerializer,
)


@api_view(["GET", "HEAD"])
def account_list(request):
    accounts = Account.objects.order_by("name", "id")
    return Response(AccountSerializer(accounts, many=True).data)


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
    return Response(
        {
            "account": AccountSerializer(account).data,
            **AccountActivitySerializer(report).data,
        }
    )
