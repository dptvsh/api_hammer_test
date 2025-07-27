from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from hammer_api.utils import generate_invite_code
from users.constants import (MAX_LENGTH_CONFIRMATION_CODE,
                             MAX_LENGTH_INVITE_CODE, MAX_LENGTH_NAME)


class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер модели пользователя с использованием номера телефона
    вместо имени пользователя.
    """

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(
                'Суперпользователь должен иметь is_staff=True.'
            )
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Суперпользователь должен иметь is_superuser=True.'
            )

        return self.create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Кастомная модель юзера с добавлением полей для телефона и инвайт-кодов.
    """

    phone_number = PhoneNumberField(
        verbose_name='Номер телефона',
        unique=True,
        region='RU',
    )
    invite_code = models.CharField(
        verbose_name='Код приглашения',
        max_length=MAX_LENGTH_INVITE_CODE,
        unique=True,
        blank=True,
        null=True,
    )
    created_at = models.DateField(
        verbose_name='Дата регистрации',
        auto_now_add=True,
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_LENGTH_NAME,
        null=True,
        blank=True,
        unique=False,
        help_text=('Необязательное поле. 150 символов или меньше.'),
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=128,
        blank=True,
        null=True,
    )
    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def save(self, *args, **kwargs):
        if self.invite_code is None:
            code = None
            while CustomUser.objects.filter(invite_code=code).exists():
                code = generate_invite_code()
            self.invite_code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.phone_number}'


class AuthCode(models.Model):
    """Модель кодов авторизации."""

    phone_number = PhoneNumberField(
        verbose_name='Номер телефона',
        unique=True,
        region='RU',
    )
    confirmation_code = models.CharField(
        verbose_name='Код авторизации',
        max_length=MAX_LENGTH_CONFIRMATION_CODE,
        unique=True,
    )
    created_at = models.DateTimeField(
        verbose_name='Дата генерации кода',
        auto_now=True,
    )

    class Meta:
        verbose_name = 'код авторизации'
        verbose_name_plural = 'Коды авторизации'
        constraints = [
            models.UniqueConstraint(
                fields=['phone_number', 'confirmation_code'],
                name='unique_code',
            ),
        ]

    def __str__(self):
        return f"{self.phone_number}: {self.confirmation_code}"


class Invitation(models.Model):
    """Модель приглашений по инвайт-кодам."""

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, unique=True,
        related_name='invitation_received', verbose_name='Приглашенный',
    )
    invited_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='invited_by', verbose_name='Пригласивший',
    )

    class Meta:
        verbose_name = 'приглашение'
        verbose_name_plural = 'Приглашения'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'invited_by'],
                name='unique_invite',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('invited_by')),
                name='prevent-sel-invite',
            ),
        ]

    def __str__(self):
        return f'Пользователя {self.user} пригласил {self.invited_by}'
