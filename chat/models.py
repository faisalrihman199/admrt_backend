from django.conf import settings
from django.db import models


class Conversation(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')

    def __str__(self) -> str:
        return self.id
    

class Chat(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_chats')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='received_chats')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='chats')
    text = models.TextField()
    delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.sender.full_name}: {self.text}"
