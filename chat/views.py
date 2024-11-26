from django.contrib.auth import get_user_model
from django.db.models import Q, Max
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from chat.models import Chat, Conversation
from chat.pagination import ChatUserPagination
from chat.serializers import ChatSerializer, ChatUserSerializer
from chat.utils import generate_conversation_id
from core.models import User
from core.utils import get_profile_image_url


User = get_user_model()


class ChatUserAPIView(generics.ListAPIView):
    serializer_class = ChatUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'email']
    pagination_class = ChatUserPagination
    
    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        current_user = self.request.user
        queryset = User.objects.filter(
            Q(full_name__icontains=search_query) | Q(email__icontains=search_query)
        ).exclude(id=current_user.id)
        return queryset


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    
    partner_id = None
    conversation_id = None

    def get_queryset(self):
        user_id = self.request.user.id
        self.partner_id = self.request.GET.get('partner_id')
        if self.partner_id:
            # Grab the list of messages with that partner only
            self.conversation_id = generate_conversation_id(user_id, self.partner_id)
            # TODO: have to add limit as well
            queryset = self.queryset.filter(conversation_id=self.conversation_id).order_by('-id')
            return queryset
        else:
            return self.queryset

    def list(self, request, *args, **kwargs):
        user_id = request.user.id
        partner_id = request.GET.get('partner_id')
        if partner_id:
            # Return the chat list from this user's conversation
            queryset = self.get_queryset()
            serializer = self.serializer_class(queryset, many=True)

            # Mark the conversation as delivered
            conversation = get_object_or_404(Conversation, id=self.conversation_id)
            if conversation:
                Chat.objects.filter(conversation=conversation, receiver=user_id).update(delivered=True)
            else:
                print('No conversation found!')

            # Return the conversation
            return Response(serializer.data)
        
        # Else Grab the whole list of conversations summary for the user
        conversations = Conversation.objects.filter(
            Q(id__startswith=f"{user_id}-") | Q(id__endswith=f"-{user_id}")
        ).annotate(
            latest_chat=Max('chats__created_at')
        ).order_by('-latest_chat')

        formatted_list = {}
        for conv_id in conversations:
            other_user = conv_id.users.exclude(id=user_id).first()
            if other_user:
                unread_count = Chat.objects.filter(conversation=conv_id, sender=other_user, delivered=False).count()
                p_image = None
                if hasattr(other_user, 'profile'):
                    p_image = get_profile_image_url(other_user.profile.profile_image)
                formatted_list[other_user.id] = {
                    "full_name": other_user.full_name,
                    "profile_image": p_image,
                    "unread_messages": unread_count
                }
        return Response({
            "user_id": user_id,
            "conversations": formatted_list
        })
    
    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        sender = self.request.user
        receiver_id = self.request.data.get('receiver_id')
        receiver = get_object_or_404(User, id=receiver_id)

        conversation_id = generate_conversation_id(sender.id, receiver.id)

        conversation, created = Conversation.objects.get_or_create(id=conversation_id)
        if created:
            conversation.users.set([sender, receiver])

        serializer.save(sender=self.request.user, conversation=conversation)

    # @action(detail=False, methods=['post'], url_path='mark-delivered')
    # def mark_as_delivered(self, request):
    #     user_id = request.user.id
    #     partner_id = request.data.get('partner_id')
    #     if partner_id:
    #         conversation_id = generate_conversation_id(user_id, partner_id)
    #         conversation = get_object_or_404(Conversation, id=conversation_id)
    #         Chat.objects.filter(conversation=conversation, receiver=user_id).update(delivered=True)
    #         return Response({"success": True})
    #     else:
    #         return Response(status=status.HTTP_404_NOT_FOUND)
