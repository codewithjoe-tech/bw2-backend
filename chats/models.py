from django.db import models
import uuid
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()
class Room(models.Model):
    CHOICES = (
        ('1','Chat'),
        ('2' , 'Video')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User , on_delete=models.CASCADE)
    category = models.CharField(max_length=255 , choices=CHOICES)

    def __str__(self):
        return self.name





class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room , on_delete=models.CASCADE)
    message = models.TextField()
    created_by = models.ForeignKey(User , on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.id