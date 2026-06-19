from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django import forms

from users.models import Language, User
from .models import (
    Conversation,
    Trip,
    TripMembership,
    TripMembership,
    TripGroup,
    TripGroupMessage,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from .services.autocomplete_location import autocomplete_location
from django.http import HttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Count


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
            "budget",
            "slots_available",
            "tag",
            "duration_value",
            "duration_unit",
            "orgin_lat",
            "origin_lon",
            "trip_image",
        ]

    def clean(self):
        """Performs custom validation to ensure that the trip details are consistent."""
        cleaned_data = super().clean()
        departure_time = cleaned_data.get("departure_time")
        expected_arrival_time = cleaned_data.get("expected_arrival_time")
        origin = cleaned_data.get("origin")
        destination = cleaned_data.get("destination")
        to_address = cleaned_data.get("to_address")
        from_address = cleaned_data.get("from_address")
        budget = cleaned_data.get("budget")
        slots_available = cleaned_data.get("slots_available")

        if origin == destination:
            raise forms.ValidationError("Origin and destination cannot be the same.")

        if from_address == to_address:
            raise forms.ValidationError("From and To addresses cannot be the same.")

        if budget is not None and budget < 0:
            raise forms.ValidationError("Budget cannot be negative.")

        if slots_available is not None and slots_available <= 0:
            raise forms.ValidationError("Slots available must be greater than zero.")

        if (
            departure_time
            and expected_arrival_time
            and expected_arrival_time <= departure_time
        ):
            raise forms.ValidationError(
                "Expected arrival time must be after departure time."
            )

        if departure_time and departure_time < timezone.now():
            raise forms.ValidationError("Departure time must be in the future.")

        if expected_arrival_time and expected_arrival_time <= timezone.now():
            raise forms.ValidationError("Expected arrival time must be in the future.")

        return cleaned_data


class TripFilterForm(forms.Form):
    passengers = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any"),
            ("1", "At least 1 seat"),
            ("2", "At least 2 seats"),
            ("3", "At least 3 seats"),
            ("4", "At least 4 seats"),
        ],
        widget=forms.Select(attrs={"class": "select"}),
    )
    budget = forms.IntegerField(
        required=False,
        initial=3,
    )

    age_group = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any"),
            ("18-25", "18-25"),
            ("26-35", "26-35"),
            ("36-45", "36-45"),
            ("46-60", "46-60"),
            ("60+", "60+"),
        ],
        widget=forms.Select(attrs={"class": "select"}),
    )
    gender = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any"),
            ("M", "Male"),
            ("F", "Female"),
        ],
        widget=forms.RadioSelect(attrs={"class": "radio radio-primary"}),
    )


class TravelCompanionForm(forms.Form):
    travel_bio = forms.CharField(widget=forms.Textarea, required=False)
    looking_for = forms.CharField(max_length=255, required=False)
    previous_experiences = forms.CharField(widget=forms.Textarea, required=False)


class CreateTripView(LoginRequiredMixin, CreateView):
    model = Trip
    form_class = TripCreateForm
    template_name = "rides/create_trip.html"

    def form_valid(self, form):
        """Creates a trip and initializes its membership and group chat."""
        print("Form is valid, setting organizer to:", self.request.user)
        form.instance.organizer = self.request.user
        form.instance.status = "upcoming"
        response = super().form_valid(form)
        TripMembership.objects.create(
            trip=self.object, user=self.request.user, status="accepted"
        )
        TripGroup.objects.create(trip=self.object, name=f"{self.object} Group")

        TripGroupMessage.objects.create(
            sender=self.request.user,
            group=self.object.tripgroup,
            activity=f"{self.request.user.username} created the trip.",
            is_system_message=True,
        )
        async_to_sync(get_channel_layer().group_send)(
            f"chat_{self.object.pk}",
            {
                "type": "trip_activity",
                "activity": f"{self.request.user.username} created the trip.",
            },
        )

        messages.success(self.request, "Trip created successfully!")
        return response

    def form_invalid(self, form):
        print("Form is invalid. Errors:", form.errors)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("trip_detail", kwargs={"pk": self.object.pk})


def auto_populate(request):
    query = request.GET.get("query", "")

    if query:
        results = autocomplete_location(query)
        return JsonResponse({"results": results})

    else:
        return JsonResponse({"results": []})


class TripDetailView(DetailView):
    model = Trip
    template_name = "rides/trip_detail.html"
    context_object_name = "trip"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_object()
        user = self.request.user

        if user.is_authenticated:
            context["is_member"] = TripMembership.objects.filter(
                trip=trip, user=user, status="accepted"
            ).exists()
            context["organizer"] = trip.organizer
            context["is_pending"] = TripMembership.objects.filter(
                trip=trip, user=user, status="pending"
            ).exists()

        return context


class TripListView(ListView):
    model = Trip
    template_name = "rides/trip_list.html"
    context_object_name = "trips"
    paginate_by = 2
    BUDGET_LIMITS = {
        1: 5000,
        2: 15000,
        3: 30000,
        4: 50000,
        5: 100000,
    }
    AGE_GROUPS = {
        "18-25": (18, 25),
        "26-35": (26, 35),
        "36-45": (36, 45),
        "46-60": (46, 60),
        "60+": (60, 100),
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        origin = self.request.GET.get("origin")
        destination = self.request.GET.get("destination")
        departure = self.request.GET.get("departure")
        tags = self.request.GET.getlist("tag")
        languages = self.request.GET.getlist("language")
        self.search_title = "Available Trips"

        form = TripFilterForm(self.request.GET)
        if form.is_valid():
            passengers = form.cleaned_data.get("passengers")
            budget = form.cleaned_data.get("budget")
            age_group = form.cleaned_data.get("age_group")
            gender = form.cleaned_data.get("gender")

        if origin:
            queryset = queryset.filter(origin__icontains=origin)
        if destination:
            queryset = queryset.filter(destination__icontains=destination)
        if departure:
            queryset = queryset.filter(departure_time__date=departure)
        if passengers:
            queryset = queryset.filter(slots_available__gte=passengers)
        if tags:
            queryset = queryset.filter(tag__name__in=tags)
        if languages:
            queryset = queryset.filter(
                organizer__profile__languages_spoken__name__in=languages
            )
        if budget:
            try:
                budget_limit = self.BUDGET_LIMITS.get(int(budget), 100000)
                queryset = queryset.filter(budget__lte=budget_limit).distinct()

            except ValueError:
                pass

        if age_group:
            age_range = self.AGE_GROUPS.get(age_group)
            if age_range:
                min_age, max_age = age_range
                queryset = queryset.filter(
                    organizer__profile__age__gte=min_age,
                    organizer__profile__age__lte=max_age,
                )

        if gender:
            queryset = queryset.filter(organizer__profile__gender=gender)

        if origin and destination:
            self.search_title = f"From {origin} to {destination}"
        elif origin:
            self.search_title = f"Starting from {origin}"
        elif destination:
            self.search_title = f"Going to {destination}"

        return queryset

    def get_template_names(self):
        """Serves partial templates for HTMX requests."""
        if self.request.headers.get("HX-Request"):
            return ["rides/partials/trip_cards.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["popular_tags"] = Trip.tag.most_common()[:5]
        context["languages"] = Language.objects.annotate(
            num_users=Count("profile")
        ).order_by("-num_users")[:6]
        context["filter_form"] = TripFilterForm(self.request.GET)
        context["budget_limits"] = self.BUDGET_LIMITS
        if self.request.headers.get("HX-Request"):
            context["search_title"] = self.search_title
        return context


@require_POST
@login_required
def join_trip_request(request, pk):
    """Process User Request to Join a Trip."""
    trip = Trip.objects.get(pk=pk)
    existing_membership = TripMembership.objects.filter(
        trip=trip, user=request.user
    ).first()
    is_full = trip.slots_available <= trip.get_accepted_members().count()

    if trip.organizer == request.user:
        messages.error(request, "You are already the organizer of this trip.")
        return redirect("trip_detail", pk=pk)

    if is_full:
        messages.error(request, "This trip is already full. You cannot join.")
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
        async_to_sync(get_channel_layer().group_send)(
            f"notifications_{trip.organizer.id}",
            {
                "type": "send_notification",
                "message": f"{request.user.username} has requested to join the trip.",
            },
        )

    return redirect("trip_detail", pk=pk)


@require_POST
@login_required
def cancel_trip_joining_request(request, pk):
    trip = Trip.objects.get(pk=pk)
    membership = TripMembership.objects.filter(trip=trip, user=request.user).first()

    if not membership:
        messages.error(request, "You are not a member of this trip.")
        return redirect("trip_detail", pk=pk)

    if membership.status == "pending":
        membership.delete()
        messages.success(request, "Your request to join the trip has been cancelled.")

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
        context["pending_requests"] = (
            TripMembership.objects.filter(
                trip__organizer=self.request.user, status="pending"
            )
            .select_related("user", "trip")
            .order_by("-joined_at")
        )

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
    return redirect("home")


@require_POST
@login_required
def accept_request(request, pk):
    """Process Organizer's Acceptance of a User's Request to Join a Trip."""
    membership = TripMembership.objects.get(pk=pk)
    if membership.trip.organizer != request.user:
        messages.error(request, "You are not authorized to accept this request.")
        return HttpResponse(status=403)

    membership.status = "accepted"
    membership.save()
    group = TripGroup.objects.get(trip=membership.trip)
    group.save()
    TripGroupMessage.objects.create(
        sender=request.user,
        group=group,
        activity=f"{membership.user.username} has joined the trip.",
        is_system_message=True,
    )
    async_to_sync(get_channel_layer().group_send)(
        f"chat_{membership.trip.pk}",
        {
            "type": "trip_activity",
            "activity": f"{membership.user.username} has joined the trip.",
        },
    )
    async_to_sync(get_channel_layer().group_send)(
        f"notifications_{membership.user.id}",
        {
            "type": "send_notification",
            "message": f"Your request to join {membership.trip} has been accepted!",
        },
    )
    return HttpResponse(status=200)


@require_POST
@login_required
def reject_request(request, pk):
    """Process Organizer's Rejection of a User's Request to Join a Trip."""
    membership = TripMembership.objects.get(pk=pk)
    if membership.trip.organizer != request.user:
        messages.error(request, "You are not authorized to reject this request.")
        return HttpResponse(status=403)

    membership.status = "rejected"
    membership.save()
    async_to_sync(get_channel_layer().group_send)(
        f"notifications_{membership.user.id}",
        {
            "type": "send_notification",
            "message": f"Your request to join {membership.trip} has been rejected.",
        },
    )
    return HttpResponse(status=200)


class ChatView(LoginRequiredMixin, DetailView):
    model = TripGroup
    template_name = "rides/trip_chat.html"
    context_object_name = "tripgroup"

    def is_member(self, user):
        return TripMembership.objects.filter(
            trip=self.object.trip, user=user, status="accepted"
        ).exists()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.is_member(request.user):
            return redirect("trip_detail", pk=self.object.trip.pk)
        return super().get(request, *args, **kwargs)


@login_required
def advance_trip_status(request, pk):
    trip = Trip.objects.get(pk=pk)
    if trip.organizer != request.user:
        return HttpResponse(status=403)

    if trip.status == "completed":
        return HttpResponse(status=400)

    new_status = trip.next_status()

    if (
        new_status == "completed"
        and timezone.now() < trip.expected_arrival_time + trip.get_duration_timedelta()
    ):
        return HttpResponse(
            "Cannot complete trip before expected arrival time.", status=400
        )

    trip.status = new_status
    trip.save()

    message_updates = {
        "upcoming": "The trip is now upcoming. Get ready for the adventure!",
        "ongoing": "The trip is now ongoing. Enjoy the ride!",
        "completed": "The trip has been completed. Hope you had a great time!",
    }

    TripGroupMessage.objects.create(
        sender=request.user,
        group=trip.tripgroup,
        activity=message_updates.get(
            new_status,
        ),
        is_system_message=True,
    )
    async_to_sync(get_channel_layer().group_send)(
        f"chat_{trip.pk}",
        {
            "type": "trip_activity",
            "activity": message_updates.get(
                new_status,
            ),
        },
    )

    return render(
        request,
        "rides/partials/trip_status.html",
        context={"tripgroup": trip.tripgroup},
    )


class InboxView(LoginRequiredMixin, TemplateView):
    template_name = "rides/inbox.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversations = Conversation.objects.filter(
            participants=self.request.user
        ).order_by("-created_at")

        for conversation in conversations:
            other_participant = conversation.get_other_participant(self.request.user)
            conversation.other = other_participant
        context["dm_conversations"] = conversations
        context["joined_trips"] = (
            TripMembership.objects.filter(user=self.request.user, status="accepted")
            .select_related("trip", "trip__organizer")
            .order_by("-joined_at")
        )
        return context


class StartChatView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user = User.objects.get(pk=pk)
        conversation = (
            Conversation.objects.filter(participants=user)
            .filter(participants=request.user)
            .first()
        )
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(user, request.user)
            conversation.save()
        return redirect("direct_chat", pk=conversation.pk)


class DirectChatView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = "rides/direct_chat.html"
    context_object_name = "conversation"

    def is_participant(self, user):
        return self.object.participants.filter(id=user.id).exists()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.is_participant(request.user):
            return redirect("inbox")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        other_participant = self.object.get_other_participant(self.request.user)
        context["other_user"] = other_participant
        return context
