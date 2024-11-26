from django.urls import path
from .views import UserConversationsView,ConversationDetailView,testView,MarkMessageAsReadView
from .views import MarkNotificationsAsReadView
from users.views import UserCountView

urlpatterns = [
    path('conversations/', UserConversationsView.as_view(), name='user-conversations'),
     path('conversation/', ConversationDetailView.as_view(), name='conversation_detail'),
     path('accounts/',UserCountView.as_view(),name="accounts"),
     path('test/',testView.as_view(),name="aziz"),
     path('read/',MarkMessageAsReadView.as_view(),name="mark_message_read"),
     path('readNotification/',MarkNotificationsAsReadView.as_view(),name="mark_notification_read")
]
