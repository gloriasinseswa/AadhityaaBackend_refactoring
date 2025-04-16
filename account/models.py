from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.forms import ValidationError
from core.models import BaseModel
from django.db import transaction
from .managers import UserManager,OTPManager
from django.core.validators import RegexValidator
import os
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from core.models import BaseModel
from .managers import UserManager, OTPManager
import os
import django.utils.timezone as timezone
from datetime import timedelta

class User(AbstractBaseUser, BaseModel):
    ADMIN = 'ADMIN'
    BUSINESS_OWNER = 'BUSINESS_OWNER'
    INDIVIDUAL = 'INDIVIDUAL'
    BUSINESS_STAFF = 'BUSINESS_STAFF'
    USER_TYPE_CHOICES = (
        (ADMIN, 'Admin'),
        (BUSINESS_OWNER, 'Business Owner'),
        (BUSINESS_STAFF, 'Business Staff'),
        (INDIVIDUAL, 'Individual'),
    )
    
    email = models.EmailField(unique=True, max_length=254)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=20, null=True)
    is_active = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def has_perm(self, perm, obj=None):
        return True
    
    def has_module_perms(self, app_label):
        return True
    
    @property
    def is_staff(self):
        return self.user_type == self.ADMIN
    
    @property
    def is_superuser(self):
        return self.user_type == self.ADMIN
    
    def is_admin(self):
        return self.user_type == self.ADMIN
    
    def is_business_owner(self):
        return self.user_type == self.BUSINESS_OWNER
    
    def is_business_staff(self):
        return self.user_type == self.BUSINESS_STAFF
    
    def is_individual(self):
        return self.user_type == self.INDIVIDUAL
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return self.get_full_name()
class Profile(BaseModel):
    def get_original_image_upload_path(instance, filename):
        return os.path.join(
            "Profiles/user_%s/original_quality" % instance.user.email,
            filename,
        )
    
    def get_medium_quality_upload_path(instance, filename):
        return os.path.join(
            "Profiles/user_%s/medium_quality" % instance.user.email,
            filename,
        )
    
    MALE = 'M'
    FEMALE = 'F'
    PREFER_NOT_TO_SPECIFY = 'N'
    GENDER_CHOICES = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (PREFER_NOT_TO_SPECIFY, 'Prefer not to specify'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1, null=True)
    date_of_birth = models.DateField(null=True)
    phone_number = models.CharField(max_length=15, null=True)
    image = models.ImageField(upload_to=get_original_image_upload_path, null=True, blank=True)
    
    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
    
    def get_low_quality_upload_path(self, filename):
        return os.path.join("Profiles/user_%s/low_quality" % self.user.email, filename)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"

class OTP(BaseModel):
    ACCOUNT_VERIFICATION = 'ACCOUNT_VERIFICATION'
    RESET_PASSWORD = 'RESET_PASSWORD'
    CHANGE_EMAIL_REQUEST = 'CHANGE_EMAIL_REQUEST'
    OTP_TYPE_CHOICES = (
        (ACCOUNT_VERIFICATION, 'Account Verification'),
        (RESET_PASSWORD, 'Reset Password'),
        (CHANGE_EMAIL_REQUEST, 'Change Email Request'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=12)
    type = models.CharField(choices=OTP_TYPE_CHOICES,
                            max_length=20, default=ACCOUNT_VERIFICATION)
    objects = OTPManager()

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        unique_together = [['user', 'type','otp']]
class Location(BaseModel):
    
    user = models.ForeignKey(User, related_name='locations', on_delete=models.CASCADE)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    zipCode = models.CharField(
        max_length=6,
        validators=[
            RegexValidator(
                regex='^[0-9]{5,6}$',
                message='Zip code must be 5 or 6 digits',
                code='invalid_zip_code'
            )
        ]
    )
    is_default = models.BooleanField(default=False)
    def clean(self):
        """Validate at the model level before saving"""
        if self.is_default:
            if Location.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).exists():
                raise ValidationError("User already has a default location")
    
    def save(self, *args, **kwargs):
        """Override save to handle default locations atomically"""
        with transaction.atomic():
            if self.is_default:
                Location.objects.filter(
                    user=self.user,
                    is_default=True
                ).exclude(pk=self.pk if self.pk else None).update(is_default=False)
            if not hasattr(self, 'is_default'):
                self.is_default = False
                
            super().save(*args, **kwargs)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'is_default'],
                name='unique_default_per_user',
                condition=models.Q(is_default=True)
            )
        ]
    
class Language(BaseModel):
    name = models.CharField(max_length=100, unique=True) 
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name
class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class UserCategory(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='users')
    class Meta:
        unique_together = ('user', 'category')
        verbose_name_plural = "User Categories"

    def __str__(self):
        return f"{self.user.email} - {self.category.name}"

class Post(BaseModel):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    LINK = 'link'

    POST_TYPES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
        (AUDIO, 'Audio'),
        (DOCUMENT, 'Document'),
        (LINK, 'Link'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content_type = models.CharField(max_length=10, choices=POST_TYPES, default=TEXT)
    text_content = models.TextField(blank=True, null=True)  
    media_file = models.FileField(upload_to='uploads/', blank=True, null=True)  
    link = models.URLField(blank=True, null=True)  
    location = models.ManyToManyField(Location, related_name='post_pincodes')
    categories = models.ManyToManyField('account.Category', related_name='post_categories')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.content_type} Post"
    

class Like(BaseModel):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.email} - Liked {self.post.id}"
class Comment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments_made")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    comment_text = models.TextField()

    def __str__(self):
        return f"{self.user.email} - Comment on {self.post.id}"
class Story(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"{self.user.email}'s Story"

class StoryImage(BaseModel):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='uploads/')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Image for {self.story.user.email}'s Story"





