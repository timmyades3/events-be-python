from django.shortcuts import render,redirect
from rest_framework import generics
from rest_framework.response import Response
from django.views import View
from .serializers import UserSerializer,Groupserializer, User_GroupsSerializer
from .models import CustomUser,Group, User_Groups
from authlib.integrations.django_client import OAuth
from django.contrib.auth import get_user_model
from rest_framework import status
from django.urls import reverse
import uuid
from .authentication import AuthenticationMiddleware, IsAuthenticatedUser
from rest_framework.views import APIView
from django.core.cache import cache
from itsdangerous import URLSafeTimedSerializer
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q


CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile',
    }
)


# Create your views here.
class UserView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [AuthenticationMiddleware]
    permission_classes = [IsAuthenticatedUser]
    
class SingleUserView(generics.RetrieveUpdateAPIView):
    authentication_classes = [AuthenticationMiddleware]
    permission_classes = [IsAuthenticatedUser]
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'  # Set the lookup field to 'id'
    
    
class LoginView(View):
    def get(self, request):
        redirect_uri = request.build_absolute_uri(reverse('auth'))
        return oauth.google.authorize_redirect(request, redirect_uri)


class AuthView(APIView):
    def post(self,request):
        data = request.data
        name = data.get("name")
        email = data.get("email")
        picture = data.get("photoUrl")
        id = data.get("id")
        print(id)
        
        try:
            user = CustomUser.objects.get(id=id)
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create(email=email, id=str(id), name=name, avatar=picture)
            
        serializer = URLSafeTimedSerializer(AuthenticationMiddleware.secret_key)
        session_token = serializer.dumps(str(user.id))
            
        data = {
            "success": True,
            "user_id": id,
            "session_token": session_token,
            "status": 200
        }
        
        return Response(data)
        
        
    def get(self, request):
        token = oauth.google.authorize_access_token(request)
        email = token.get('userinfo', {}).get('email')
        name = token.get('userinfo', {}).get('name')
        picture = token.get('userinfo', {}).get('picture')
        access_token = token.get('access_token', {})
        id = token.get('userinfo', {}).get('sub')
        access_token = token.get('access_token', {})

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create(email=email, user_id=str(id), name=name, avatar=picture)
            
        # Set the is_active status in Redis
        cache_key = f'user_active_status:{user.id}'
        cache.set(cache_key, True)

        # Generate a session token
        serializer = URLSafeTimedSerializer(AuthenticationMiddleware.secret_key)
        session_token = serializer.dumps(str(user.id))
        
        data = {
            "success": True,
            "user_id": id,
            "session_token": session_token,
            "status": 200
        }
        
        response = Response(data, status=200)

        return response
    

class CreateGroupApiView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = Groupserializer
    
    def post(self, request, *args, **kwargs):
        serializer = Groupserializer()
        if serializer.is_valid():
            
            serializer.save(admin=self.request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
    


class RetrieveGroupApiView(generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = Groupserializer
    lookup_field = 'pk'

class UpdateGroupApiView(generics.UpdateAPIView):
    queryset = Group.objects.all()
    serializer_class = Groupserializer
    lookup_field = 'pk'

    


class GetUserGroupsApiView(generics.ListAPIView):
    queryset= User_Groups.objects.all()
    serializer_class = User_GroupsSerializer
    # def get(self, request, *args, **kwargs):
    #     user = request.user
    #     if user:
    #         user_groups = User_Groups.objects.filter(user=user).select_related('group')      
    #         groups = [user_group.group for user_group in user_groups]
      
    #         response_data = {
    #         'groups': groups,
    #         }
    #         return Response(response_data, status=status.HTTP_200_OK)
    #     return Response({"error": "user does not exist"},status=status.HTTP_404_NOT_FOUND)