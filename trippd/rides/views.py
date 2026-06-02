from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .models import Trip

# Create your views here.


def home(request):
    return render(request, "rides/home.html")


class CreateTripView(CreateView):
    model = Trip
    fields = [
        "origin",
        "destination",
        "departure_time",
        "expected_arrival_time",
        "price",
        "slots_available",
        "tag",
    ]
    template_name = "rides/create_trip.html"

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("trip_detail", kwargs={"pk": self.object.pk})


class TripDetailView(DetailView):
    model = Trip
    template_name = "rides/trip_detail.html"
    context_object_name = "trip"


class TripListView(ListView):
    model = Trip
    template_name = "rides/trip_list.html"
    context_object_name = "trips"

    def get_queryset(self):
        queryset = super().get_queryset().order_by("-departure_time")
        return queryset
