from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from faker import Faker
from account.models import Category, User, UserCategory

class CategoryViewTests(TestCase):
    def setUp(self):
        """Initialize test client and test data"""
        self.client = APIClient()
        self.fake = Faker()
        
        self.user = User.objects.create_user(
            email=self.fake.email(),
            password=self.fake.password(),
            first_name=self.fake.first_name(),
            last_name=self.fake.last_name()
        )
        self.category = Category.objects.create(name=self.fake.unique.word())
        self.client.force_authenticate(user=self.user)

    def test_list_categories(self):
        """Test retrieving list of categories"""
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Category.objects.count())

    def test_create_category(self):
        """Test creating a new category"""
        url = reverse('category-list')
        data = {'name': self.fake.unique.word()}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.filter(name=data['name']).exists(), True)

    def test_retrieve_category(self):
        """Test retrieving a specific category"""
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.category.name)

    def test_update_category(self):
        """Test updating a category"""
        url = reverse('category-detail', args=[self.category.id])
        new_name = self.fake.unique.word()
        response = self.client.put(url, {'name': new_name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, new_name)

    def test_delete_category(self):
        """Test deleting a category"""
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.filter(id=self.category.id).exists(), False)

    def test_featured_categories(self):
        """Test retrieving featured categories"""
        url = reverse('category-featured')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access(self):
        """Test unauthorized access to category endpoints"""
        self.client.logout()
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def tearDown(self):
        """Clean up test data"""
        Category.objects.all().delete()
        User.objects.all().delete()