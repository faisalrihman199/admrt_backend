from django.db import models
from core.models import User  # Importing the Users model from the core app

class Conversation(models.Model):
    user1 = models.ForeignKey(User, related_name='conversation_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='conversation_user2', on_delete=models.CASCADE)
    last_message = models.ForeignKey("Message",related_name='last_name',on_delete=models.CASCADE,null=True,  # Allow null values
        blank=True ) # Allow blank values in forms)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Conversation between {self.user1.username} and {self.user2.username}'


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='message_sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='message_receiver', on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.sender.username} at {self.created_at}'







# Create your models here.
