from django.urls import path
from . import views 

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("profile/", views.profile, name="profile"),
    path("verify/<int:pk>/<str:token>/", views.verify_account, name="verify_account"),
]

