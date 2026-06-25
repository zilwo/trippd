from turtle import mode

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

from users.models import Language, User, Notification
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
from .forms import (
    TripCreateForm,
    CompanionTravelForm,
    TripFilterForm,
    BUDGET_LIMITS,
    AGE_GROUPS,
)


def home(request):
    return render(request, "rides/home.html")


def auto_populate(request):
    query = request.GET.get("query", "")

    if query:
        results = autocomplete_location(query)
        return JsonResponse({"results": results})

    else:
        return JsonResponse({"results": []})


class CreateTripView(LoginRequiredMixin, CreateView):
    model = Trip
    template_name = "rides/create_trip.html"

    def form_valid(self, form):
        """Creates a trip which can be a planned trip or a non-planned trip and initializes the membership and group."""
        print("Form is valid, setting organizer to:", self.request.user)
        form.instance.organizer = self.request.user
        if self.mode == "companion":
            form.instance.status = "planning"
            print("image is ", form.instance.trip_image)
            print(
                "Creating a companion travel request with status 'planning'",
                form.instance,
            )
        else:
            form.instance.status = "upcoming"
            print("Creating a planned trip with status 'upcoming'", form.instance)
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

    def get_form_class(self):
        """Determines which form to use"""
        self.mode = self.request.POST.get("creation_mode", "trip")
        if self.mode == "companion":
            return CompanionTravelForm
        return TripCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["creation_mode"] = self.mode
        return context

    def get_success_url(self):
        return reverse("trip_detail", kwargs={"pk": self.object.pk})


class EditTripView(LoginRequiredMixin, UpdateView):
    model = Trip
    template_name = "rides/create_trip.html"

    def get_queryset(self):
        return Trip.objects.filter(organizer=self.request.user)

    def get_success_url(self):
        return reverse("trip_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        print("Form is valid, updating trip:", form.instance.trip_image)
        response = super().form_valid(form)
        print("Trip updated successfully.")
        return response

    def form_invalid(self, form):
        print("Form is invalid. Errors:", form.errors)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.status == "planning":
            context["is_companion_edit"] = True
        return context

    def get_form_class(self):
        if self.object.status == "planning":
            return CompanionTravelForm
        return TripCreateForm


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
            if len(destination) >= 3:
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
                budget_limit = self.BUDGET_LIMITS.get(budget, 100000)
                queryset = (
                    queryset.filter(budget__lte=budget_limit)
                    .distinct()
                    .order_by("-budget")
                )

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

        return queryset.filter(status="upcoming").order_by("-departure_time")

    def get_template_names(self):
        """Serves partial templates for HTMX requests."""
        if self.request.headers.get("HX-Request"):
            return ["rides/partials/trip_cards.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["urlmode"] = "trip_list"

        if not self.request.headers.get("HX-Request"):
            ongoing_trips = Trip.objects.filter(status="upcoming")
            context["popular_tags"] = Trip.tag.most_common(
                extra_filters={"taggit_taggeditem_items__object_id__in": ongoing_trips}
            )[:5]

            context["languages"] = Language.objects.annotate(
                num_users=Count("profile")
            ).order_by("-num_users")[:6]
            context["filter_form"] = TripFilterForm(self.request.GET)
            context["budget_limits"] = BUDGET_LIMITS
        else:
            context["search_title"] = self.search_title
        return context


class CompanionListView(ListView):
    model = Trip
    template_name = "rides/companion_list.html"
    context_object_name = "companion_requests"
    paginate_by = 4

    def get_queryset(self):
        queryset = super().get_queryset()

        destination = self.request.GET.get("destination")
        tags = self.request.GET.getlist("tag")
        languages = self.request.GET.getlist("language")
        form = TripFilterForm(self.request.GET)
        self.search_title = "Companion Travel Requests"

        if form.is_valid():
            passengers = form.cleaned_data.get("passengers")
            budget = form.cleaned_data.get("budget")
            age_group = form.cleaned_data.get("age_group")
            gender = form.cleaned_data.get("gender")

        if destination:
            if len(destination) >= 3:
                queryset = queryset.filter(destination__icontains=destination)

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
                budget_limit = BUDGET_LIMITS.get(budget, 100000)
                queryset = (
                    queryset.filter(budget__lte=budget_limit)
                    .distinct()
                    .order_by("-budget")
                )

            except ValueError:
                pass

        if age_group:
            age_range = AGE_GROUPS.get(age_group)
            if age_range:
                min_age, max_age = age_range
                queryset = queryset.filter(
                    organizer__profile__age__gte=min_age,
                    organizer__profile__age__lte=max_age,
                )

        if gender:
            queryset = queryset.filter(organizer__profile__gender=gender)

        if destination:
            self.search_title = f"Going to {destination}"

        queryset = queryset.filter(status="planning")
        return queryset.order_by("-created_at").distinct()

    def get_template_names(self):
        """Serves partial templates for HTMX requests."""

        if self.request.headers.get("HX-Request"):
            return ["rides/partials/companion_cards.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["urlmode"] = "companion_list"

        if not self.request.headers.get("HX-Request"):
            companion_trips = Trip.objects.filter(status="planning")
            context["popular_tags"] = Trip.tag.most_common(
                extra_filters={
                    "taggit_taggeditem_items__object_id__in": companion_trips
                }
            )[:5]
            context["budget_limits"] = BUDGET_LIMITS
            context["languages"] = Language.objects.annotate(
                num_users=Count("profile")
            ).order_by("-num_users")[:6]
            context["filter_form"] = TripFilterForm(self.request.GET)
        else:
            context["search_title"] = self.search_title
        return context


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
            context["duration"] = trip.trip_duration()

        return context


class CompanionDetailView(DetailView):
    model = Trip
    template_name = "rides/trip_detail.html"
    context_object_name = "trip"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companion_request = self.get_object()
        user = self.request.user

        if user.is_authenticated:
            context["is_member"] = TripMembership.objects.filter(
                trip=companion_request, user=user, status="accepted"
            ).exists()
            context["organizer"] = companion_request.organizer
            context["is_pending"] = TripMembership.objects.filter(
                trip=companion_request, user=user, status="pending"
            ).exists()

        return context


@require_POST
@login_required
def join_trip_request(request, pk):
    """Process User Request to Join a Trip."""
    trip = Trip.objects.get(pk=pk)
    join_message = request.POST.get("message", "").strip()

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
        if join_message:
            TripMembership.objects.create(
                trip=trip, user=request.user, message=join_message
            )
        else:
            TripMembership.objects.create(trip=trip, user=request.user)
        messages.success(
            request, "Your request to join the trip has been sent to the organizer."
        )

        request_message = (
            f"{request.user.username} has requested to join your trip: {trip}."
        )
        Notification.objects.create(
            user=trip.organizer,
            text=request_message,
            link=reverse("trip_dashboard") + "?tab=joinrequests",
        )
        print("we have th ", trip.organizer.notifications.filter(isread=False).count())

        async_to_sync(get_channel_layer().group_send)(
            f"notifications_{trip.organizer.id}",
            {
                "type": "send_notification",
                "message": request_message,
                "unread_count": trip.organizer.notifications.filter(
                    isread=False
                ).count(),
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


@require_POST
@login_required
def delete_trip(request, pk):
    trip = Trip.objects.get(pk=pk)
    if trip.organizer != request.user:
        messages.error(request, "You are not authorized to delete this trip.")
        return redirect("trip_detail", pk=pk)

    trip.delete()
    if trip.status == "planning":
        messages.success(request, "Companion travel request deleted successfully.")
        return redirect("companion_list")
    else:
        messages.success(request, "Trip deleted successfully.")
        return redirect("trip_list")


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

    acceptance_message = f"Your request to join {membership.trip} has been accepted!"
    Notification.objects.create(
        user=membership.user,
        text=acceptance_message,
        link=reverse("trip_chat", kwargs={"pk": membership.trip.pk}),
    )
    async_to_sync(get_channel_layer().group_send)(
        f"notifications_{membership.user.id}",
        {
            "type": "send_notification",
            "message": acceptance_message,
            "unread_count": membership.user.get_unread_notification_count(),
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
            "unread_count": membership.user.get_unread_notification_count(),
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

    expected_finish_time = trip.expected_finish_time
    if expected_finish_time and timezone.now() < expected_finish_time:
        return HttpResponse(
            "Cannot advance trip status before expected finish time.", status=400
        )

    new_status = trip.next_status()

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
