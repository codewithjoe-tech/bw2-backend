from django.urls import path
from . views import *



urlpatterns = [
    path('register' ,RegisterView.as_view() ),
    path('login' , LoginView.as_view() ),
    path('refresh' , RefreshView.as_view() ),
    path('logout' , LogoutView.as_view() ),
    path('user' , GetUser.as_view() ),
]
