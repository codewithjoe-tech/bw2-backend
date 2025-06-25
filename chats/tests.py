import json
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

from chat.views import CreateRoomView, GetRoom, GetRoomById, GetMessages
from chat.consumers import ChatConsumer, VideoCallConsumer

mock_redis_client = MagicMock()
mock_redis_client.sadd.return_value = 1
mock_redis_client.srem.return_value = 1
mock_redis_client.scard.return_value = 1
mock_redis_client.smembers.return_value = {b'testuser1'}

@patch('django_redis.get_redis_connection', return_value=mock_redis_client)
class BaseConsumerTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.User = get_user_model()
        self.test_user = self.User.objects.create_user(
            username='testuser', email='test@example.com', password='password123'
        )
        self.test_user2 = self.User.objects.create_user(
            username='testuser2', email='test2@example.com', password='password123'
        )
        self.channel_layer = get_channel_layer()

    def get_auth_communicator(self, path, user):
        communicator = WebsocketCommunicator(
            application=self.application,
            path=path
        )
        communicator.scope['user'] = user
        return communicator

class MockRoom:
    objects = MagicMock()
    DoesNotExist = type('DoesNotExist', (Exception,), {})

    def __init__(self, id, room_name, category, created_by=None):
        self.id = id
        self.room_name = room_name
        self.category = category
        self.created_by = created_by
        self.created_at = '2023-01-01T12:00:00Z'

class MockMessage:
    objects = MagicMock()

    def __init__(self, id, room, created_by, message):
        self.id = id
        self.room = room
        self.created_by = created_by
        self.message = message
        self.created_at = '2023-01-01T12:00:00Z'

class MockRoomSerializer:
    def __init__(self, instance=None, data=None, many=False):
        self.instance = instance
        self.data = data
        self.many = many
        self.errors = {}
        if data:
            if not data.get('room_name'):
                self.errors['room_name'] = ['This field is required.']
            if not data.get('category'):
                self.errors['category'] = ['This field is required.']

    def is_valid(self, raise_exception=False):
        if self.errors and raise_exception:
            raise Exception("Validation Error")
        return not bool(self.errors)

    def save(self, created_by):
        if not self.errors:
            self.instance = MockRoom(
                id='mock-room-id-123',
                room_name=self.data['room_name'],
                category=self.data['category'],
                created_by=created_by
            )
            return self.instance
        return None

    @property
    def data(self):
        if self.instance:
            if self.many:
                return [{
                    'id': room.id,
                    'room_name': room.room_name,
                    'category': room.category,
                    'created_by': room.created_by.username if room.created_by else None
                } for room in self.instance]
            return {
                'id': self.instance.id,
                'room_name': self.instance.room_name,
                'category': self.instance.category,
                'created_by': self.instance.created_by.username if self.instance.created_by else None
            }
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

class MockMessageSerializer:
    def __init__(self, instance=None, data=None, many=False):
        self.instance = instance
        self.data = data
        self.many = many

    def is_valid(self):
        return True

    def save(self, room, created_by):
        self.instance = MockMessage(
            id='mock-msg-id-123',
            room=room,
            created_by=created_by,
            message=self.data['message']
        )
        return self.instance

    @property
    def data(self):
        if self.instance:
            if self.many:
                return [{
                    'id': msg.id,
                    'room_id': msg.room.id,
                    'created_by': msg

.created_by.username,
                    'message': msg.message,
                    'created_at': msg.created_at
                } for msg in self.instance]
            return {
                'id': self.instance.id,
                'room_id': self.instance.room.id,
                'created_by': self.instance.created_by.username,
                'message': self.instance.message,
                'created_at': self.instance.created_at
            }
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

@patch('chat.models.Room', new=MockRoom)
@patch('chat.models.Message', new=MockMessage)
@patch('chat.serializers.RoomSerializer', new=MockRoomSerializer)
@patch('chat.serializers.MessageSerializer', new=MockMessageSerializer)
class ChatAPITests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user1 = self.User.objects.create_user(
            username='chatuser1', email='chat1@example.com', password='password123'
        )
        self.user2 = self.User.objects.create_user(
            username='chatuser2', email='chat2@example.com', password='password123'
        )
        self.client.force_authenticate(user=self.user1)

        self.chat_room = MockRoom(id='chat-room-1', room_name='General Chat', category='1', created_by=self.user1)
        self.video_room = MockRoom(id='video-room-2', room_name='Video Call', category='2', created_by=self.user1)

        MockRoom.objects.get.side_effect = lambda **kwargs: {
            'id': self.chat_room.id
        }.get(kwargs.get('id')) or {
            'id': self.video_room.id
        }.get(kwargs.get('id')) or MockRoom.DoesNotExist()

        MockRoom.objects.filter.return_value = [self.chat_room, self.video_room]
        MockRoom.objects.filter.side_effect = lambda **kwargs: [
            room for room in [self.chat_room, self.video_room]
            if (kwargs.get('created_by') == room.created_by and
                ('category' not in kwargs or kwargs.get('category') == room.category) and
                ('room_name__icontains' not in kwargs or kwargs.get('room_name__icontains').lower() in room.room_name.lower()))
        ]

        self.message1 = MockMessage(id='msg1', room=self.chat_room, created_by=self.user1, message='Hello world!')
        self.message2 = MockMessage(id='msg2', room=self.chat_room, created_by=self.user2, message='Hi there!')
        MockMessage.objects.filter.return_value = [self.message1, self.messagebygg

.message2]
        MockMessage.objects.filter.side_effect = lambda **kwargs: [
            msg for msg in [self.message1, self.message2]
            if kwargs.get('room__id') == msg.room.id
        ]

    def test_create_room_success(self):
        url = reverse('create-room')
        data = {
            'room_name': 'New Test Chat Room',
            'category': '1'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['room_name'], 'New Test Chat Room')
        self.assertEqual(response.data['category'], '1')
        self.assertEqual(response.data['created_by'], self.user1.username)

    def test_create_room_invalid_data(self):
        url = reverse('create-room')
        data = {
            'room_name': '',
            'category': '1'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('room_name', response.data)

        data = {
            'room_name': 'Valid Name',
            'category': ''
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_get_rooms_filtered_by_category(self):
        url_chat = reverse('get-rooms') + '?category=chat'
        response_chat = self.client.get(url_chat, format='json')
        self.assertEqual(response_chat.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_chat.data), 1)
        self.assertEqual(response_chat.data[0]['category'], '1')
        self.assertEqual(response_chat.data[0]['room_name'], 'General Chat')

        url_video = reverse('get-rooms') + '?category=video'
        response_video = self.client.get(url_video, format='json')
        self.assertEqual(response_video.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_video.data), 1)
        self.assertEqual(response_video.data[0]['category'], '2')
        self.assertEqual(response_video.data[0]['room_name'], 'Video Call')

    def test_get_rooms_default_category(self):
        url = reverse('get-rooms')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], '1')

    def test_get_room_by_id_success(self):
        url = reverse('get-room-by-id', args=[self.chat_room.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.chat_room.id)
        self.assertEqual(response.data['room_name'], 'General Chat')

    def test_get_room_by_id_not_found(self):
        url = reverse('get-room-by-id', args=['non-existent-id'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_get_messages_success(self):
        url = reverse('get-messages', args=[self.chat_room.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['message'], 'Hello world!')
        self.assertEqual(response.data[1]['message'], 'Hi there!')
        self.assertEqual(response.data[0]['created_by'], self.user1.username)

    def test_get_messages_no_messages_found(self):
        empty_room = MockRoom(id='empty-room-id', room_name='Empty Room', category='1', created_by=self.user1)
        MockMessage.objects.filter.return_value = []

        url = reverse('get-messages', args=[empty_room.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

class ChatConsumerTests(BaseConsumerTest):
    async def setUp(self):
        await super().setUp()
        self.chat_room_id = 'test-chat-room-123'
        await sync_to_async(MockRoom.objects.get.reset_mock)()
        await sync_to_async(MockRoom.objects.get.return_value.__setattr__)('id', self.chat_room_id)
        await sync_to_async(MockRoom.objects.get.return_value.__setattr__)('category', '1')

    async def test_chat_consumer_connect_success(self):
        with patch('chat.consumers.ChatConsumer.get_chat_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.chat_room_id, room_name="Test Chat", category='1', created_by=self.test_user))):
            communicator = self.get_auth_communicator(f'/ws/chat/{self.chat_room_id}/', self.test_user)
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)
            await communicator.disconnect()

    async def test_chat_consumer_connect_authentication_fail(self):
        communicator = 我们bsocketCommunicator(
            application=self.application,
            path=f'/ws/chat/{self.chat_room_id}/'
        )
        communicator.scope['user'] = MagicMock(is_authenticated=False)
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(communicator.scope['close_code'], 4001)

    async def test_chat_consumer_connect_room_full(self):
        mock_redis_client.scard.return_value = 11
        with patch('chat.consumers.ChatConsumer.get_chat_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.chat_room_id, room_name="Full Chat", category='1', created_by=self.test_user))):
            communicator = self.get_auth_communicator(f'/ws/chat/{self.chat_room_id}/', self.test_user)
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)
            response = await communicator.receive_json()
            self.assertEqual(response['type'], 'error')
            self.assertIn('room is full', response['message'])
            await communicator.wait_until_closed()
            self.assertFalse(communicator.connected)
            self.assertEqual(communicator.scope['close_code'], 4002)
        mock_redis_client.scard.return_value = 1

    async def test_chat_consumer_send_and_receive_message(self):
        with patch('chat.consumers.ChatConsumer.get_chat_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.chat_room_id, room_name="Test Chat", category='1', created_by=self.test_user))):
            communicator1 = self.get_auth_communicator(f'/ws/chat/{self.chat_room_id}/', self.test_user)
            communicator2 = self.get_auth_communicator(f'/ws/chat/{self.chat_room_id}/', self.test_user2)

            connected1, _ = await communicator1.connect()
            connected2, _ = await communicator2.connect()
            self.assertTrue(connected1)
            self.assertTrue(connected2)

            await communicator1.receive_json()
            await communicator2.receive_json()

            test_message = "Hello, chat room!"
            await communicator1.send_json_to({'message': test_message})

            response2 = await communicator2.receive_json()
            self.assertEqual(response2['id'], 'mock-msg-id-123')
            self.assertEqual(response2['message'], test_message)
            self.assertEqual(response2['created_by'], self.test_user.username)

            response1 = await communicator1.receive_json()
            self.assertEqual(response1['id'], 'mock-msg-id-123')
            self.assertEqual(response1['message'], test_message)
            self.assertEqual(response1['created_by'], self.test_user.username)

            await communicator1.disconnect()
            await communicator2.disconnect()

    async def test_chat_consumer_user_count_update(self):
        with patch('chat.consumers.ChatConsumer.get_chat_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.chat_room_id, room_name="Test Chat", category='1', created_by=self.test_user))):
            mock_redis_client.scard.return_value = 1

            communicator1 = self.get_auth_communicator(f'/ws/chat/{self.chat_room_id}/', self.test_user)
            connected1, _ = await communicator1.connect()
            self.assertTrue(connected1)
            initial_count_msg = await communicator1.receive_json()
            self.assertEqual(initial_count_msg['type'], 'user_count')
            self.assertEqual(initial_count_msg['count'], 1)

            mock_redis_client.scard.return_value = 2
            communicator2 = self.get_auth_communicator(f'/ws/chat/{self.chat_room_id}/', self.test_user2)
            connected2, _ = await communicator2.connect()
            self.assertTrue(connected2)

            count_update_msg1 = await communicator1.receive_json()
            self.assertEqual(count_update_msg1['type'], 'user_count')
            self.assertEqual(count_update_msg1['count'], 2)

            count_update_msg2 = await communicator2.receive_json()
            self.assertEqual(count_update_msg2['type'], 'user_count')
            self.assertEqual(count_update_msg2['count'], 2)

            await communicator1.disconnect()
            mock_redis_client.scard.return_value = 1
            count_update_msg2_disc = await communicator2.receive_json()
            self.assertEqual(count_update_msg2_disc['type'], 'user_count')
            self.assertEqual(count_update_msg2_disc['count'], 1)

            await communicator2.disconnect()
        mock_redis_client.scard.return_value = 1

class VideoCallConsumerTests(BaseConsumerTest):
    async def setUp(self):
        await super().setUp()
        self.video_room_id = 'test-video-room-456'
        await sync_to_async(MockRoom.objects.get.reset_mock)()
        await sync_to_async(MockRoom.objects.get.return_value.__setattr__)('id', self.video_room_id)
        await sync_to_async(MockRoom.objects.get.return_value.__setattr__)('category', '2')

        mock_redis_client.smembers.return_value = set()
        mock_redis_client.sadd.return_value = 1
        mock_redis_client.srem.return_value = 1

    async def test_video_consumer_connect_success(self):
        with patch('chat.consumers.VideoCallConsumer.get_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.video_room_id, room_name="Test Video", category='2', created_by=self.test_user))):
            communicator = self.get_auth_communicator(f'/ws/video-call/{self.video_room_id}/', self.test_user)
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)
            response = await communicator.receive_json()
            self.assertEqual(response['type'], 'existing_users')
            self.assertEqual(response['users'], [])

            await communicator.disconnect()

    async def test_video_consumer_connect_room_full(self):
        mock_redis_client.smembers.return_value = {f'user{i}'.encode('utf-8') for i in range(VideoCallConsumer.MAX_VIDEO_USERS)}
        with patch('chat.consumers.VideoCallConsumer.get_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.video_room_id, room_name="Full Video", category='2', created_by=self.test_user))):
            communicator = self.get_auth_communicator(f'/ws/video-call/{self.video_room_id}/', self.test_user)
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)
            response = await communicator.receive_json()
            self.assertEqual(response['type'], 'error')
            self.assertIn('room is currently full', response['message'])
            await communicator.wait_until_closed()
            self.assertFalse(communicator.connected)
            self.assertEqual(communicator.scope['close_code'], 4002)
        mock_redis_client.smembers.return_value = set()

    async def test_video_consumer_new_peer_broadcast(self):
        mock_redis_client.smembers.return_value = set()
        with patch('chat.consumers.VideoCallConsumer.get_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.video_room_id, room_name="Test Video", category='2', created_by=self.test_user))):
            communicator1 = self.get_auth_communicator(f'/ws/video-call/{self.video_room_id}/', self.test_user)
            connected1, _ = await communicator1.connect()
            self.assertTrue(connected1)
            await communicator1.receive_json()

            mock_redis_client.smembers.return_value = {self.test_user.username.encode('utf-8')}
            communicator2 = self.get_auth_communicator(f'/ws/video-call/{self.video_room_id}/', self.test_user2)
            connected2, _ = await communicator2.connect()
            self.assertTrue(connected2)
            await communicator2.receive_json()

            new_peer_msg = await communicator1.receive_json()
            self.assertEqual(new_peer_msg['type'], 'new_peer')
            self.assertEqual(new_peer_msg['username'], self.test_user2.username)

            await communicator1.disconnect()
            await communicator2.disconnect()
        mock_redis_client.smembers.return_value = set()

    async def test_video_consumer_user_left_broadcast(self):
        with patch('chat.consumers.VideoCallConsumer.get_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.video_room_id, room_name="Test Video", category='2', created_by=self.test_user))):
            communicator1 = self.get_auth_communicator(f'/ws/video-call/{self.video_room_id}/', self.test_user)
            communicator2 = self.get_auth_communicator(f'/ws/video-call/{self.video_room_id}/', self.test_user2)

            await communicator1.connect()
            await communicator2.connect()

            await communicator1.receive_json()
            await communicator2.receive_json()
            await communicator1.receive_json()
            await communicator2.receive_json()

            mock_redis_client.srem.return_value = 1
            await communicator1.disconnect()

            user_left_msg = await communicator2.receive_json()
            self.assertEqual(user_left_msg['type'], 'user_left')
            self.assertEqual(user_left_msg['from'], self.test_user.username)

            await communicator2.disconnect()
        mock_redis_client.smembers.return_value = set()

    async def test_video_consumer_relay_signaling_message(self):
        with patch('chat.consumers.VideoCallConsumer.get_room',
                   new_callable=sync_to_async(lambda: MockRoom(id=self.video_room_id, room_name="Test Video", category='2', created_by=self.test_user))):
            communicator1 = self.get_auth_communicator(f'/ws/video-call/{self.video_room_id}/', self.test_user)
            communicator2 = self.get_auth_communicator(f'/ws/video-call/{self.video_room_id}/', self.test_user2)

            await communicator1.connect()
            await communicator2.connect()

            await communicator1.receive_json()
            await communicator2.receive_json()
            await communicator1.receive_json()
            await communicator2.receive_json()

            offer_payload = {
                'type': 'offer',
                'sdp': 'v=0...',
                'to': self.test_user2.username
            }
            await communicator1.send_json_to(offer_payload)

            received_offer = await communicator2.receive_json()
            self.assertEqual(received_offer['type'], 'offer')
            self.assertEqual(received_offer['sdp'], 'v=0...')
            self.assertEqual(received_offer['from'], self.test_user.username)
            self.assertEqual(received_offer['to'], self.test_user2.username)

            answer_payload = {
                'type': 'answer',
                'sdp': 'v=0...',
                'to': self.test_user.username
            }
            await communicator2.send_json_to(answer_payload)

            received_answer = await communicator1.receive_json()
            self.assertEqual(received_answer['type'], 'answer')
            self.assertEqual(received_answer['sdp'], 'v=0...')
            self.assertEqual(received_answer['from'], self.test_user2.username)
            self.assertEqual(received_answer['to'], self.test_user.username)

            await communicator1.disconnect()
            await communicator2.disconnect()
