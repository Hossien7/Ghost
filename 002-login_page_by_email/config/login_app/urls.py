from django.urls import path
from .views import login
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('', login, name='login'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
