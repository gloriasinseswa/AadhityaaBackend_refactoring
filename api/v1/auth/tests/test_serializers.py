from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from faker import Faker
from account.models import User, Location, Profile, OTP
from api.v1.auth.serializers import (
    CreateAccountSerializer,
    CustomAuthTokenSerializer,
    LoginSerializer,
    VerifyOTPSerializer,
    LocationSerializer
)

class AuthSerializerTestCase(TestCase):
    def setUp(self):
        """Initialize faker and common test data"""
        self.fake = Faker()
        self.password = self.fake.password(length=12)
        self.user = User.objects.create_user(
            email=self.fake.email(),
            password=self.password,
            first_name=self.fake.first_name(),
            last_name=self.fake.last_name()
        )

class CreateAccountSerializerTest(AuthSerializerTestCase):
    def setUp(self):
        """Set up test data using faker"""
        super().setUp()
        self.valid_data = {
            'email': self.fake.email(),
            'password': self.fake.password(length=12, special_chars=True),
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'phone_number': self.fake.phone_number(),
            'gender': self.fake.random_element(elements=('M', 'F', 'O')),
            'date_of_birth': self.fake.date()
        }

    def test_valid_create_account(self):
        """Test creating account with valid data"""
        serializer = CreateAccountSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.email, self.valid_data['email'])
        self.assertEqual(user.first_name, self.valid_data['first_name'])
        self.assertEqual(user.profile.phone_number, self.valid_data['phone_number'])

    def test_duplicate_email(self):
        """Test validation for duplicate email"""
        serializer = CreateAccountSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        duplicate_data = self.valid_data.copy()
        serializer = CreateAccountSerializer(data=duplicate_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

class LoginSerializerTest(AuthSerializerTestCase):
    def test_valid_login(self):
        """Test login with valid credentials"""
        credentials = {
            'email': self.user.email,
            'password': self.password
        }
        serializer = LoginSerializer(data=credentials)
        self.assertTrue(serializer.is_valid())

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        invalid_credentials = {
            'email': self.user.email,
            'password': self.fake.password()
        }
        serializer = LoginSerializer(data=invalid_credentials)
        self.assertFalse(serializer.is_valid())

class LocationSerializerTest(AuthSerializerTestCase):
    def setUp(self):
        super().setUp()
        self.valid_location_data = {
            'country': self.fake.country(),
            'state': self.fake.state(),
            'district': self.fake.city(),
            'zipCode': self.fake.postcode()
        }

    def test_valid_location(self):
        """Test creating location with valid data"""
        serializer = LocationSerializer(data=self.valid_location_data)
        self.assertTrue(serializer.is_valid())
        location = serializer.save()
        
        self.assertEqual(location.country, self.valid_location_data['country'])
        self.assertEqual(location.state, self.valid_location_data['state'])

class VerifyOTPSerializerTest(AuthSerializerTestCase):
    def setUp(self):
        super().setUp()
        self.otp_code = self.fake.numerify(text='######')  
        self.otp = OTP.objects.create(
            user=self.user,
            otp=self.otp_code,
            type='ACCOUNT_VERIFICATION'
        )

    def test_valid_otp(self):
        """Test OTP verification with valid code"""
        serializer = VerifyOTPSerializer(data={'otp': self.otp_code})
        self.assertTrue(serializer.is_valid())

    def test_expired_otp(self):
        """Test expired OTP verification"""
        import datetime
        from django.utils import timezone
        self.otp.created_at = timezone.now() - datetime.timedelta(minutes=15)
        self.otp.save()

        serializer = VerifyOTPSerializer(data={'otp': self.otp_code})
        self.assertFalse(serializer.is_valid())