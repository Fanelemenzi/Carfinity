from django.contrib import admin
from django.urls import path
from django.urls import path, include
from . import settings
from maintenance_history import views
from django.conf.urls.static import static

app_name = 'maintenance_history'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('maintenance_history.urls')),
    path('', include('maintenance_history.urls')),
    path('', include('onboarding.urls')),
] #+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
