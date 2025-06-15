from rest_framework import serializers
from . models import Room , Message
from authenticate.serializers import UserSerializer




class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = ['created_by']


class MessageSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    room = serializers.CharField()
    created_by = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = '__all__'