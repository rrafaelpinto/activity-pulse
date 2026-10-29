from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from activity import views

urlpatterns = [
    path("api/accounts/", views.account_list, name="account-list"),
    path("api/accounts/<int:account_id>/activity/", views.account_activity, name="account-activity"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
