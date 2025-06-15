from django.urls import path

from . views import *

urlpatterns = [
    path('create-room' , CreateRoomView.as_view()),
    path('get-rooms', GetRoom.as_view()),
    path('get-room/<id>', GetRoomById.as_view()),
    path('get-messages/<id>', GetMessages.as_view())
]
