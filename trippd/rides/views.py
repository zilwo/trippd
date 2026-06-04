from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView
from django import forms
from .models import Trip
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.


def home(request):
    return render(request, "rides/home.html")


class TripCreateForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "origin",
            "destination",
            "description",
            "from_address",
            "to_address",
            "departure_time",
            "expected_arrival_time",
            "price",
            "slots_available",
            "tag",
        ]

    def clean(self):
        cleaned_data = super().clean()
        departure_time = cleaned_data.get("departure_time")
        expected_arrival_time = cleaned_data.get("expected_arrival_time")

        if departure_time and expected_arrival_time:
            if expected_arrival_time <= departure_time:
                raise forms.ValidationError(
                    "Expected arrival time must be after departure time."
                )

        return cleaned_data


class CreateTripView(CreateView):
    model = Trip
    form_class = TripCreateForm
    template_name = "rides/create_trip.html"

    def form_valid(self, form):
        print("Form is valid, setting organizer to:", self.request.user)
        form.instance.organizer = self.request.user
        messages.success(self.request, "Trip created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form is invalid. Errors:", form.errors)
        messages.error(self.request, "There were errors in the form. Please correct them and try again.")
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
    paginate_by = 2

    def get_queryset(self):
        queryset = super().get_queryset()
        origin = self.request.GET.get("origin")
        destination = self.request.GET.get("destination")
        departure = self.request.GET.get("departure")
        passengers = self.request.GET.get("passengers")

        if origin:
            queryset = queryset.filter(origin__icontains=origin)
        if destination:
            queryset = queryset.filter(destination__icontains=destination)
        if departure:
            queryset = queryset.filter(departure_time__date=departure)
        if passengers:
            queryset = queryset.filter(slots_available__gte=passengers)

        return queryset.order_by("-created_at")


@login_required
def join_trip(request, pk):
    trip = Trip.objects.get(pk=pk)

    if trip.organizer == request.user:
        messages.error(request, "You are already the organizer of this trip.")
        return redirect("trip_detail", pk=pk)
    if trip.slots_available > 0:
        trip.slots_available -= 1
        trip.save()
        messages.success(
            request,
            "You have successfully joined the trip! Wait for the organizer to accept your request.",
        )
    else:
        messages.error(request, "Sorry, no slots available for this trip.")

    return redirect("trip_detail", pk=pk)
