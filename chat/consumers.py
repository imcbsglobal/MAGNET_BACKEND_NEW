import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, UserOnlineStatus
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # We need user info to track online status
        # For now we'll expect it in the query string or sent after connect
        # But since we're using AuthMiddlewareStack, let's see if we can get it from scope
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Mark user as offline
        if hasattr(self, 'user_info'):
            await self.update_user_status(False)

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'init':
                # Initialize user info for status tracking
                self.user_info = {
                    'id': data.get('user_id'),
                    'role': data.get('role')
                }
                await self.update_user_status(True)
                
            elif message_type == 'chat_message':
                content = data.get('message')
                sender_id = data.get('sender_id')
                sender_role = data.get('sender_role')

                # Save message to database
                saved_message, recipient_id, recipient_role = await self.save_message(sender_id, sender_role, content)

                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat.message',
                        'message': content,
                        'sender_id': sender_id,
                        'sender_role': sender_role,
                        'created_at': saved_message.created_at.isoformat(),
                        'id': saved_message.id,
                        'attachments': [] 
                    }
                )

                # Send notification to recipient's private notification group
                await self.channel_layer.group_send(
                    f'notify_{recipient_role}_{recipient_id}',
                    {
                        'type': 'new_message_notification',
                        'room_id': self.room_id,
                        'sender_id': sender_id,
                        'sender_role': sender_role,
                        'message': content,
                        'created_at': saved_message.created_at.isoformat()
                    }
                )
            
            elif message_type == 'typing':
                sender_id = data.get('sender_id')
                sender_role = data.get('sender_role')
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user.typing',
                        'sender_id': sender_id,
                        'sender_role': sender_role,
                        'is_typing': data.get('is_typing', False)
                    }
                )
        except Exception as e:
            print(f"WebSocket Receive Error: {str(e)}")

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_role': event['sender_role'],
            'created_at': event['created_at'],
            'id': event['id'],
            'attachments': event.get('attachments', [])
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': event['sender_id'],
            'sender_role': event['sender_role'],
            'is_typing': event['is_typing']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, sender_role, content):
        room = ChatRoom.objects.get(id=self.room_id)
        message = Message.objects.create(
            room=room,
            sender_id=sender_id,
            sender_role=sender_role,
            content=content
        )
        # Update room's updated_at
        room.save() 
        
        # Determine recipient to send notification
        recipient_id = room.student_id if sender_role == 'teacher' else room.teacher_id
        recipient_role = 'student' if sender_role == 'teacher' else 'teacher'
        
        return message, recipient_id, recipient_role

    @database_sync_to_async
    def update_user_status(self, is_online):
        if not hasattr(self, 'user_info') or not self.user_info:
            return
        UserOnlineStatus.objects.update_or_create(
            user_id=self.user_info['id'],
            user_role=self.user_info['role'],
            defaults={'is_online': is_online, 'last_seen': timezone.now()}
        )

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.role = self.scope['url_route']['kwargs']['role']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_group_name = f'notify_{self.role}_{self.user_id}'

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def new_message_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'room_id': event['room_id'],
            'sender_id': event['sender_id'],
            'sender_role': event['sender_role'],
            'message': event['message'],
            'created_at': event['created_at']
        }))

    @database_sync_to_async
    def update_user_status(self, is_online):
        # We need to get user info from scope or attributes if available
        # This consumer might not have self.user_info set like ChatConsumer
        pass
