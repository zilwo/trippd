from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path(
        "notifications/<int:notification_id>/",
        views.notification_redirect,
        name="notification_redirect",
    ),
    path(
        "mark-notification-read/<int:notification_id>/",
        views.mark_notification_as_read,
        name="mark_notification_read",
    ),
    path("verify/<int:pk>/<str:token>/", views.verify_account, name="verify_account"),
    path("<str:username>/", views.UserProfileView.as_view(), name="profile"),
]
