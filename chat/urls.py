from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, ChatUserAPIView


router = DefaultRouter()
router.register('', ChatViewSet)

urlpatterns = [
    path('user/', ChatUserAPIView.as_view(), name='chat-user'),
] + router.urls
