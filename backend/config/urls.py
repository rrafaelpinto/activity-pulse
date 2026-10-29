from django.urls import path

from activity import views

urlpatterns = [
    path("api/accounts/", views.account_list, name="account-list"),
    path("api/accounts/<int:account_id>/activity/", views.account_activity, name="account-activity"),
]
