from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken







class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self , request):
        data = request.data
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data , status=201)
        return Response(serializer.errors , status=400)
    


class LoginView(APIView):
    authentication_classes = []
    permission_classes =  []
    def post(self, request):
        data = request.data
        serializer = LoginSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        response = Response(status=200)
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite='None'
        )
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=True,
            samesite='None'
        )   
        return response
    
class RefreshView(APIView):
    permission_classes = []
    authentication_classes = []
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        access_token = request.COOKIES.get('access_token')
        if not (refresh_token and access_token):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)

          
            response = Response(status=status.HTTP_200_OK)

            response.set_cookie(
                key='refresh_token',
                value=str(token),
                httponly=True,
                secure=True,
                samesite='None'
            )
            response.set_cookie(
                key='access_token',
                value=str(token.access_token), 
                httponly=True,
                secure=True,
                samesite='None'
            )
            return response
        except Exception as e:
            print(e)
            response = Response(status=status.HTTP_400_BAD_REQUEST)
            response.delete_cookie('refresh_token')
            response.delete_cookie('access_token')
            return response




class GetUser(APIView):
    def get(self , request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data , status=200)
        
class LogoutView(APIView):
    def post(self , request):
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response