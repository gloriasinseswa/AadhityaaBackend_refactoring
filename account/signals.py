from django.dispatch import receiver,Signal

from account.models import OTP
from .tasks import send_verification_code
account_created = Signal()

@receiver(account_created)
def account_created_handler(sender, instance, created, **kwargs):
    # send email
    send_verification_code.delay(instance.id, OTP.ACCOUNT_VERIFICATION)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when User is created/updated"""
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
