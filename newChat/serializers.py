from rest_framework import serializers
from .models import Conversation, Message

from core.serializers import UserDetailSerializer

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'message', 'sender', 'receiver', 'created_at','status']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'user1', 'user2', 'last_message', 'updated_at', 'messages']

class ConversationsSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()  # Get other user in conversation
    unread_messages_count = serializers.SerializerMethodField()  # Count unread messages
    last_message = MessageSerializer()  # Serialize the last_message as a nested object

    class Meta:
        model = Conversation
        fields = ['id', 'user1', 'user2', 'last_message', 'unread_messages_count', 'other_user']

    def get_other_user(self, obj):
        request = self.context.get('request')  # Access the request object
        user = request.user if request else None
        
        if user:
            # Determine the other user in the conversation
            other_user = obj.user2 if obj.user1 == user else obj.user1
            return UserDetailSerializer(other_user, context={'request': request}).data  # Serialize the other user
        return None

    def get_unread_messages_count(self, obj):
        request = self.context.get('request')  # Access the request object
        user = request.user if request else None

        if user:
            
            # Count unread messages where the current user is the receiver and status is 'sent' or 'delivered'
            h = Message.objects.filter(
                conversation=obj,
                receiver=user,
                status__in=['sent', 'delivered']
            ).count()
            return h
        return 0

    

class MessageStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['status']
