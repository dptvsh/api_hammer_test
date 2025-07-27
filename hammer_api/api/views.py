import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.serializers import (AuthCodeSerializer, InviteCodeSerializer,
                             PhoneNumberSerializer, UserProfileSerializer)
from hammer_api.utils import generate_confirmation_code
from users.models import AuthCode, Invitation

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    """Вьюсет для авторизации пользователей."""

    CODE_EXPIRATION_TIME = timedelta(minutes=5)

    def get_serializer_class(self):
        if self.action == 'request_code':
            return PhoneNumberSerializer
        return AuthCodeSerializer

    @action(detail=False, methods=['post'])
    def request_code(self, request, *args, **kwargs):
        """Получение кода авторизации."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        code = generate_confirmation_code()

        time.sleep(1)

        AuthCode.objects.update_or_create(
            phone_number=phone_number,
            defaults={'confirmation_code': code},
        )

        return Response(
            {"confirmation_code": code},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'])
    def auth_code(self, request):
        """Получение токена для входа с помощью кода авторизации."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['confirmation_code']

        auth_code = AuthCode.objects.get(
            phone_number=phone_number, confirmation_code=code,
        )
        if timezone.now() - auth_code.created_at > self.CODE_EXPIRATION_TIME:
            return Response(
                {"error": "Код истёк"}, status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={'phone_number': phone_number},
        )

        return Response(
            {'token': str(AccessToken.for_user(user))},
            status=status.HTTP_200_OK,
        )


class UserProfileViewSet(viewsets.GenericViewSet):
    """Профиль авторизованного пользователя."""

    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    def get_serializer_class(self):
        if self.action == 'activate_invite':
            return InviteCodeSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получение профиля текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def activate_invite(self, request):
        """Активация инвайт-кода."""
        user = request.user

        if hasattr(user, 'invitation_received'):
            return Response(
                {"error": "Вы уже активировали инвайт-код."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite_code = serializer.validated_data['invite_code']

        if invite_code == user.invite_code:
            return Response(
                {"error": "Нельзя активировать свой собственный инвайт-код."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inviter = get_object_or_404(User, invite_code=invite_code)

        Invitation.objects.create(invited_by=inviter, user=user)

        return Response(
            {"message": "Инвайт-код успешно активирован"},
            status=status.HTTP_200_OK,
        )
