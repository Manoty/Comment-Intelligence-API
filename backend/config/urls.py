from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', include('apps.common.urls')),
    path('api/auth/', include('apps.accounts.urls')),
    # Phase 2:
    # path('api/comments/', include('apps.comments.urls')),
]