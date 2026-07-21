from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Automatically creates a Profile instance whenever a new User is created."""
    if created:
        Profile.objects.get_or_create(user=instance)
