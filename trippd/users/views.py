from django import forms
from django.http import Http404
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from .utils.tokens import AccountActivationTokenGenerator
from .models import Language, Notification, User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile, Rating
from django.db.models import Count
from rides.models import Trip


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User.profile.related.related_model
        fields = [
            "bio",
            "profile_picture",
            "location",
            "interests",
            "languages_spoken",
            "gender",
            "age",
            "instagram",
        ]


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "username", "password1", "password2")


class CustomLoginView(LoginView):
    template_name = "users/login.html"
    next_page = "discover"


class CustomLogoutView(LogoutView):
    next_page = "discover"


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
def edit_profile(request):
    """Updates user profile interests are expected to be a comma-separated string"""
    languages = Language.objects.all()
    gender_choices = Profile._meta.get_field("gender").choices
    if request.method == "POST":
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            print("form tags cleaned data:", form.cleaned_data.get("interests"))
            form.save()

            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

            return redirect("profile", username=request.user.username)

    return render(
        request,
        "users/edit_profile.html",
        context={"languages": languages, "gender_choices": gender_choices},
    )


class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/profile.html"
    context_object_name = "profile_user"
    slug_url_kwarg = "username"
    slug_field = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile_user = self.get_object()

        context["profile"] = profile_user.profile
        context["is_own_profile"] = self.request.user == profile_user
        completed_trips = Trip.objects.filter(
            status="completed",
            memberships__user=profile_user,
        ).order_by("-departure_time")

        rating_counts = (
            Rating.objects.filter(ratee=profile_user)
            .values("rating")
            .annotate(count=Count("id"))
        )

        distribution = {i: 0 for i in range(1, 6)}

        for item in rating_counts:
            distribution[item["rating"]] = item["count"]

        total_reviews = sum(distribution.values())

        rating_distribution = []

        for star in range(5, 0, -1):
            count = distribution[star]
            percent = (count / total_reviews * 100) if total_reviews else 0

            rating_distribution.append(
                {
                    "star": star,
                    "count": count,
                    "percent": round(percent),
                }
            )

        context["rating_distribution"] = rating_distribution
        context["total_reviews"] = total_reviews
        context["completed_trips"] = completed_trips
        context["completed_trip_count"] = completed_trips.count()

        return context


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "rides/partials/notification_list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        return self.request.user.notifications.order_by("-created_at").order_by(
            "isread"
        )[:20]


@login_required
def notification_redirect(request, notification_id):
    """Redirects to the link associated with a notification and marks it as read. yes this is a GET request, but we are marking the notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.isread = True
        notification.save()
        print(
            f"Redirecting user {request.user.username} to {notification.link} for notification {notification_id}"
        )
        return redirect(notification.link)
    except Notification.DoesNotExist:
        raise Http404(
            "Notification does not exist or you do not have permission to view it."
        )


@login_required
def mark_notification_as_read(request, notification_id):
    """Marks a specific notification as read."""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.isread = True
        notification.save()
        print(
            f"Marked notification {notification_id} as read for user {request.user.username}"
        )
        return render(
            request,
            "rides/partials/notification_item.html",
            {"notification": notification},
        )
    except Notification.DoesNotExist:
        raise Http404(
            "Notification does not exist or you do not have permission to modify it."
        )
