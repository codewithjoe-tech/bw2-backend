from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import *
from .models import *


class CreateRoomView(APIView):
    def post(self, request):
        try:
            data = request.data
            print(data)
            serializer = RoomSerializer(data=data)
            if serializer.is_valid():
                serializer.save(created_by=request.user)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def get(self, request):
        try:
            rooms = Room.objects.filter(created_by=request.user)
            serializer = RoomSerializer(rooms, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class SearchRoom(APIView):
    def get(self, request):
        try:
            room_name = request.query_params.get('room_name')
            rooms = Room.objects.filter(room_name__icontains=room_name)
            serializer = RoomSerializer(rooms, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class GetRoom(APIView):
    def get(self, request):
        try:
            filter_category = request.query_params.get('category', 'chat')
            print(filter_category)
            rooms = Room.objects.filter(created_by=request.user, category='1' if filter_category == 'chat' else '2')
            print(rooms)

            serializer = RoomSerializer(rooms, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class GetRoomById(APIView):
    def get(self, request, id):
        try:
            room = Room.objects.get(id=id)
            serializer = RoomSerializer(room)
            return Response(serializer.data, status=200)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class GetMessages(APIView):
    def get(self, request, id):
        try:
            message = Message.objects.filter(room__id=id).select_related('created_by').order_by('created_at')
            serializer = MessageSerializer(message, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
