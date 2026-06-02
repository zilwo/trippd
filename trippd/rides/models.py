from django.db import models
from users.models import User
from taggit.managers import TaggableManager


# Create your models here.

class Trip(models.Model):
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_trips")
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    from_address = models.CharField(max_length=255,default="Undecided") 
    to_address = models.CharField(max_length=255,default="Undecided")
    departure_time = models.DateTimeField()
    expected_arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    slots_available = models.PositiveIntegerField()
    duration = models.CharField(max_length=50,default="1 week")
    tag = TaggableManager(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)


    def get_members_count(self):
        return self.memberships.filter(status="accepted").count()


    def __str__(self):
        return f"{self.origin} to {self.destination} on {self.departure_time.strftime("%Y-%m-%d %H:%M")}"
    
class TripMembership(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trip_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected")
    ], default="pending")

    def __str__(self):
        return f"{self.user.email} in {self.trip}"
    

