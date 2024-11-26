from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('profile/', include('users.urls')),
    path('ad-space/', include('ad_space.urls')),
    path('newChat/',include('newChat.urls')),
    path('chat/', include('chat.urls')),
    path('settings/', include('core.urls')),
]
