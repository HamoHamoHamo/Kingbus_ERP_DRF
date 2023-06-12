from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin', admin.site.urls),
    path('', include('humanresource.urls')),
    path('dispatch/', include('dispatch.urls')),
    path('complaint/', include('complaint.urls')),
    path('notice', include('notice.urls')),
    path('vehicle', include('vehicle.urls')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)