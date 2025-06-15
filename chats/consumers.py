from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .serializers import MessageSerializer
from .models import Room, Message
from django_redis import get_redis_connection
import logging


MAX_CHAT_USERS = 10
MAX_VIDEO_USERS = 2

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope['user']
        self.room = await self.get_chat_room()

        if not (self.user and self.user.is_authenticated and self.room and self.room.category == '1'):
            await self.close(code=4001, reason="Authentication or room invalid")
            return

        cache_key = f"room:{self.room_group_name}:users"
        client = await database_sync_to_async(get_redis_connection)('default')
        await database_sync_to_async(client.sadd)(cache_key, self.user.username.encode('utf-8'))
        current_users = await database_sync_to_async(client.scard)(cache_key)

        if current_users > MAX_CHAT_USERS:
            await self.accept()
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Chat room is full. Please try again later.'
            }))
            await database_sync_to_async(client.srem)(cache_key, self.user.username.encode('utf-8'))
            await self.close(code=4002, reason="Room full")
            return

        print(f"User {self.user} connected to room {self.room_group_name}. Current users: {current_users}")

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_count_update',
                'count': current_users
            }
        )

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name') and self.user and self.user.is_authenticated:
            cache_key = f"room:{self.room_group_name}:users"
            client = await database_sync_to_async(get_redis_connection)('default')
            await database_sync_to_async(client.srem)(cache_key, self.user.username.encode('utf-8'))
            current_users = await database_sync_to_async(client.scard)(cache_key)

            print(f"User {self.user} disconnected from room {self.room_group_name}. Current users: {current_users}")

            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_count_update',
                    'count': current_users
                }
            )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')
            if not message:
                print("Empty message received")
                return

            db_message = await self.save_message(message)
            if not db_message:
                print("Failed to save message")
                return

            serialized_message = await self.serialize_message(db_message)
            if not serialized_message:
                print("Failed to serialize message")
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': json.dumps(serialized_message)
                }
            )
        except json.JSONDecodeError:
            print("Invalid JSON received")
        except Exception as e:
            print(f"Error processing message: {e}")

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=message)

    async def user_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_count',
            'count': event['count']
        }))

    @database_sync_to_async
    def get_chat_room(self):
        try:
            room = Room.objects.get(id=self.room_name)
            return room
        except Room.DoesNotExist as e:
            print(f"Room not found: {e}")
            return None
        except Exception as e:
            print(f"Error fetching room: {e}")
            return None

    @database_sync_to_async
    def save_message(self, message):
        try:
            db_message = Message.objects.create(
                room=self.room,
                created_by=self.user,
                message=message
            )
            return db_message
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        try:
            serializer = MessageSerializer(message)
            return serializer.data
        except Exception as e:
            print(f"Error serializing message: {e}")
            return None




logger = logging.getLogger(__name__)
MAX_VIDEO_USERS = 4

class VideoCallConsumer(AsyncWebsocketConsumer):
  

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"video_call_{self.room_name}"
        self.user = self.scope["user"]

        if not (self.user and self.user.is_authenticated):
            await self.close(code=4001, reason="User not authenticated")
            return

        self.room = await self.get_room()
        if not (self.room and self.room.category == "2"):
            await self.close(code=4001, reason="Room not found or is not a video room")
            return

        self.redis = get_redis_connection("default")
        self.cache_key = f"room:{self.room_group_name}:users"
        
        current_users_list = await self.get_room_users()

        if len(current_users_list) >= MAX_VIDEO_USERS:
            await self.accept()
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "This room is currently full."
            }))
            await self.close(code=4002, reason="Room is full")
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await database_sync_to_async(self.redis.sadd)(self.cache_key, self.user.username)
        
        logger.info(f"{self.user.username} connected to room {self.room_group_name}")

        await self.send(text_data=json.dumps({
            'type': 'existing_users',
            'users': current_users_list
        }))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast.new_peer',
                'username': self.user.username,
                'exclude_channel': self.channel_name
            }
        )

    async def disconnect(self, close_code):
      
        if hasattr(self, 'room_group_name') and self.user and self.user.is_authenticated:
            await database_sync_to_async(self.redis.srem)(self.cache_key, self.user.username)
            
            logger.info(f"{self.user.username} disconnected from room {self.room_group_name}")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast.user_left',
                    'from': self.user.username
                }
            )
            
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
    
        try:
            data = json.loads(text_data)
            to_user = data.get('to')
            
            if not to_user:
                return

            data['from'] = self.user.username

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'relay.signaling_message',
                    'to_user': to_user,
                    'payload': data
                }
            )
        except Exception:
            logger.exception(f"Error in receive from {self.user.username}")


    async def broadcast_new_peer(self, event):
        if self.channel_name != event.get('exclude_channel'):
            await self.send(text_data=json.dumps({
                'type': 'new_peer',
                'username': event['username']
            }))

    async def broadcast_user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'from': event['from']
        }))

    async def relay_signaling_message(self, event):
        if event['to_user'] == self.user.username:
            await self.send(text_data=json.dumps(event['payload']))

    @database_sync_to_async
    def get_room(self):
        try:
            return Room.objects.get(id=self.room_name)
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def get_room_users(self) -> list:
        users = self.redis.smembers(self.cache_key)
        return [user.decode('utf-8') for user in users]

