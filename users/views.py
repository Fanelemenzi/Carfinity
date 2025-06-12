from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'public/index.html', {})

def about(request):
    return render(request, 'public/about.html', {})

def blog(request):
    return render(request, 'public/blog.html', {})

def contact(request):
    return render(request, 'public/contact.html', {})

def login(request):
    return render(request, 'public/login.html', {})

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