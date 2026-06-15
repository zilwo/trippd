from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager


class User(AbstractUser):
    """Custom user model with email verification."""

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(blank=True, region="IN")
    is_verified = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class Language(models.Model):
    """Spoken languages for user profiles."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    """Stores Profile Information."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    location = models.CharField(max_length=255, blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    interests = TaggableManager(blank=True)
    languages_spoken = models.ManyToManyField(Language, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
        blank=True,
    )
    age = models.PositiveIntegerField(null=True, blank=True)

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
    """Model representing a rating given by one user to another for a specific trip."""

    rater = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="given_ratings"
    )
    ratee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_ratings"
    )
    trip = models.ForeignKey(
        "rides.Trip", on_delete=models.CASCADE, related_name="ratings"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        unique_together = ("rater", "ratee", "trip")

    def __str__(self):
        return f"{self.rater.email} rated {self.ratee.email} for {self.trip}"
