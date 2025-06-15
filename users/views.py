from django.shortcuts import render, redirect
from .models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


# Create your views here.
def home(request):
    return render(request, 'public/index.html', {})

def about(request):
    return render(request, 'public/about.html', {})

def blog(request):
    return render(request, 'public/blog.html', {})

def contact(request):
    return render(request, 'public/contact.html', {})

def login_user(request):
    if request.method =="POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.success(request, ("There was an error try again"))
            return redirect('login')
    else:
        return render(request, 'public/login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logged out"))
    return redirect('home')

def dashboard(request):
    return render(request, 'dashboard/dashboard.html', {})

def register(request):
    return render(request, 'public/register.html', {})

def search(request):
    return render(request, 'search/search.html', {})

def search_results(request):
    return render(request, 'search/search-results.html', {})

#def create_record(request):
#    return render(request, 'maintenance/create_record.html', {})