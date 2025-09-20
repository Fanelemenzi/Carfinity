from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.generic import RedirectView
from . import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/users/', include('users.admin_urls')),
    path('admin/organizations/', include('organizations.admin_urls')),
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('pwa.urls')),
    path('', include('maintenance_history.urls')),
    path('', include('assessments.urls')),
    path('', include('onboarding.urls', namespace='onboarding')),
    path('insurance/', include('insurance_app.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/images/icon.png', permanent=True)),
] #+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
