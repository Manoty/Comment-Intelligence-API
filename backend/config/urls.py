from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/',          admin.site.urls),
    path('api/health/',     include('apps.common.urls')),
    path('api/auth/',       include('apps.accounts.urls')),
    path('api/comments/',   include('apps.comments.urls')),
    path('api/moderation/', include('apps.moderation.urls')),

    # [HARD-09] OpenAPI
    path('api/schema/',         SpectacularAPIView.as_view(),        name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/',   SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]