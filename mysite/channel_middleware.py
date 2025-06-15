from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.db import close_old_connections
from django.contrib.auth import get_user_model


User = get_user_model()

from asgiref.sync import sync_to_async

class AuthenticationMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        close_old_connections()
        scope['user'] =None
     
     
        
        cookies = scope.get("cookies", {})
        access_token = cookies.get(f"access_token")

        if access_token:
            try:
                token = AccessToken(access_token)
                user_id = token['user_id']

                
                user = await self.get_user(user_id)
                
                if user is None or not user.is_active:  
                    scope['user'] = AnonymousUser()
                    return await self.app(scope, receive, send)


                scope['user'] = user

            except (InvalidToken, TokenError , User.DoesNotExist) as e:
                scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)

  

    @database_sync_to_async
    def get_user(self, user_id:str):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

