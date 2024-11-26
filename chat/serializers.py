from django.contrib.auth import get_user_model
from rest_framework import serializers

from chat.models import Chat
from core.models import User
from core.utils import get_profile_image_url


class ChatSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    # receiver = serializers.CharField(source="receiver.full_name", read_only=True)
    receiver_id = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), source='receiver')
    conversation = serializers.CharField(source='conversation.id', read_only=True)

    class Meta:
        model = Chat
        fields = ["id", "sender_id", "receiver_id", "conversation", "text", "delivered", "created_at"]
        
        
class ChatUserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'user_role', 'profile_image']
        
    def get_profile_image(self, obj):
        if hasattr(obj, 'profile') and obj.profile.profile_image:
            return get_profile_image_url(obj.profile.profile_image)
        return None
