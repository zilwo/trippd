from django.urls import path
from . import views

urlpatterns = [
    path("", views.TripListView.as_view(), name="home"),
    path("create-ride/", views.CreateTripView.as_view(), name="create_trip"),
    path("rides/", views.TripListView.as_view(), name="trip_list"),
    path("ride/<int:pk>/", views.TripDetailView.as_view(), name="trip_detail"),
    path("join-ride/<int:pk>/", views.join_trip, name="join_trip"),

]
