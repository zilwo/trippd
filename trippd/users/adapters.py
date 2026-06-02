from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from .models import User
from django.contrib import messages
from django.shortcuts import redirect

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        print("PRE SOCIAL LOGIN CALLED")
        if sociallogin.is_existing:
            return
        
        email = sociallogin.user.email
        
        if email:
            user_exists = User.objects.filter(email=email).exists()
            if user_exists:
                messages.error(request, "An account with this email already exists. Please log in using your email and password.")
                raise ImmediateHttpResponse(redirect("login"))
