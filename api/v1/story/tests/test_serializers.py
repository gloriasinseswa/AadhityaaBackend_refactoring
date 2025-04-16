from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from account.models import User, Story
from api.v1.story.serializer import StorySerializer, StoryCreateSerializer

class StorySerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.story = Story.objects.create(user=self.user)

    def test_story_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields"""
        serializer = StorySerializer(instance=self.story)
        expected_fields = {'id', 'user', 'images', 'created_at'}
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_story_create_serializer_validation(self):
        """Test story creation validation"""
        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        data = {'images': [image]}
        serializer = StoryCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_story_create_serializer_no_images(self):
        """Test story creation fails without images"""
        data = {'images': []}
        serializer = StoryCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('images', serializer.errors)

    def test_story_create_serializer_invalid_image(self):
        """Test story creation with invalid image type"""
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"text content",
            content_type="text/plain"
        )
        data = {'images': [invalid_file]}
        serializer = StoryCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
