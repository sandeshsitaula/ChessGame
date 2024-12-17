
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from authentication.models import Profile

@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated:
        return redirect('/play/lobby/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            return JsonResponse({'error': 'Passwords do not match'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
            
        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user)
        login(request, user)
        return JsonResponse({'success': 'Registration successful'})
    return render(request, 'auth/register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/play/lobby/')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('lobby'))
        else:
            return render(request, 'auth/login.html', {'error': 'Invalid credentials'})
            
    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
