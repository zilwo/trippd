from django.urls import path
from . import views

urlpatterns = [
    path("", views.DiscoverView.as_view(), name="discover"),
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
    path("ride/chat/<int:pk>/", views.TripHubView.as_view(), name="trip_hub"),
    path("ride/inbox/", views.InboxView.as_view(), name="inbox"),
    path("ride/start-chat/<int:pk>/", views.StartChatView.as_view(), name="start_chat"),
    path(
        "ride/direct-chat/<int:pk>/", views.DirectChatView.as_view(), name="direct_chat"
    ),
    path(
        "ride/complete-trip/<int:pk>/",
        views.complete_trip,
        name="complete_trip",
    ),
    path(
        "ride/finalize/<int:pk>/",
        views.FinalizeTripView.as_view(),
        name="finalize_trip",
    ),
    path(
        "ride/confirm_ongoing/<int:pk>/",
        views.confirm_ongoing,
        name="confirm_ongoing",
    ),
    path(
        "trip/<int:pk>/submit-reviews/",
        views.submit_reviews,
        name="submit_reviews",
    ),
    path(
        "activities/create/",
        views.AcitvityCreateView.as_view(),
        name="activity_create",
    ),
    path(
        "discover/place/<int:pk>/section/<str:section>/",
        views.PlaceSectionListView.as_view(),
        name="place_section_list",
    ),
    path(
        "discover/autocomplete/",
        views.autocomplete_places_view,
        name="autocomplete_places",
    ),
    path(
        "activities/<int:pk>/",
        views.ActivityDetailView.as_view(),
        name="activity_detail",
    ),
    path(
        "places/<str:place_id>/hero-image/",
        views.get_place_hero_image,
        name="place_hero_image",
    ),
    path(
        "discover/place/<int:pk>/",
        views.PlaceDetailView.as_view(),
        name="discover_place",
    ),
    path(
        "discover/place/<int:pk>/section/",
        views.place_section,
        name="discover_place_section",
    ),
    path(
        "toggle-saved-place/<int:pk>/",
        views.toggle_saved_place,
        name="toggle_saved_place",
    ),
    path(
        "saved-places/",
        views.SavedPlaceListView.as_view(),
        name="saved_places",
    ),
    path(
        "discover/search/",
        views.PlaceSearchView.as_view(),
        name="place_search",
    ),
    path(
        "ask-ai/<str:place_id>/",
        views.ask_ai_about_place,
        name="ask_ai",
    ),
    path(
        "homescreen/",
        views.homes,
        name="homes",
    ),
]
