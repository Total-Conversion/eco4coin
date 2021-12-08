import random
import string

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


def random_wallet_id():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(34))


def create_fake_email():
    return "fake@email.com"


class CustomUser(AbstractUser):
    cash_locked = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100000000)],
        help_text="how much cash_balance a user has locked"
    )
    coin_locked = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100000000)],
        help_text="how much coin_balance a user has locked"
    )
    cash_balance = models.FloatField(
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(100000000)],
        help_text="how much cash_balance a user has"
    )
    device = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    coin_balance = models.IntegerField(default=10)
    wallet_id = models.CharField(
        default=random_wallet_id,
        unique=True,
        max_length=34,
    )
    email = models.EmailField(blank=True, default=create_fake_email)

    def __str__(self):
        return str(self.wallet_id)
