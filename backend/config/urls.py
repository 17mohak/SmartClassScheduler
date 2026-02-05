from django.contrib import admin
from django.urls import path, include
from api.views import login_view # Import the new view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/login/', login_view), # Add this line
]