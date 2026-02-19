from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import CustomUserCreationForm
from .forms import CustomUserProfileForm

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60


def _get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _login_attempt_keys(username, ip_address):
    safe_username = (username or '').strip().lower()
    return (
        f'login_attempts:{ip_address}:{safe_username}',
        f'login_lock_until:{ip_address}:{safe_username}',
    )


# Create your views here.
def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account was created successfully!')
            return redirect("login")  # Ensure "login" corresponds to a valid URL name
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        ip_address = _get_client_ip(request)
        attempts_key, lock_key = _login_attempt_keys(username, ip_address)

        lock_until = cache.get(lock_key)
        if lock_until and lock_until > timezone.now().timestamp():
            remaining = int(lock_until - timezone.now().timestamp())
            wait_minutes = max(1, remaining // 60)
            messages.error(request, f"Too many failed attempts. Try again in about {wait_minutes} minute(s).")
            return render(request, 'accounts/login.html')

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            cache.delete(attempts_key)
            cache.delete(lock_key)
            return redirect("task_list")
        else:
            attempts = cache.get(attempts_key, 0) + 1
            cache.set(attempts_key, attempts, LOGIN_LOCKOUT_SECONDS)
            if attempts >= MAX_LOGIN_ATTEMPTS:
                lock_until_timestamp = timezone.now().timestamp() + LOGIN_LOCKOUT_SECONDS
                cache.set(lock_key, lock_until_timestamp, LOGIN_LOCKOUT_SECONDS)
                messages.error(request, "Too many failed login attempts. Account access temporarily locked.")
            else:
                remaining_tries = MAX_LOGIN_ATTEMPTS - attempts
                messages.error(request, f"Invalid username or password. {remaining_tries} attempt(s) left before temporary lock.")
            return render(request, 'accounts/login.html')
    return render(request, 'accounts/login.html')

# if a user is not logged in our login_required decorator will redirect back
#to the login page
# else we allow user to see the message
@login_required
def home_view(request):
    return redirect("task_list")

@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("login")  # Ensure "login" corresponds to a valid URL name


@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = CustomUserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = CustomUserProfileForm(instance=user)
    return render(request, "accounts/profile.html", {"form": form})
