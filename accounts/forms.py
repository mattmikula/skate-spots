"""Forms for user authentication."""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class LoginForm(forms.Form):
    """Form for user login."""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Username"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Password"})
    )


class RegisterForm(UserCreationForm):
    """Form for user registration."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "Email"}),
    )

    class Meta:
        model = User
        fields = ("email", "username", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input", "placeholder": "Username"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": "form-input", "placeholder": "Password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-input", "placeholder": "Confirm Password"}
        )
