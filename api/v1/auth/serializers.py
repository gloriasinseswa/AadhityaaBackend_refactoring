import re 
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.password_validation import validate_password as password_validator
from rest_framework import serializers
from account.models import Story, User, OTP, Location, Profile, StoryImage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from account.models import Profile

class LocationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    zipCode = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = Location
        fields = ['id', 'country', 'state', 'district', 'zipCode', 'is_default']
        extra_kwargs = {'is_default': {'read_only': True}}

    def validate_zipCode(self, value):
        cleaned_zip = re.sub(r'\D', '', value)
        if len(cleaned_zip) not in [5, 6]:
            raise serializers.ValidationError("Invalid zip code format.")
        return cleaned_zip

    def to_internal_value(self, data):
        """Override to make sure is_default is not passed manually."""
        if 'is_default' in data:
            del data['is_default']  
        return super().to_internal_value(data)

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    locations = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'gender', 'date_of_birth', 'phone_number', 'image',
            'locations'
        ]
        extra_kwargs = {
            'image': {'required': False}
        }

    def get_locations(self, obj):
        locations = obj.user.locations.all()
        return LocationSerializer(locations, many=True).data

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
    
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class UserSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, required=False)
    date_of_birth = serializers.CharField(
        source='profile.date_of_birth', 
        required=False,
        allow_null=True,
        allow_blank=True
    )
    gender = serializers.CharField(
        source='profile.gender',
        required=False,
        allow_null=True,
        allow_blank=True
    )
    setup_completed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'phone', 'password', 'date_of_birth', 
            'gender', 'locations', 'is_active', 'setup_completed'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'read_only': True}
        }

    def get_setup_completed(self, instance):
        return all([instance.first_name, instance.last_name, instance.phone, instance.locations.exists()])

    def to_representation(self, instance):
        cache_key = f'user_repr_{instance.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            cached_data = super().to_representation(instance)
            cache.set(cache_key, cached_data, timeout=300)  
        return cached_data

    def create(self, validated_data):
        locations_data = validated_data.pop('locations', [])
        profile_data = validated_data.pop('profile', {})
        user = User.objects.create_user(**validated_data)
        user._profile_data = profile_data 
        
        self._create_or_update_locations(user, locations_data)
        return user

    def update(self, instance, validated_data):
        locations_data = validated_data.pop('locations', None)
        profile_data = validated_data.pop('profile', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if profile_data:
            profile, _ = UserProfileUpdate.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        if locations_data is not None:
            self._create_or_update_locations(instance, locations_data)
        instance.save()
        return instance

    def _create_or_update_locations(self, user, locations_data):
        if not locations_data:
            return
        to_create = []
        to_update = []
        existing_locations = {str(loc.id): loc for loc in user.locations.all()}
        
        for idx, location_data in enumerate(locations_data):
            location_id = location_data.get('id')
            if location_id and str(location_id) in existing_locations:
                location = existing_locations[str(location_id)]
                for key, value in location_data.items():
                    if key != 'id':
                        setattr(location, key, value)
                to_update.append(location)
            else:
                to_create.append(Location(
                    user=user,
                    is_default=(idx == 0 and user.locations.count() == 0),
                    **{k: v for k, v in location_data.items() if k != 'id'}
                ))

        if to_create:
            Location.objects.bulk_create(to_create)
        if to_update:
            Location.objects.bulk_update(to_update, ['country', 'state', 'city', 'district', 'zipCode', 'is_default'])

        if any(loc.get('id') for loc in locations_data):
            updated_ids = [str(loc.get('id')) for loc in locations_data if loc.get('id')]
            user.locations.exclude(id__in=updated_ids).delete()

class SetDefaultLocationSerializer(serializers.Serializer):
    location_id = serializers.UUIDField()

    def validate_location_id(self, value):
        user = self.context['request'].user
        if not Location.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Location not found or doesn't belong to you")
        return value

class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})


class CreateAccountSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=15, required=False)
    gender = serializers.ChoiceField(choices=Profile.GENDER_CHOICES, required=False)
    date_of_birth = serializers.DateField(required=False)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 
                 'phone_number', 'gender', 'date_of_birth']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        profile_data = {}
        if 'phone_number' in validated_data:
            profile_data['phone_number'] = validated_data.pop('phone_number')
        if 'gender' in validated_data:
            profile_data['gender'] = validated_data.pop('gender')
        if 'date_of_birth' in validated_data:
            profile_data['date_of_birth'] = validated_data.pop('date_of_birth')
        
        user = User.objects.create_user(**validated_data)
        
        if profile_data:
            Profile.objects.filter(user=user).update(**profile_data)
        
        return user

class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True)
    
    def validate(self, attrs):
        otp_code = attrs.get('otp')
        print(f"Validating OTP: {otp_code}")
        
        try:
            self.otp_obj = OTP.objects.get(otp=otp_code)
            print(f"OTP found: {self.otp_obj.otp}, User: {self.otp_obj.user.email}, Type: {self.otp_obj.type}")
            
            from django.utils import timezone
            from django.conf import settings
            from datetime import timedelta
            
            expiry_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRY', 5)
            expiry_delta = timedelta(minutes=expiry_minutes)
            
            expiry_time = self.otp_obj.created_at + expiry_delta
            
            if timezone.now() > expiry_time:
                print(f"OTP expired: Created at {self.otp_obj.created_at}, Expired at {expiry_time}, Now: {timezone.now()}")
                raise serializers.ValidationError("OTP has expired. Please request a new one.")
            
            self.user = self.otp_obj.user
            
            return attrs
        except OTP.DoesNotExist:
            print(f"OTP not found: {otp_code}")
            all_otps = OTP.objects.all()
            print(f"Existing OTPs: {[o.otp for o in all_otps]}")
            raise serializers.ValidationError("Invalid OTP")

class UpdateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    type = serializers.ChoiceField(choices=OTP.OTP_TYPE_CHOICES, default=OTP.ACCOUNT_VERIFICATION)
    def validate_email(self, value):
        value = value.lower()
        try:
            self.user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist')

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate_email(self, value):
        value = value.lower()
        try:
            self.user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            return value
    
    def validate_new_password(self, value):
        password_validator(value)
        return value

class ProfileMeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def put(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'name', 'code']
        read_only_fields = ['id']

class StoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryImage
        fields = ['id', 'story', 'image', 'created_at']
        read_only_fields = ['id', 'created_at']

class StorySerializer(serializers.ModelSerializer):
    images = StoryImageSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Story
        fields = ['id', 'user', 'user_name', 'images', 'created_at', 'is_expired']
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Story.objects.create(**validated_data)

