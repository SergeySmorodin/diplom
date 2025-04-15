from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/cloud/', include('cloud_app.urls', namespace='cloud-v1')),
    path('api/v1/users/', include('users.urls', namespace='users-v1')),
    
]