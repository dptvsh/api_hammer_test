from random import choices, randint
from string import ascii_letters, digits

from users.constants import MAX_LENGTH_INVITE_CODE


def generate_invite_code(
        length=MAX_LENGTH_INVITE_CODE,
        chars=ascii_letters + digits
):
    """Генерация инвайт-кода."""
    return ''.join(choices(chars, k=length))


def generate_confirmation_code():
    """Генерация цифрового кода (для SMS)."""
    return str(randint(1000, 9999))
