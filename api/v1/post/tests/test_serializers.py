from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from account.models import User, Post, Category, Location, Comment
from api.v1.post.serializers import PostSerializer, CommentSerializer, LikeSerializer

class PostSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.category = Category.objects.create(name='Test Category')
        self.location = Location.objects.create(
            user=self.user,
            country='Test Country',
            state='Test State',
            district='Test District',
            zipCode='12345'
        )

    def test_validate_text_post(self):
        """Test text post validation"""
        data = {
            'content_type': 'text',
            'text_content': 'Test content',
            'categories': [self.category.id],
            'zip_code': [self.location.id]
        }
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_validate_media_post(self):
        """Test media post validation"""
        media = SimpleUploadedFile(
            "test_file.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        data = {
            'content_type': 'image',
            'media_file': media,
            'categories': [self.category.id],
            'zip_code': [self.location.id]
        }
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_content_type(self):
        """Test invalid content type validation"""
        data = {
            'content_type': 'invalid',
            'text_content': 'Test content',
            'categories': [self.category.id],
            'zip_code': [self.location.id]
        }
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_validate_invalid_content_type(self):
        """Test validation rejects invalid content type"""
        data = {
            'content_type': 'invalid',
            'text_content': 'Test content',
            'categories': [self.category.id],
            'zip_code': [self.location.id]
        }
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content_type', serializer.errors)

    def test_validate_empty_content(self):
        """Test validation requires content based on content_type"""
        data = {
            'content_type': 'text',
            'text_content': '',
            'categories': [self.category.id],
            'zip_code': [self.location.id]
        }
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('text_content', serializer.errors)

    def test_validate_missing_media(self):
        """Test validation requires media file for media posts"""
        data = {
            'content_type': 'image',
            'categories': [self.category.id],
            'zip_code': [self.location.id]
        }
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('media_file', serializer.errors)

class CommentSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            user=self.user,
            content_type='text',
            text_content='Test post'
        )

    def test_comment_serializer_create(self):
        """Test creating a comment through serializer"""
        data = {
            'post': self.post.id,
            'comment_text': 'Test comment'
        }
        serializer = CommentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        comment = serializer.save(user=self.user)
        self.assertEqual(comment.comment_text, 'Test comment')
        self.assertEqual(comment.user, self.user)

    def test_comment_serializer_invalid_data(self):
        """Test comment serializer with invalid data"""
        data = {
            'post': self.post.id,
            'comment_text': ''  # Empty comment should be invalid
        }
        serializer = CommentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
