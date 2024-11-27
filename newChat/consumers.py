import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db import models
from .models import Conversation, Message
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode, ExpiredSignatureError, InvalidTokenError
from django.conf import settings
from core.models import User as user
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import Notification
from django.core.mail import send_mail
from django.conf import settings


User = get_user_model()

class ChatConsumer(WebsocketConsumer):
    
    def connect(self):
        token = self.scope['query_string'].decode().split('token=')[-1]
        self.user = self.get_user_from_token(token)
        
        if not self.user or not self.user.is_authenticated:
            self.close()
        else:
            self.accept()
            self.user_group_name = f"user_{self.user.id}"
            async_to_sync(self.channel_layer.group_add)(
                self.user_group_name,
                self.channel_name
            )
            # Add the user to a global group for broadcasting
            async_to_sync(self.channel_layer.group_add)(
                "global_users",
                self.channel_name,
            )
            self.user.last_seen = "Online"
            self.user.save(update_fields=["last_seen"])
            print(f"User {self.user.id} connected to group '{self.user_group_name}' and marked as online")

            # Temporarily remove the user from the global group to exclude them from the broadcast
            async_to_sync(self.channel_layer.group_discard)(
                "global_users",
                self.channel_name
            )

            # Emit a message to notify all other users that this user is online
            async_to_sync(self.channel_layer.group_send)(
                "global_users",
                {
                    'type': 'user_status',
                    'message': f"User {self.user.id} is online.",
                    'user_id': self.user.id,
                    'status': "Online"
                }
            )

            # Re-add the user to the global group after broadcasting
            async_to_sync(self.channel_layer.group_add)(
                "global_users",
                self.channel_name
            )

            # Update the status of all undelivered messages to "delivered"
            self.update_undelivered_messages_to_delivered(self.user)
            # self.mark_notifications_as_delivered(self.user)
            # Get the unread message count after updating the status
            unread_counts = self.get_unread_messages_count(self.user)
            print(unread_counts)
            
            # Prepare the message based on the unread status
            msg_check = True if len(unread_counts) > 0 else False
            if msg_check:
                message = f"You have unread messages."
            else:
                message = "You have no unread messages."
            # self.emit_unread_notifications(self.user)
            
            # Emit the unread count to the user only
            self.send(text_data=json.dumps({
                'type': 'unread_messages_count',
                'message': message,
                'unread_count': unread_counts
            }))

    def update_undelivered_messages_to_delivered(self, user):
        # Get undelivered messages for the user
        undelivered_messages = Message.objects.filter(
            receiver=user,
            status='sent'  # Only consider messages that are still "sent"
        )

        # Update the status to "delivered" and emit events to senders
        for message in undelivered_messages:
            # Update the message status to "delivered"
            message.status = 'delivered'
            message.save(update_fields=['status'])

            # Prepare the serialized message data for emitting
            message_data = {
                'id': message.id,
                'conversation_id': message.conversation.id,
                'sender_id': message.sender.id,
                'receiver_id': message.receiver.id,
                'status': message.status,
                'created_at': message.created_at.isoformat()
            }

            # Emit the delivery status to the sender
            sender_group_name = f"user_{message.sender.id}"
            async_to_sync(self.channel_layer.group_send)(
                sender_group_name,
                {
                    'type': 'message_delivery_status',
                    'message': message_data
                }
            )
        print(f"All 'sent' messages for user {user.id} have been updated to 'delivered' and senders notified.")
    def message_delivery_status(self, event):
        message_data = event['message']
        
        # Send the delivery status to the sender's WebSocket
        self.send(text_data=json.dumps({
            'type': 'delivery_status',
            'message_id': message_data['id'],
            'status': message_data['status'],
            'conversation_id': message_data['conversation_id'],
            'receiver_id': message_data['receiver_id'],
            'sender_id': message_data['sender_id'],
            'timestamp': message_data['created_at']
        }))
        

    def get_unread_messages_count(self, user):
        # Assuming `Message` model has 'status', 'receiver', 'conversation_id', and 'sender_id' fields
        unread_messages = (
            Message.objects.filter(
                receiver=user,
                status__in=['sent', 'delivered']
            )
            .values('conversation_id', 'sender_id')  # Group by conversation_id and sender_id
            .annotate(unread_count=models.Count('id'))  # Count messages in each group
        )

        # Create a list of dictionaries to hold the result
        unread_counts = []
        for msg in unread_messages:
            unread_counts.append({
                'conversation_id': msg['conversation_id'],
                'sender_id': msg['sender_id'],
                'unread_messages': msg['unread_count']
            })

        return unread_counts
    def get_user_from_token(self, token):
        try:
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return User.objects.get(id=decoded_data['user_id'])
        except (User.DoesNotExist, InvalidTokenError, ExpiredSignatureError):
            return None

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json.get('message', '')
        recipient_id = text_data_json.get('recipient_id', None)
        conversation_id = text_data_json.get('conversation_id', None)

        # Handle marking messages as read
        if conversation_id:
            self.mark_messages_as_read(conversation_id)
            return

        if recipient_id:
            try:
                recipient = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Recipient not found.'
                }))
                return

            # Retrieve or create a conversation between the two users
            conversation = Conversation.objects.filter(
                (models.Q(user1=self.user) & models.Q(user2=recipient)) |
                (models.Q(user1=recipient) & models.Q(user2=self.user))
            ).first()

            if not conversation:
                conversation = Conversation.objects.create(user1=self.user, user2=recipient)

            # Check if recipient's last_seen is a valid datetime object
            if recipient.last_seen != "Online":
                
                is_recipient_online = False
            else:
                is_recipient_online = True  
            print("receipient online status",is_recipient_online)
            message_status = "delivered" if is_recipient_online else "sent"

            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                receiver=recipient,
                message=message_text,
                status=message_status  # Set the message status
            )
            serialized_message = {
                'id': message.id,
                'conversation': message.conversation.id,
                'sender': message.sender.id,
                'receiver': message.receiver.id,
                'message': message.message,
                'status': message.status,
                'created_at': message.created_at.isoformat()
            }

            # Create a notification for the recipient
            notification_status = "sent" if not is_recipient_online else "delivered"
            Notification.objects.create(
                user=recipient,
                message=f"You have a new message from {self.user.username}",
                notificationType="message",
                status=notification_status
            )
            
            
            # Set last_message to the newly created message's ID
            conversation.last_message = message
            conversation.save()
            if(message_status == "sent"):
                self.send_unread_messages_email(recipient)
                

            # Send message to the recipient
            recipient_group_name = f"user_{recipient.id}"
            async_to_sync(self.channel_layer.group_send)(
                recipient_group_name,
                {
                    'type': 'chat_message',
                    'message': serialized_message,
                    'sender_id': self.user.id
                }
            )
            self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': serialized_message,  # Sending the same message back
            'sender_id': self.user.id
        }))
        else:
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Recipient ID is missing.'
            }))
            text_data_json = json.loads(text_data)
            message_text = text_data_json.get('message', '')
            recipient_id = text_data_json.get('recipient_id', None)
            conversation_id = text_data_json.get('conversation_id', None)

            # Handle marking messages as read
            if conversation_id:
                self.mark_messages_as_read(conversation_id)
                return

            if recipient_id:
                try:
                    recipient = User.objects.get(id=recipient_id)
                except User.DoesNotExist:
                    self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Recipient not found.'
                    }))
                    return

                # Retrieve or create a conversation between the two users
                conversation = Conversation.objects.filter(
                    (models.Q(user1=self.user) & models.Q(user2=recipient)) |
                    (models.Q(user1=recipient) & models.Q(user2=self.user))
                ).first()

                if not conversation:
                    conversation = Conversation.objects.create(user1=self.user, user2=recipient)

                # Check if recipient is online by comparing their last_seen field
                time_difference = timezone.now() - recipient.last_seen
                is_recipient_online = time_difference <= timedelta(minutes=2)  # Define the threshold for "online" status

                # Set the message status based on recipient's online status
                message_status = "delivered" if is_recipient_online else "sent"

                # Create the message and save it
                message = Message.objects.create(
                    conversation=conversation,
                    sender=self.user,
                    receiver=recipient,
                    message=message_text,
                    status=message_status  # Set the message status
                )

                # Set last_message to the newly created message's ID
                conversation.last_message = message
                conversation.save()
                
                # Send message to the recipient
                recipient_group_name = f"user_{recipient.id}"
                async_to_sync(self.channel_layer.group_send)(
                    recipient_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_text,
                        'sender_id': self.user.id
                    }
                )
                
            else:
                self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Recipient ID is missing.'
                }))
    
    
    def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']

        self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message,
            'sender_id': sender_id
        }))
        print(f"Message received: {message} from user {sender_id}")

    def mark_messages_as_read(self, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Update the status of messages in the specified conversation
            Message.objects.filter(
                conversation=conversation,
                receiver=self.user,
                status__in=['sent', 'delivered']  
            ).update(status='read')



            sender_id = Message.objects.filter(conversation=conversation, receiver=self.user).values_list('sender_id', flat=True).first()
            if sender_id:
                sender_group_name = f"user_{sender_id}"

                async_to_sync(self.channel_layer.group_send)(
                    sender_group_name,
                    {
                        'type': 'chat_message_read',
                        'message': json.dumps({
                            'id': conversation.id,
                            'status': 'read',
                            'conversation': conversation.id,
                            'sender': sender_id,
                            'receiver': self.user.id,
                            'created_at': timezone.now().isoformat()
                        })
                    }
                )
                print(f"User {self.user.id} marked messages in conversation {conversation_id} as read and notified the sender {sender_id}.")
            
        except Conversation.DoesNotExist:
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Conversation not found.'
            }))




    def disconnect(self, close_code):
        if self.user:
            self.user_group_name = f"user_{self.user.id}"
            
            # Remove the user from their own group
            async_to_sync(self.channel_layer.group_discard)(
                self.user_group_name,
                self.channel_name
            )

            disconnectTime= timezone.now()
            self.user.last_seen = timezone.now()
            self.user.save(update_fields=["last_seen"])

            # Temporarily remove the user from the global group to exclude them from the broadcast
            async_to_sync(self.channel_layer.group_discard)(
                "global_users",
                self.channel_name
            )

            # Emit a message to notify all other users that this user has disconnected
            async_to_sync(self.channel_layer.group_send)(
                "global_users",
                {
                    'type': 'user_status',
                    'message': f"User {self.user.id} has disconnected.",
                    'user_id':self.user.id,
                    "status": disconnectTime.isoformat()
                }
            )

            # Re-add the user to the global group after broadcasting
            async_to_sync(self.channel_layer.group_add)(
                "global_users",
                self.channel_name
            )

            print(f"User {self.user.id} disconnected and marked last seen as {self.user.last_seen}")


    def chat_message_read(self, event):
        message_data = json.loads(event['message'])
    
        # Send the message read status to the WebSocket
        self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': message_data['id'],
            'status': message_data['status'],
            'conversation_id': message_data['conversation'],
            'sender_id': message_data['sender'],
            'receiver_id': message_data['receiver'],
            'timestamp': message_data['created_at']
        }))
        print(f"Message {message_data['id']} in conversation {message_data['conversation']} has been read by receiver {message_data['receiver']}")

    def user_status(self, event):
        message = event['message']
        user_id = event['user_id']
        status = event['status']
        
        
        # Only send to other users, not the one triggering the event
        if self.user.id != user_id:
            self.send(text_data=json.dumps({
                'type': "User_status",
                'message': message,
                'user_id': user_id,
                'status': status
            }))
        
        print(f" message: {message}, User ID: {user_id}, Status: {status}")
    def emit_unread_notifications(self, user):
        """
        Emit the count of pending notifications (sent or delivered) to the connected user.
        """
        # Count the pending notifications for the user
        notification_count = Notification.objects.filter(
            user=user,
            status__in=['sent', 'delivered']
        ).count()

        # Emit the notification count to the user
        self.send(text_data=json.dumps({
            'type': 'notification_count',
            'count': notification_count
        }))

        print(f"Emitted notification count ({notification_count}) to user {user.id}.")


    # def emitUnreadNotifications(self, user):
    #     """
    #     Emit all pending notifications (sent or delivered) to the connected user.
    #     """
    #     notifications = Notification.objects.filter(
    #         user=user,
    #         status__in=['sent', 'delivered']
    #     )

    #     # Emit notifications to the user
    #     for notification in notifications:
    #         self.send(text_data=json.dumps({
    #             'type': 'notification',
    #             'message': notification.message,
    #             'status': notification.status,
    #             'notificationType': notification.notificationType,
    #             'created_at': notification.created_at.isoformat()
    #         }))

    #     print(f"Emitted {notifications.count()} notifications to user {user.id}.")
        
   

    def mark_notifications_as_delivered(self, user):
        """
        Set the status of all pending notifications for the user as 'delivered'.
        """
        # Fetch all notifications that are 'sent' but not 'delivered'
        notifications = Notification.objects.filter(
            user=user,
            status='sent'
        )

        # Update the status to 'delivered'
        notifications.update(status='delivered')

        # Emit the updated notifications to the user
        for notification in notifications:
            self.send(text_data=json.dumps({
                'type': 'notification',
                'message': notification.message,
                'status': 'delivered',
                'notificationType': notification.notificationType,
                'created_at': notification.created_at.isoformat(),
                'delivered_at': notification.delivered_at.isoformat() if notification.delivered_at else None
            }))
        
        print(f"Marked {notifications.count()} notifications as delivered for user {user.id}.")
    def send_unread_messages_email(self, user):
        print("inside send_unread_messages_email")
        """Send an email to the user informing them about unread messages."""
        unread_messages = Message.objects.filter(
            receiver_id=user.id,
            status='sent',
           
        )

        if unread_messages.exists():
            # Prepare the email content
            subject = f"You have unread messages "
            message = f"Hello {user.email},\n\nYou have unread messages from {unread_messages.first().sender.full_name}.\nPlease log in to your account to read the messages."

            # Send the email
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            print(f"Sent email to {user.email} about unread messages.")
            