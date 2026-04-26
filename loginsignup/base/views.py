from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm  # Import your custom form

def home(request):
    return render(request, "home.html", {})

def authView(request):
    
    if request.user.is_authenticated:
        return redirect('base:home')
    
    if request.method == "POST":
        form = SignUpForm(request.POST)  # Use SignUpForm instead of UserCreationForm
        
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('base:home')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = SignUpForm()  # Use SignUpForm instead of UserCreationForm
    
    return render(request, "registration/signup.html", {
        "form": form
    })

def loginView(request):
    if request.user.is_authenticated:
        return redirect('base:home')
    
    if request.method == "POST":
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Try to authenticate with username first
        user = authenticate(username=username_or_email, password=password)
        
        # If authentication failed, try with email
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('base:home')
        else:
            messages.error(request, 'Invalid username/email or password.')
            form = AuthenticationForm()
    else:
        form = AuthenticationForm()
    
    return render(request, "registration/login.html", {"form": form})

@login_required
def profile(request):
    context = {
        'user': request.user
    }
    return render(request, 'profile.html', context)

def edit_profile(request):
    if request.method == "POST":
        user = request.user
        
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Validate email
        email_error = None
        if email and User.objects.filter(email=email).exclude(id=user.id).exists():
            email_error = 'This email address is already in use by another account.'
        
        if not email_error:
            # Update user information
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('base:profile')
        else:
            messages.error(request, email_error)
    
    context = {
        'user': request.user
    }
    return render(request, 'edit_profile.html', context)

def logoutView(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('base:home')


def aboutus(request):
    context = {
    
    }
    return render(request, 'aboutus.html', context)