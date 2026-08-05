from datetime import timedelta
from django.db import models
from .utils.formatdelta import format_delta
from users.models import User
from taggit.managers import TaggableManager


class Trip(models.Model):
    """Represents a ride/trip which users can request to join."""

    trip_type = models.CharField(
        max_length=20,
        choices=[("ride-sharing", "Ride Sharing"), ("trip", "Trip")],
        default="trip",
    )
    organizer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="organized_trips"
    )
    destination = models.CharField(max_length=255)
    origin = models.CharField(max_length=255, blank=True)
    origin_lat = models.FloatField(null=True, blank=True)
    origin_lon = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True)
    from_address = models.CharField(max_length=255, blank=True)
    to_address = models.CharField(max_length=255, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    expected_finish_time = models.DateTimeField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    slots_available = models.PositiveIntegerField()
    tag = TaggableManager(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("planning", "Planning"),
            ("upcoming", "Upcoming"),
            ("ongoing", "Ongoing"),
            ("completed", "Completed"),
        ],
        default="planning",
    )
    trip_image = models.ImageField(
        upload_to="trip_images/",
        blank=True,
        null=True,
        default="trip_images/default.jpg",
    )
    looking_for = models.CharField(
        max_length=255,
        blank=True,
    )
    previous_experiences = models.TextField(blank=True)

    def get_accepted_members(self):
        return self.memberships.filter(status="accepted")

    def __str__(self):
        return f"{self.origin if self.origin else 'TBD'} to {self.destination}"

    def next_status(self):
        status_flow = {
            "planning": "upcoming",
            "upcoming": "ongoing",
            "ongoing": "completed",
        }
        return status_flow.get(self.status, self.status)

    def trip_duration(self):
        if self.departure_time and self.expected_finish_time:
            duration = self.expected_finish_time - self.departure_time
            return format_delta(duration, trip_type=self.trip_type)
        return None

    def is_valid_trip(self):
        """Check all required fields are filled for a valid trip."""
        print(
            "Checking trip validity:",
            self.origin,
            self.destination,
            self.departure_time,
            self.expected_finish_time,
            self.budget,
            self.slots_available,
        )
        return all(
            [
                self.origin,
                self.destination,
                self.departure_time,
                self.expected_finish_time,
                self.budget,
                self.slots_available,
            ]
        )


class TripMembership(models.Model):
    """Tracks a user's membership status for a trip."""

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="trip_memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(
        blank=True, default="I am interested in joining this trip!"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Onboard"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["trip", "user"], name="unique_trip_user")
        ]

    def __str__(self):
        return f"{self.user.username} in {self.trip}"


class TripGroup(models.Model):
    """Chat group associated with a trip."""

    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=255)
    whats_app_group_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class TripGroupMessage(models.Model):
    """Message or activity updates posted in a trip group chat."""

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    group = models.ForeignKey(
        TripGroup, on_delete=models.CASCADE, related_name="chat_messages"
    )
    body = models.TextField(max_length=500)
    send_at = models.DateTimeField(auto_now_add=True)
    activity = models.CharField(max_length=255, blank=True)
    is_system_message = models.BooleanField(default=False)

    def __str__(self):
        return f"Message by {self.sender.username} in {self.group.name}"


class Conversation(models.Model):
    """Represents a private conversation between two users."""

    participants = models.ManyToManyField(User, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation between {', '.join(p.username for p in self.participants.all())}"

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()


class ConversationMessage(models.Model):
    """Message sent within a private conversation."""

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField(max_length=1000)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Message by {self.sender.username} in conversation {self.conversation.id}"
        )


class Place(models.Model):
    """Represents a place associated with an activity."""

    place_id = models.CharField(max_length=255, unique=True)

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    region = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    types = models.CharField(max_length=100, blank=True, null=True)
    map_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    featured = models.BooleanField(default=False)
    highlights = models.TextField(blank=True)
    best_time_to_visit = models.CharField(max_length=255, blank=True)
    best_for = models.CharField(max_length=255, blank=True)
    viewport_low_lat = models.FloatField(null=True, blank=True)
    viewport_low_lng = models.FloatField(null=True, blank=True)
    viewport_high_lat = models.FloatField(null=True, blank=True)
    viewport_high_lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.address

    def best_for_list(self):
        if not self.best_for:
            return []
        return [label.strip() for label in self.best_for.split(",") if label.strip()]


class Activity(models.Model):
    """Represents an activity at a place."""

    class Category(models.TextChoices):
        FOOD = "food", "Food & Drinks"
        SIGHTSEEING = "sightseeing", "Sightseeing"
        NATURE = "nature", "Nature & Outdoors"
        SHOPPING = "shopping", "Shopping"
        ENTERTAINMENT = "entertainment", "Entertainment"
        SPORTS = "sports", "Sports & Adventure"
        NIGHTLIFE = "nightlife", "Nightlife"
        RELAXATION = "relaxation", "Relaxation"
        STAY = "stay", "Stay"
        OTHER = "other", "Other"

    organizer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="organized_activities"
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name="activities", null=True, blank=True
    )
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=500, blank=True)
    start_time = models.DateTimeField()
    duration = models.DurationField(default=timedelta(minutes=30))
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    place = models.ForeignKey(
        Place, on_delete=models.PROTECT, related_name="activities"
    )
    max_participants = models.PositiveIntegerField(default=10)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        null=True,
        blank=True,
        default=Category.OTHER,
    )

    activity_image = models.ImageField(
        upload_to="activity_images/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.title} organized by {self.organizer.username}"

    def formatted_duration(self):
        total_seconds = int(self.duration.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes = remainder // 60

        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hr{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} min")

        return " ".join(parts) or "0 min"
