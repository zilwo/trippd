from django.db import models
from users.models import User
from taggit.managers import TaggableManager
from datetime import timedelta


class Trip(models.Model):
    """Represents a trip which users can request to join."""

    organizer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="organized_trips"
    )
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    from_address = models.CharField(max_length=255)
    to_address = models.CharField(max_length=255)
    departure_time = models.DateTimeField()
    expected_arrival_time = models.DateTimeField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    slots_available = models.PositiveIntegerField()
    duration_value = models.PositiveIntegerField(null=True, blank=True)
    duration_unit = models.CharField(
        max_length=50,
        choices=[
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
        ],
    )
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

    def get_accepted_members(self):
        return self.memberships.filter(status="accepted")

    def __str__(self):
        return f"{self.origin} to {self.destination}"

    def next_status(self):
        status_flow = {
            "planning": "upcoming",
            "upcoming": "ongoing",
            "ongoing": "completed",
        }
        return status_flow.get(self.status, self.status)

    def get_duration_timedelta(self):
        """Returns a timedelta object based on the duration_value and duration_unit."""

        if self.duration_value is None or self.duration_unit is None:
            return timedelta(0)

        if self.duration_unit == "days":
            return timedelta(days=self.duration_value)
        elif self.duration_unit == "weeks":
            return timedelta(weeks=self.duration_value)
        elif self.duration_unit == "months":
            return timedelta(days=self.duration_value * 30)
        else:
            return timedelta(0)


class TripMembership(models.Model):
    """Tracks a user's membership status for a trip."""

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="trip_memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
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
