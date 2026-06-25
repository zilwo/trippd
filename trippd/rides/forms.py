from django import forms
from django.utils import timezone
from .models import Trip

BUDGET_LIMITS = {
    0: "Any",
    1: 5000,
    2: 15000,
    3: 30000,
    4: 50000,
    5: 100000,
}
AGE_GROUPS = {
    "18-25": (18, 25),
    "26-35": (26, 35),
    "36-45": (36, 45),
    "46-60": (46, 60),
    "60+": (60, 100),
}


class TripCreateForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "origin",
            "destination",
            "description",
            "from_address",
            "to_address",
            "departure_time",
            "expected_finish_time",
            "budget",
            "slots_available",
            "tag",
            "trip_image",
        ]

    def clean(self):
        """Performs custom validation to ensure that the trip details are consistent."""
        cleaned_data = super().clean()
        departure_time = cleaned_data.get("departure_time")
        expected_finish_time = cleaned_data.get("expected_finish_time")
        origin = cleaned_data.get("origin")
        destination = cleaned_data.get("destination")
        to_address = cleaned_data.get("to_address")
        from_address = cleaned_data.get("from_address")
        budget = cleaned_data.get("budget")
        slots_available = cleaned_data.get("slots_available")

        if not origin:
            raise forms.ValidationError("Origin is required.")
        if not destination:
            raise forms.ValidationError("Destination is required.")
        if not from_address:
            raise forms.ValidationError("From address is required.")
        if not to_address:
            raise forms.ValidationError("To address is required.")
        if not departure_time:
            raise forms.ValidationError("Departure time is required.")
        if not expected_finish_time:
            raise forms.ValidationError("Expected finish time is required.")
        if not budget:
            raise forms.ValidationError("Budget is required.")
        if not slots_available:
            raise forms.ValidationError("Slots available is required.")

        if origin == destination:
            raise forms.ValidationError("Origin and destination cannot be the same.")

        if from_address == to_address:
            raise forms.ValidationError("From and To addresses cannot be the same.")

        if budget is not None and budget < 0:
            raise forms.ValidationError("Budget cannot be negative.")

        if slots_available is not None and slots_available <= 0:
            raise forms.ValidationError("Slots available must be greater than zero.")

        if (
            departure_time
            and expected_finish_time
            and expected_finish_time <= departure_time
        ):
            raise forms.ValidationError(
                "Expected finish time must be after departure time."
            )

        if departure_time and departure_time < timezone.now():
            raise forms.ValidationError("Departure time must be in the future.")

        if expected_finish_time and expected_finish_time <= timezone.now():
            raise forms.ValidationError("Expected finish time must be in the future.")

        return cleaned_data


class CompanionTravelForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "to_address",
            "destination",
            "description",
            "slots_available",
            "budget",
            "tag",
            "looking_for",
            "previous_experiences",
            "trip_image",
        ]

    def clean(self):
        cleaned_data = super().clean()
        destination = cleaned_data.get("destination")
        budget = cleaned_data.get("budget")
        slots_available = cleaned_data.get("slots_available")
        looking_for = cleaned_data.get("looking_for")

        if not destination:
            raise forms.ValidationError(
                "Destination is required for companion requests."
            )
        if not looking_for:
            raise forms.ValidationError(
                "Please specify what you are looking for in a travel companion."
            )
        if budget is not None and budget < 0:
            raise forms.ValidationError("Budget cannot be negative.")

        if slots_available is not None and slots_available <= 0:
            raise forms.ValidationError("Slots available must be greater than zero.")

        return cleaned_data


class TripFilterForm(forms.Form):
    passengers = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any"),
            ("1", "At least 1 seat"),
            ("2", "At least 2 seats"),
            ("3", "At least 3 seats"),
            ("4", "At least 4 seats"),
        ],
        widget=forms.Select(attrs={"class": "select"}),
    )
    budget = forms.IntegerField(
        required=False,
        initial=3,
    )

    age_group = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any"),
            ("18-25", "18-25"),
            ("26-35", "26-35"),
            ("36-45", "36-45"),
            ("46-60", "46-60"),
            ("60+", "60+"),
        ],
        widget=forms.Select(attrs={"class": "select"}),
    )
    gender = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any"),
            ("M", "Male"),
            ("F", "Female"),
        ],
        widget=forms.RadioSelect(attrs={"class": "radio radio-primary"}),
    )
