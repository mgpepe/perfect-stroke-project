import base64
import uuid

import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api.services.email_service import send_email
from .serializers import (
    UserGetSerializer, UserSignupSerializer, UserFbSignupSerializer,
    UserEditSerializer, FacebookLoginSerializer, ForgottenPasswordSerializer,
)

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def search_users(request):
    query = request.query_params.get('query', '')
    skip = int(request.query_params.get('skip', 0))
    take = int(request.query_params.get('take', 20))

    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(username__icontains=query)
    )[skip:skip + take]

    serializer = UserGetSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = UserGetSerializer(user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def facebook_user_exists(request, facebook_id):
    exists = User.objects.filter(facebook_id=facebook_id).exists()
    return Response({'exists': exists})


@api_view(['GET'])
@permission_classes([AllowAny])
def is_username_available(request, username):
    available = not User.objects.filter(username=username).exists()
    return Response({'available': available})


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserSignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    tokens = get_tokens_for_user(user)
    return Response({
        'user': UserGetSerializer(user).data,
        **tokens,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def facebook_login(request):
    serializer = FacebookLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data['facebook_token']

    # Verify with Facebook
    fb_response = requests.get(
        'https://graph.facebook.com/v2.9/me',
        params={
            'access_token': token,
            'fields': 'id,name,first_name,last_name,birthday,picture',
        },
        timeout=10,
    )

    if fb_response.status_code != 200:
        return Response(
            {'error': 'Invalid Facebook token'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    fb_data = fb_response.json()
    fb_id = int(fb_data['id'])

    # Find or create user
    user = User.objects.filter(facebook_id=fb_id).first()
    if not user:
        user = User(
            username=f'fb_{uuid.uuid4().hex[:8]}',
            facebook_id=fb_id,
            first_name=fb_data.get('first_name', ''),
            last_name=fb_data.get('last_name', ''),
            picture_url=fb_data.get('picture', {}).get('data', {}).get('url', ''),
        )
        user.set_unusable_password()
        user.save()

    tokens = get_tokens_for_user(user)
    return Response({
        'user': UserGetSerializer(user).data,
        **tokens,
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = UserEditSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserGetSerializer(user).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgotten_password(request):
    serializer = ForgottenPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    identifier = serializer.validated_data['username_or_email']

    user = User.objects.filter(
        Q(username=identifier) | Q(email=identifier)
    ).first()

    if user:
        token = default_token_generator.make_token(user)
        encoded_token = base64.urlsafe_b64encode(token.encode()).decode()
        from django.conf import settings
        reset_link = f'{settings.API_URL}/account/reset-password?username={user.username}&token={encoded_token}'
        send_email(
            user.email,
            'Password Reset - PerfectStroke',
            f'<p>Click <a href="{reset_link}">here</a> to reset your password.</p>',
        )

    return Response({'status': 'ok'})
