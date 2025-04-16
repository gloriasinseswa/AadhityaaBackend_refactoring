from django.contrib.auth.models import BaseUserManager
from django.db.models.manager import Manager

''''
class UserManager(BaseUserManager):
    def create_user(self, email, password, first_name, last_name, gender, date_of_birth,**kwargs):
        is_active = kwargs.pop('is_active', True)
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            is_active=is_active,
            **kwargs,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password, first_name, last_name, gender, date_of_birth):
        user = self.create_user(
            email, password, first_name, last_name, gender, date_of_birth,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user 
    '''  
""""
 class OTPManager(Manager):
    def create_otp(self, user,**kwargs):
        otp = self.model(user=user, otp=self._generate_otp(), **kwargs)
        otp.save()
        return otp
    def _generate_otp(self,is_numeric=True,size=6):
        import random
        keys = '0123456789' if is_numeric else '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if is_numeric:
            otp = ''.join(random.choices(keys, k=6))
        
        while self.model.objects.filter(otp=otp).exists():
            otp = ''.join(random.choices(keys, k=6))
            break
        return otp
    def verify_otp(self, otp):
        from django.conf import settings
        from django.utils import timezone
        now = timezone.now()
        delta = settings.VERIFICATION_CODE_EXPRY
        otp = self.model.objects.filter(otp=otp,created_at__lt=now).first()
        return otp != None 
"""
class UserManager(BaseUserManager):
    def create_user(self, email, password, first_name, last_name, **kwargs):
        is_active = kwargs.pop('is_active', True)
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            **kwargs,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, first_name, last_name):
        user = self.create_user(
            email, password, first_name, last_name,
        )
        user.user_type = 'ADMIN'
        user.save(using=self._db)
        return user

class OTPManager(Manager):
    def create_otp(self, user, **kwargs):
        otp = self.model(user=user, otp=self._generate_otp(), **kwargs)
        otp.save()
        return otp
        
    def _generate_otp(self, is_numeric=True, size=6):
        import random
        keys = '0123456789' if is_numeric else '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        otp = ''.join(random.choices(keys, k=size))

        while self.model.objects.filter(otp=otp).exists():
            otp = ''.join(random.choices(keys, k=size))
            
        return otp
        
    def verify_otp(self, otp_code):
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            otp_obj = self.model.objects.get(otp=otp_code)
            
            now = timezone.now()
            expiry_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRY', 5)
            expiry_time = otp_obj.created_at + timedelta(minutes=expiry_minutes)
            
            if now > expiry_time:
                return False, "OTP has expired. Please request a new one."
                
            return True, otp_obj
            
        except self.model.DoesNotExist:
            return False, "Invalid OTP"
