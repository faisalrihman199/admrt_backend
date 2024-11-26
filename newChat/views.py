from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer,ConversationsSerializer
from core.models import User  # Assuming User model is in core app
from core.serializers import UserDetailSerializer
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Conversation, Message  # Ensure Message is imported
from .serializers import ConversationsSerializer,MessageStatusSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from core.models import Notification
class UserConversationsView(generics.ListAPIView):
    serializer_class = ConversationsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Get all conversations where the user is either user1 or user2
        return Conversation.objects.filter(user1=user) | Conversation.objects.filter(user2=user)

    def get(self, request, *args, **kwargs):
        try:
            # Fetch the queryset
            queryset = self.get_queryset()
            # Serialize the data and pass request context
            serializer = self.get_serializer(queryset, many=True, context={'request': request})

            # Optional: Mark unread messages as read
            # for conversation in queryset:
            #     # Get all messages in the conversation where the receiver is the user and status is 'unread'
            #     unread_messages = Message.objects.filter(
            #         conversation=conversation,
            #         receiver=request.user,
            #         status__in=["sent","delivered"] # Assuming 'unread' is your status for unread messages
            #     )
            #     # Update the status to 'read'
            #     unread_messages.update(status='read')

            # Return the response
            return Response({
                'success': True,
                'message': "All conversations fetched successfully",
                'status': status.HTTP_200_OK,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            # Return error response
            return Response({
                'success': False,
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        
class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        conversation_id = request.GET.get('pk')
        user = self.request.user
        

        print("user is ",user)
        try:
            # Fetch the conversation
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Check if the user is part of the conversation
            if conversation.user1 != user and conversation.user2 != user:
                return Response({
                    'success': False,
                    'status': status.HTTP_403_FORBIDDEN,
                    'error': 'You do not have permission to access this conversation.'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get all messages in the conversation
            messages = Message.objects.filter(conversation=conversation).order_by('created_at')

            # Update the status of unread messages where receiver is the current user
            unread_messages = messages.filter(receiver=user, status__in=['sent', 'delivered'])
            unread_messages.update(status='read')

            # Serialize the data
            conversation_data = ConversationSerializer(conversation).data
            message_data = MessageSerializer(messages, many=True).data

            # Determine the other user in the conversation
            other_user = conversation.user2 if conversation.user1 == user else conversation.user1

            # Serialize the other user data
            other_user_data = UserDetailSerializer(other_user).data

            # Return the response
            return Response({
                'success': True,
                'status': status.HTTP_200_OK,
                'data': {
                    'conversation': conversation_data,
                    'messages': message_data,
                    'second_user': other_user_data
                }
            }, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            return Response({
                'success': False,
                'status': status.HTTP_404_NOT_FOUND,
                'error': 'Conversation not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class testView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.AllowAny]
    def get(self, request, *args, **kwargs):
        user = self.request.user

        return Response("hi")

class MarkNotificationsAsReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        """
        Marks all notifications for a specific user as read.
        """
        # Get the user by the provided user_id
        user = self.request.user

        # Retrieve all notifications for this user that are 'sent' or 'delivered'
        notifications = Notification.objects.filter(
            user=user,
            status__in=['sent', 'delivered']
        )

        # If no unread notifications exist, return an error response
        if not notifications.exists():
            return Response({'error': 'No unread notifications found.'}, status=status.HTTP_404_NOT_FOUND)

        # Mark notifications as read
        with transaction.atomic():
            # Update the status of notifications in the database
            notifications.update(status='read')
        
        # Retrieve the updated notifications (after the update)
        updated_notifications = Notification.objects.filter(
            user=user,
            status='read'
        )

        # Prepare the response data with updated notifications
        notifications_data = [
            {
                'id': notification.id,
                'message': notification.message,
                'status': notification.status,
                'created_at': notification.created_at.isoformat(),
                'notificationType': notification.notificationType,
            }
            for notification in updated_notifications
        ]

        # Return the updated notifications with a success message
        return Response({
            'success': True,
            'message': 'All notifications marked as read.',
            'data': notifications_data
        }, status=status.HTTP_200_OK)


   
class MarkMessageAsReadView(generics.GenericAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        # Retrieve message_id from query parameters
        message_id = request.query_params.get('id')
        
        if not message_id:
            return Response({'error': 'Message ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the message object
        message = get_object_or_404(Message, id=message_id)
        
        # Wrap the status update and message emission in a transaction
        with transaction.atomic():
            # Update the message status to 'read'
            serializer = self.get_serializer(message, data={'status': 'read'}, partial=True)
            
            if serializer.is_valid():
                serializer.save()

                # Emit to notify the sender that the message has been read
                self.emit_message_read_to_sender(message)
                
                return Response({'message': 'Message marked as read and sender notified.'}, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def emit_message_read_to_sender(self, message):
        # Define the sender's channel group name
        sender_group_name = f"user_{message.sender.id}"
        
        # Serialize the message read status update
        serialized_message = {
            'id': message.id,
            'conversation': message.conversation.id,
            'sender': message.sender.id,
            'receiver': message.receiver.id,
            'status': 'read',
            'created_at': message.created_at.isoformat()
        }
        
        # Get the channel layer and send the message read update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            sender_group_name,
            {
                'type': 'chat_message_read',  # Defines the event type
                'message': json.dumps(serialized_message)
            }
        )
    

    