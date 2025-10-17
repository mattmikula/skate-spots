"""Frontend HTML views for authentication."""

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit

from .forms import LoginForm, RegisterForm


@ratelimit(key="ip", rate="5/m", method="POST")
def login_page(request):
    """Display login page."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                form.add_error(None, "Incorrect username or password")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@ratelimit(key="ip", rate="5/m", method="POST")
def register_page(request):
    """Display registration page."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    """Logout user and redirect to home."""
    logout(request)
    return redirect("home")
