from django.test import TestCase
from faker import Faker
from account.models import Category, UserCategory, User
from api.v1.category.serializers import CategorySerializer, UserCategorySerializer
from rest_framework.test import APIRequestFactory

class CategorySerializerTest(TestCase):
    def setUp(self):
        """Initialize test data"""
        self.fake = Faker()
        self.category_data = {
            'name': self.fake.unique.word()
        }
        self.category = Category.objects.create(name=self.category_data['name'])

    def test_category_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        serializer = CategorySerializer(instance=self.category)
        expected_fields = {'id', 'name', 'created_at'}
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_category_serialization(self):
        """Test category serialization"""
        serializer = CategorySerializer(instance=self.category)
        self.assertEqual(serializer.data['name'], self.category_data['name'])

    def test_category_creation(self):
        """Test category creation through serializer"""
        new_category_data = {'name': self.fake.unique.word()}
        serializer = CategorySerializer(data=new_category_data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.name, new_category_data['name'])

class UserCategorySerializerTest(TestCase):
    def setUp(self):
        """Initialize test data"""
        self.fake = Faker()
        self.user = User.objects.create_user(
            email=self.fake.email(),
            password=self.fake.password(),
            first_name=self.fake.first_name(),
            last_name=self.fake.last_name()
        )
        self.category = Category.objects.create(name=self.fake.unique.word())
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

    def test_user_category_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        user_category = UserCategory.objects.create(
            user=self.user,
            category=self.category
        )
        serializer = UserCategorySerializer(
            instance=user_category,
            context={'request': self.request}
        )
        expected_fields = {'id', 'user', 'category', 'category_name', 'created_at'}
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_user_category_creation(self):
        """Test user category creation through serializer"""
        serializer = UserCategorySerializer(
            data={'category': self.category.id},
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        user_category = serializer.save()
        self.assertEqual(user_category.user, self.user)
        self.assertEqual(user_category.category, self.category)