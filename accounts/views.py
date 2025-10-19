from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .forms import CustomLoginForm, CustomUserCreationForm

@require_http_methods(["GET", "POST"])
def custom_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.POST.get('next', request.GET.get('next', '/'))
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def custom_register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            user_type = form.cleaned_data.get('user_type')
            messages.success(request, f'Account created successfully as {user_type.title()}!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')