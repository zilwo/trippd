from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(blank=True, region="IN")
    is_verified = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    def __str__(self):
        return self.email
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    trips_completed = models.PositiveIntegerField(default=0)
    hobbies = TaggableManager(blank=True)
    

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def average_rating(self):
        ratings = self.user.received_ratings.all()
        if ratings.exists():
            return sum(r.rating for r in ratings) / ratings.count()
        return 0
    
    def total_ratings(self):
        return self.user.received_ratings.count()
    
class Rating(models.Model):
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="given_ratings")
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_ratings")
    trip = models.ForeignKey("rides.Trip", on_delete=models.CASCADE, related_name="ratings")
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])


    class Meta:
        unique_together = ("rater", "ratee", "trip")

    def __str__(self):
        return f"{self.rater.email} rated {self.ratee.email} for {self.trip}"
    
    