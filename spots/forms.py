"""Forms for skate spots."""

from django import forms

from .models import SkateSpot


class SkateSpotForm(forms.ModelForm):
    """Form for creating and editing skate spots."""

    class Meta:
        model = SkateSpot
        fields = [
            "name",
            "description",
            "spot_type",
            "difficulty",
            "latitude",
            "longitude",
            "address",
            "city",
            "country",
            "is_public",
            "requires_permission",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
            "spot_type": forms.Select(attrs={"class": "form-input"}),
            "difficulty": forms.Select(attrs={"class": "form-input"}),
            "latitude": forms.NumberInput(
                attrs={"class": "form-input", "step": "0.000001"}
            ),
            "longitude": forms.NumberInput(
                attrs={"class": "form-input", "step": "0.000001"}
            ),
            "address": forms.TextInput(attrs={"class": "form-input"}),
            "city": forms.TextInput(attrs={"class": "form-input"}),
            "country": forms.TextInput(attrs={"class": "form-input"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "requires_permission": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
        }
