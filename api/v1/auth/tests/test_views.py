from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from account.models import User, OTP, Profile

class AuthViewTests(TestCase):
    def setUp(self):
        """Initialize test client and test data"""
        self.client = APIClient()
        self.fake = Faker()
        self.user_data = {
            'email': self.fake.email(),
            'password': 'TestPass123!',
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'phone_number': self.fake.phone_number(),
            'gender': 'M',
            'date_of_birth': '1990-01-01'
        }
        
    def test_user_registration(self):
        """Test user registration flow"""
    
        url = reverse('accounts-list')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        user = User.objects.get(email=self.user_data['email'])
        self.assertFalse(user.is_active)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_otp_verification(self):
        """Test OTP verification flow"""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            is_active=False
        )
        
        otp = OTP.objects.create(
            user=user,
            otp='123456',
            type='ACCOUNT_VERIFICATION'
        )
        url = reverse('accounts-verify-otp')
        response = self.client.post(url, {'otp': '123456'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_login(self):
        """Test login functionality"""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )
        url = reverse('accounts-login')
        response = self.client.post(url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        url = reverse('accounts-login')
        response = self.client.post(url, {
            'email': self.fake.email(),
            'password': 'WrongPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_resend_verification(self):
        """Test resend verification functionality"""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            is_active=False
        )
        url = reverse('accounts-resend-verification')
        response = self.client.post(url, {'email': user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(OTP.objects.filter(user=user).exists())

    def test_password_reset(self):
        """Test password reset flow"""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )
        url = reverse('accounts-reset-password')
        new_password = 'NewPass123!'
        response = self.client.post(url, {
            'email': user.email,
            'new_password': new_password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))

    def test_protected_endpoint_access(self):
        """Test protected endpoint access with and without authentication"""
        user = User.objects.create_user(**self.user_data)
        url = reverse('accounts-detail', args=[user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        login_url = reverse('accounts-login')
        login_response = self.client.post(login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        token = login_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        """Clean up after tests"""
        User.objects.all().delete()
        OTP.objects.all().delete()
        Profile.objects.all().delete()