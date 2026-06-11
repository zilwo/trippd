from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from .utils.tokens import AccountActivationTokenGenerator
from .models import User
from django.contrib.auth.decorators import login_required


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "username", "password1", "password2")


class CustomLoginView(LoginView):
    template_name = "users/login.html"
    next_page = "home"


class CustomLogoutView(LogoutView):
    next_page = "home"


class SignUpView(CreateView):
    template_name = "users/signup.html"
    success_url = reverse_lazy("login")
    form_class = SignupForm

    def form_valid(self, form):
        """Creates a new user, generates an activation token, and sends a verification email."""
        user = form.save()
        print(f"New user created: {user.email}")

        token = AccountActivationTokenGenerator().make_token(user)
        verification_link = self.request.build_absolute_uri(
            reverse_lazy(
                "verify_account",
                kwargs={"pk": user.pk, "token": token},
            )
        )

        send_mail(
            subject="Welcome!",
            message=f"Hi {user.email}, Here is your activation link: {verification_link}",
            from_email="noreply@trippd.com",
            recipient_list=[user.email],
        )

        return redirect(self.success_url)


def verify_account(request, pk, token):
    """Verifies the user's account using the provided token"""
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        user = None

    if user is not None and AccountActivationTokenGenerator().check_token(user, token):
        user.is_verified = True
        user.save()
        return redirect("login")
    else:
        print("Invalid verification attempt for user:", user)
        return render(request, "users/activation_invalid.html")


@login_required
def profile(request):
    return render(request, "users/profile.html")


@login_required
def edit_profile(request):
    """Updates user profile Hobbies are expected to be a comma-separated string"""
    if request.method == "POST":
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        bio = request.POST.get("bio", "")
        hobbies = request.POST.get("hobbies", "")
        profile_picture = request.FILES.get("profile_picture")

        profile = request.user.profile

        request.user.first_name = first_name
        request.user.last_name = last_name

        profile.bio = bio
        if profile_picture:
            profile.profile_picture = profile_picture
        if hobbies:
            tags = [hobby.strip() for hobby in hobbies.split(",") if hobby.strip()]
            profile.hobbies.set(tags)
        request.user.save()
        profile.save()

        return redirect("profile")

    return render(request, "users/edit_profile.html")
