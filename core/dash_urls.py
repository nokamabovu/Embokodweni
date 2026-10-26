from django.contrib.auth import views as auth_views
from django.urls import path

from . import dashboard

urlpatterns = [
    path("login/", dashboard.StaffLoginView.as_view(), name="dash_login"),
    path("manifest.webmanifest", dashboard.manifest, name="dash_manifest"),
    path("sw.js", dashboard.service_worker, name="dash_sw"),
    path("logout/", auth_views.LogoutView.as_view(next_page="dash_login"), name="dash_logout"),
    path("", dashboard.overview, name="dash_overview"),
    path("inbox/", dashboard.inbox, name="dash_inbox"),
    path("bookings/<int:pk>/", dashboard.booking_detail, name="dash_booking"),
    path("messages/<int:pk>/", dashboard.message_detail, name="dash_message"),
    path("notifications/", dashboard.notifications, name="dash_notifications"),
    path("notifications/<int:pk>/", dashboard.notification_open, name="dash_notification_open"),
    path("notifications/api/", dashboard.notifications_api, name="dash_notifications_api"),
    path("blocked-dates/", dashboard.blocked_dates, name="dash_blocked"),
]
