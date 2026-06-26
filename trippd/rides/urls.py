from django.urls import path
from . import views

urlpatterns = [
    path("", views.TripListView.as_view(), name=""),
    path("create-ride/", views.CreateTripView.as_view(), name="create_trip"),
    path("autopopulate/", views.auto_populate, name="autopopulate"),
    path("rides/", views.TripListView.as_view(), name="trip_list"),
    path("companions/", views.CompanionListView.as_view(), name="companion_list"),
    path("ride/<int:pk>/", views.TripDetailView.as_view(), name="trip_detail"),
    path("join-ride/<int:pk>/", views.join_trip_request, name="join_trip_request"),
    path(
        "leave-ride/<int:pk>/",
        views.cancel_trip_joining_request,
        name="cancel_trip_joining_request",
    ),
    path("ride/dashboard/", views.DashboardView.as_view(), name="trip_dashboard"),
    path("ride/accept/<int:pk>/", views.accept_request, name="accept_request"),
    path("ride/reject/<int:pk>/", views.reject_request, name="reject_request"),
    path("ride/<int:pk>/delete-ride/", views.delete_trip, name="delete_trip"),
    path("ride/<int:pk>/edit/", views.EditTripView.as_view(), name="edit_trip"),
    path(
        "companion/<int:pk>/edit/", views.EditTripView.as_view(), name="edit_companion"
    ),
    path("ride/chat/<int:pk>/", views.ChatView.as_view(), name="trip_chat"),
    path("ride/inbox/", views.InboxView.as_view(), name="inbox"),
    path("ride/start-chat/<int:pk>/", views.StartChatView.as_view(), name="start_chat"),
    path(
        "ride/direct-chat/<int:pk>/", views.DirectChatView.as_view(), name="direct_chat"
    ),
    path(
        "ride/advance-status/<int:pk>/",
        views.advance_trip_status,
        name="advance_trip_status",
    ),
    path(
        "ride/finalize/<int:pk>/",
        views.FinalizeTripView.as_view(),
        name="finalize_trip",
    ),
]
