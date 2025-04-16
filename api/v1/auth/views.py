from warnings import filters
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from account.signals import account_created
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from django.db import transaction
from rest_framework import serializers
from rest_framework import filters


from .serializers import (
    CreateAccountSerializer, SendOTPSerializer, VerifyOTPSerializer, 
    UpdateAccountSerializer, LoginSerializer, ProfileSerializer,
    LocationSerializer, LanguageSerializer, StorySerializer, StoryImageSerializer
)
from account.models import (
    User, OTP, Profile, Location, Language,Story, StoryImage
)
from rest_framework.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class AccountViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CreateAccountSerializer
    permission_classes = []

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateAccountSerializer
        if self.action == "activate_account" or self.action == 'verify_otp':
            return VerifyOTPSerializer
        if self.action == 'send_otp' or self.action == 'resend_verification':
            return SendOTPSerializer
        if self.action == 'partial_update':
            return UpdateAccountSerializer
        if self.action == 'login':
            return LoginSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ['create', 'activate_account', 'verify_otp', 'send_otp', 
                          'reset_password', 'login', 'resend_verification']:
            self.permission_classes = [AllowAny]
        if self.action in ['retrieve', 'update', 'partial_update']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip()  
        password = serializer.validated_data['password']
        print(f"Login attempt with email: '{email}'")
        
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
            print(f"User found: {user.id}, email: {user.email}, is_active: {user.is_active}")
            
            if not user.is_active:
                return Response({
                    "detail": "Account is not active. Please verify your email using the OTP sent to your email address.",
                    "requires_verification": True,
                    "email": email
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.check_password(password):
                print("Password validation failed")
                return Response({"detail": "Invalid credentials"}, 
                            status=status.HTTP_401_UNAUTHORIZED)
    
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user_id": str(user.id),
                "email": user.email
            }, status=status.HTTP_200_OK)
            
        except user_model.DoesNotExist:
            print(f"No user with email '{email}' exists")
            return Response({"detail": "Invalid credentials"}, 
                        status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        
        if not email or not new_password:
            return Response({"detail": "Email and new password are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            
            from api.v1.auth.serializers import password_validator
            try:
                password_validator(new_password)
            except serializers.ValidationError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            
            Token.objects.filter(user=user).delete()
            
            return Response({"detail": "Password reset successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "If an account with this email exists, the password has been reset"}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], url_path='send-otp')
    def send_otp(self, request):
        """Send OTP to user's email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.user
        otp_type = serializer.validated_data.get('type')
        
        from account.tasks import send_verification_code
        send_verification_code.delay(user.id, otp_type)
        
        from django.conf import settings
        expiry_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRY', 5)
        
        return Response({
            "message": f"OTP sent successfully. It will expire in {expiry_minutes} minutes.",
            "expiry_minutes": expiry_minutes
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='resend-verification')
    def resend_verification(self, request):
        """Resend verification OTP to user's email"""
        email = request.data.get('email')
        if not email:
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
            
            if user.is_active:
                return Response({"detail": "Account is already active"}, status=status.HTTP_400_BAD_REQUEST)
    
            OTP.objects.filter(user=user, type=OTP.ACCOUNT_VERIFICATION).delete()
            
            from account.tasks import send_verification_code
            send_verification_code.delay(user.id, OTP.ACCOUNT_VERIFICATION)
            
            return Response({"detail": "Verification code sent to your email"}, status=status.HTTP_200_OK)
        except user_model.DoesNotExist:
            return Response({"detail": "If the email exists, a verification code has been sent"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """Verify OTP"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        otp_obj = serializer.otp_obj
        user = serializer.user
        
        if otp_obj.type == OTP.ACCOUNT_VERIFICATION:
            user.is_active = True
            user.save()
            
            otp_obj.delete()
            
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                "message": "Account activated successfully",
                "token": token.key,
                "user_id": str(user.id),
                "email": user.email
            }, status=status.HTTP_200_OK)
            
        elif otp_obj.type == OTP.RESET_PASSWORD:
            return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
        else:
            otp_obj.delete()
            return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)

    @action(["POST"], detail=False, url_path='activate-account')
    def activate_account(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        otp_code = serializer.validated_data.get('otp')
        
        try:
            otp_obj = OTP.objects.get(otp=otp_code)
            user = otp_obj.user
            
            if otp_obj.type != OTP.ACCOUNT_VERIFICATION:
                return Response({"detail": "Invalid OTP type"}, status=status.HTTP_400_BAD_REQUEST)
            
            user.is_active = True
            user.save()
            
            otp_obj.delete()

            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                "message": "Account activated successfully",
                "token": token.key,
                "user_id": str(user.id),
                "email": user.email
            }, status=status.HTTP_200_OK)
        except OTP.DoesNotExist:
            return Response({"detail": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save(is_active=False)
        profile_data = {
            'user': user,
            'gender': serializer.validated_data.get('gender', None),
            'date_of_birth': serializer.validated_data.get('date_of_birth', None),
            'phone_number': serializer.validated_data.get('phone_number', None),
            'image': serializer.validated_data.get('image', None)
        }
        
        profile_data = {k: v for k, v in profile_data.items() if v is not None}
    
        if len(profile_data) > 1: 
            Profile.objects.create(**profile_data)
        from account.tasks import send_verification_code
        send_verification_code.delay(user.id, OTP.ACCOUNT_VERIFICATION)
        
        account_created.send(sender=self.__class__, instance=user, created=True)
        
        return Response({
            **serializer.data,
            "message": "Account created successfully. Please check your email for verification code."
        }, status=201)
        
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        try:
            profile = instance.profile
            profile_data = {
                'gender': profile.gender,
                'date_of_birth': profile.date_of_birth,
                'phone_number': profile.phone_number,
                'image': request.build_absolute_uri(profile.image.url) if profile.image else None
            }
            data.update(profile_data)
        except Profile.DoesNotExist:
            pass
            
        return Response(data)
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user_fields = ['first_name', 'last_name', 'email']
        profile_fields = ['gender', 'date_of_birth', 'phone_number', 'image']
        
        user_data = {k: v for k, v in request.data.items() if k in user_fields}
        profile_data = {k: v for k, v in request.data.items() if k in profile_fields}
        serializer = self.get_serializer(instance, data=user_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if profile_data:
            profile, created = Profile.objects.get_or_create(user=instance)
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
            
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

class ProfileViewSet(viewsets.GenericViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)
    
    def get_object(self):
        profile = Profile.objects.select_related('user').prefetch_related(
            'user__locations'
        ).get(user=self.request.user)
        print(f"User: {profile.user.id}")
        print(f"Locations count: {profile.user.locations.count()}")
        print(f"First location: {profile.user.locations.first()}")
        
        return profile
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
       
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        if request.method == 'GET':
            return self.retrieve(request)
        return self.update(request, partial=(request.method == 'PATCH'))
class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Location.objects.filter(user=self.request.user)
    
    @method_decorator(cache_page(60*5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    def perform_create(self, serializer):
        user = self.request.user
        
        with transaction.atomic():
            locations = Location.objects.filter(user=user).select_for_update()
            if locations.count() >= 4:
                raise ValidationError("Maximum limit of 4 locations reached")
            is_default = serializer.validated_data.get('is_default', False)
            if is_default:
                locations.filter(is_default=True).update(is_default=False)
            serializer.save(user=user)

    def get_object(self):
        profile = Profile.objects.select_related('user').prefetch_related(
            'user__locations'
        ).get(user=self.request.user)
        print(f"Profile user: {profile.user.id}")
        print(f"Locations count: {profile.user.locations.count()}")
        print(f"First location: {profile.user.locations.first()}") 
        
        #return profile
        return super().get_object()
    
    def perform_destroy(self, instance):
        if Location.objects.filter(user=self.request.user).count() <= 1:
            raise ValidationError("Cannot delete your last location")
        
        was_default = instance.is_default
        instance.delete()
        if was_default:
            new_default = Location.objects.filter(
                user=self.request.user
            ).first()
            if new_default:
                new_default.is_default = True
                new_default.save()
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set a location as the default"""
        location = self.get_object()
        Location.objects.filter(user=request.user, is_default=True).update(is_default=False)
        location.is_default = True
        location.save()
        
        serializer = self.get_serializer(location)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get the user's default location"""
        try:
            location = Location.objects.get(user=request.user, is_default=True)
            serializer = self.get_serializer(location)
            return Response(serializer.data)
        except Location.DoesNotExist:
            return Response({"detail": "No default location set"}, status=status.HTTP_404_NOT_FOUND) 
class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        language = serializer.save()
        return Response({
            "message": "Language created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
