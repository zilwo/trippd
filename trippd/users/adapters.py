from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from .models import User
from django.contrib import messages
from django.shortcuts import redirect


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to handle social account logins, ensuring that users with existing email addresses are prompted to log in instead of creating duplicate accounts."""

    def pre_social_login(self, request, sociallogin):
        print("PRE SOCIAL LOGIN CALLED")
        if sociallogin.is_existing:
            return

        email = sociallogin.user.email

        if email:
            user_exists = User.objects.filter(email=email).exists()
            if user_exists:
                messages.error(
                    request,
                    "An account with this email already exists. Please log in using your email and password.",
                )
                raise ImmediateHttpResponse(redirect("login"))

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.is_verified = True
        user.save()
        return user
