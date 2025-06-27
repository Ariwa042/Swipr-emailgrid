from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from .forms import CustomUserCreationForm, CustomAuthenticationForm, PasswordChangeForm
from django.conf import settings

User = settings.AUTH_USER_MODEL


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in the user after registration
            messages.success(request, 'Registration successful! Welcome to EmailGrid.')
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # username field is used for email
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('accounts:profile')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """User logout view"""
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile view"""
    # Get the user's active subscription
    from payments.models import Subscription
    current_subscription = Subscription.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gt=timezone.now()
    ).first()
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'current_subscription': current_subscription
    })


@login_required
def change_password_view(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})