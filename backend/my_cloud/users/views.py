from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, logout, login
from .models import User
from .serializers import UserRegistrationSerializer, UserSerializer, UserLoginSerializer
import logging

logger = logging.getLogger(__name__)

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        logger.debug(f"Registration attempt with data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Registration validation failed: {serializer.errors}")
            return Response(
                {"detail": "Validation failed", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            self.perform_create(serializer)
            user = serializer.instance
            logger.info(f"User {user.username} registered successfully")
            return Response(
                {"detail": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response(
                {"detail": "Registration failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def list(self, request, *args, **kwargs):
        logger.debug(f"User list requested by {request.user.username}")
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"Admin user {request.user.username} accessed user list")
            return response
        except Exception as e:
            logger.error(f"Error getting user list: {str(e)}")
            return Response(
                {"detail": "Error retrieving user list"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance == request.user:
                logger.warning(f"Admin {request.user.username} attempted to delete themselves")
                return Response(
                    {"detail": "Cannot delete yourself"},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            self.perform_destroy(instance)
            logger.info(f"User {instance.username} deleted by admin {request.user.username}")
            return Response(
                {"detail": "User deleted successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return Response(
                {"detail": "Error deleting user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logger.debug(f"Login attempt with data: {request.data}")
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Login validation failed: {serializer.errors}")
            return Response(
                {"detail": "Validation failed", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        username = request.data.get('username')
        password = request.data.get('password')
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info(f"User {username} logged in. Session: {request.session.session_key}")
            return Response({
                'detail': 'Login successful',
                'user': UserSerializer(user).data,
                'sessionid': request.session.session_key
            })
        
        logger.warning(f"Failed login attempt for username: {username}")
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_authenticated:
            logger.warning("Logout attempt by unauthenticated user")
            return Response(
                {"detail": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        username = request.user.username
        try:
            logout(request)
            logger.info(f"User {username} logged out successfully")
            return Response(
                {"detail": "Logout successful"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error during logout for user {username}: {str(e)}")
            return Response(
                {"detail": "Error during logout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )