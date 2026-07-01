from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created successfully",
                "user": {
                    "email_or_username": user.email,
                    "created_at": user.date_joined
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response({
                "message": "Login successful",
                "access": serializer.validated_data['token'],
                "refresh": serializer.validated_data['refresh_token'],
                "user": {
                    "id": serializer.validated_data['user_id'],
                    "email": serializer.validated_data['user_email'],
                    "fullName": serializer.validated_data['full_name'],
                    "role": serializer.validated_data['user_role'],
                    "createdAt": serializer.validated_data['created_at']
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
