from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from users.constants import (MAX_LENGTH_CONFIRMATION_CODE,
                             MAX_LENGTH_INVITE_CODE)
from users.models import AuthCode

User = get_user_model()


class PhoneNumberSerializer(serializers.ModelSerializer):
    """Сериализатор номер телефона пользователя."""

    phone_number = PhoneNumberField(region='RU')

    class Meta:
        model = User
        fields = (
            'phone_number',
        )


class AuthCodeSerializer(serializers.Serializer):
    """
    Сериализатор проверки кода авторизации пользователя и получения токена.
    """

    phone_number = PhoneNumberField(region='RU')
    confirmation_code = serializers.CharField(
        max_length=MAX_LENGTH_CONFIRMATION_CODE,
    )

    def validate(self, data):
        data_conf_code = data.get('confirmation_code')
        phone_number = data.get('phone_number')

        auth_code = AuthCode.objects.filter(
            phone_number=phone_number,
        ).exists()

        if not auth_code:
            raise serializers.ValidationError(
                {'phone_number': 'Номер телефона не найден в базе.'}
            )
        elif not AuthCode.objects.get(
            phone_number=phone_number,
        ).confirmation_code == data_conf_code:
            raise serializers.ValidationError(
                {'confirmation_code': 'Неверный код авторизации.'}
            )

        return data


class InvitedUserSerializer(serializers.ModelSerializer):
    """
    Вспомогательный сериализатор для вывода номеров приглашенных пользователей.
    """

    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('phone_number',)

    def get_phone_number(self, obj):
        return str(obj.phone_number)


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя."""

    invited_users = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'phone_number', 'invite_code', 'invited_users',
        )
        read_only_fields = fields

    def get_invited_users(self, obj):
        invited = obj.invited_by.all().select_related('user')
        return InvitedUserSerializer(
            [inv.user for inv in invited],
            many=True
        ).data


class InviteCodeSerializer(serializers.Serializer):
    """Сериализатор инвайт-кодов."""

    invite_code = serializers.CharField(max_length=MAX_LENGTH_INVITE_CODE)

    def validate_invite_code(self, value):
        if not User.objects.filter(invite_code=value).exists():
            raise serializers.ValidationError('Инвайт-код не найден')
        return value
