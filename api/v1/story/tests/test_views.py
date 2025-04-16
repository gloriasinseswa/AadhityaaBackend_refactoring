from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from account.models import User, Story, StoryImage
from django.urls import reverse

class StoryViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_story(self):
        """Test creating a story with images"""
        url = reverse('story-list')
        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        data = {
            'images': [image]
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Story.objects.count(), 1)
        self.assertEqual(StoryImage.objects.count(), 1)

    def test_list_stories(self):
        """Test listing stories"""
        Story.objects.create(user=self.user)
        url = reverse('story-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_story(self):
        """Test deleting a story"""
        story = Story.objects.create(user=self.user)
        url = reverse('story-detail', kwargs={'pk': story.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Story.objects.count(), 0)

    def test_delete_other_user_story(self):
        """Test attempting to delete another user's story"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='pass123',
            first_name='Other',
            last_name='User'
        )
        story = Story.objects.create(user=other_user)
        url = reverse('story-detail', kwargs={'pk': story.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_story_invalid_image(self):
        """Test creating a story with invalid image"""
        url = reverse('story-list')
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"invalid file content",
            content_type="text/plain"
        )
        data = {'images': [invalid_file]}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_story_expiry(self):
        """Test story expiry functionality"""
        from django.utils import timezone
        from datetime import timedelta
        
        old_story = Story.objects.create(user=self.user)
        old_story.created_at = timezone.now() - timedelta(hours=25)
        old_story.save()
        
        new_story = Story.objects.create(user=self.user)
        
        url = reverse('story-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_multiple_images(self):
        """Test creating a story with multiple images"""
        url = reverse('story-list')
        image1 = SimpleUploadedFile(
            "test1.jpg",
            b"file_content_1",
            content_type="image/jpeg"
        )
        image2 = SimpleUploadedFile(
            "test2.jpg",
            b"file_content_2",
            content_type="image/jpeg"
        )
        data = {'images': [image1, image2]}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StoryImage.objects.count(), 2)

    def test_unauthorized_access(self):
        """Test unauthorized access to stories"""
        self.client.force_authenticate(user=None)
        
        url = reverse('story-list')
        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        response = self.client.post(url, {'images': [image]}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
