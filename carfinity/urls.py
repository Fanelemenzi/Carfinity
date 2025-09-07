from django.contrib import admin
from django.urls import path, include
from . import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('pwa.urls')),
    path('', include('maintenance_history.urls')),
    path('', include('onboarding.urls', namespace='onboarding')),
    path('insurance/', include('insurance_app.urls')),
] #+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
