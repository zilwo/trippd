from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("create-ride/", views.CreateTripView.as_view(), name="create_trip"),
    path("ride/<int:pk>/", views.TripDetailView.as_view(), name="trip_detail"),
    path("rides/", views.TripListView.as_view(), name="trip_list"),

]
