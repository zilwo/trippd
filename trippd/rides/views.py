from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView
from django import forms
from .models import Trip, TripMembership, TripMembership
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin

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
            "duration_value",
            "duration_unit",
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


class CreateTripView(LoginRequiredMixin, CreateView):
    model = Trip
    form_class = TripCreateForm
    template_name = "rides/create_trip.html"

    def form_valid(self, form):
        print("Form is valid, setting organizer to:", self.request.user)
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
        TripMembership.objects.create(
            trip=self.object, user=self.request.user, status="accepted"
        )
        messages.success(self.request, "Trip created successfully!")
        return response

    def form_invalid(self, form):
        print("Form is invalid. Errors:", form.errors)
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
    paginate_by = 5

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

@require_POST
@login_required
def join_trip(request, pk):
    trip = Trip.objects.get(pk=pk)
    existing_membership = TripMembership.objects.filter(
        trip=trip, user=request.user
    ).first()

    if trip.organizer == request.user:
        messages.error(request, "You are already the organizer of this trip.")
        return redirect("trip_detail", pk=pk)

    if existing_membership:
        if existing_membership.status == "pending":
            messages.info(request, "Your request to join this trip is already pending.")
        elif existing_membership.status == "accepted":
            messages.info(request, "You are already a member of this trip.")
        elif existing_membership.status == "rejected":
            messages.info(
                request,
                "Your previous request to join this trip was rejected. Please contact the organizer for more information.",
            )
    else:
        TripMembership.objects.create(trip=trip, user=request.user)
        messages.success(
            request, "Your request to join the trip has been sent to the organizer."
        )

    return redirect("trip_detail", pk=pk)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "rides/trip_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organized_trips"] = Trip.objects.filter(
            organizer=self.request.user
        ).order_by("-departure_time")
    
        context["joined_trips"] = (
            TripMembership.objects.filter(user=self.request.user)
            .exclude(trip__organizer=self.request.user)
            .select_related("trip")
            .order_by("-joined_at")
        )
        context["pending_requests"] = TripMembership.objects.filter(
            trip__organizer=self.request.user, status="pending"
        ).select_related("user", "trip").order_by("-joined_at")

        return context
    

class EditTripView(LoginRequiredMixin, UpdateView):
    model = Trip
    form_class = TripCreateForm
    template_name = "rides/create_trip.html"

    def get_queryset(self):
        return Trip.objects.filter(organizer=self.request.user)

    def get_success_url(self):
        return reverse("trip_detail", kwargs={"pk": self.object.pk})
 
@require_POST
@login_required
def delete_trip(request, pk):
    trip = Trip.objects.get(pk=pk)
    if trip.organizer != request.user:
        messages.error(request, "You are not authorized to delete this trip.")
        return redirect("trip_detail", pk=pk)

    trip.delete()
    messages.success(request, "Trip deleted successfully.")
    return redirect("home")

@require_POST
@login_required
def accept_request(request, pk):
    membership = TripMembership.objects.get(pk=pk)
    if membership.trip.organizer != request.user:
        messages.error(request, "You are not authorized to accept this request.")
        return redirect("trip_dashboard")

    membership.status = "accepted"
    membership.save()
    messages.success(request, f"You have accepted {membership.user.username}'s request to join {membership.trip}.")
    return redirect("trip_dashboard")

@require_POST
@login_required
def reject_request(request, pk):
    membership = TripMembership.objects.get(pk=pk)
    if membership.trip.organizer != request.user:
        messages.error(request, "You are not authorized to reject this request.")
        return redirect("trip_dashboard")

    membership.status = "rejected"
    membership.save()
    messages.success(request, f"You have rejected {membership.user.username}'s request to join {membership.trip}.")
    return redirect("trip_dashboard")


