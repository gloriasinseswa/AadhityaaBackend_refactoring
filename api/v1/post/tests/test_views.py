from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from account.models import User, Post, Category, Location, Like, Comment
from django.urls import reverse

class PostViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
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
        self.client.force_authenticate(user=self.user)

    def test_create_text_post(self):
        """Test creating a text post"""
        url = reverse('posts-list')
        data = {
            'content_type': 'text',
            'text_content': 'Test content',
            'categories': [str(self.category.id)],
            'zip_code': [str(self.location.id)]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().text_content, 'Test content')

    def test_create_media_post(self):
        """Test creating a media post"""
        url = reverse('posts-list')
        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        data = {
            'content_type': 'image',
            'media_file': image,
            'categories': [str(self.category.id)],
            'zip_code': [str(self.location.id)]
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_like_post(self):
        """Test liking and unliking a post"""
        post = Post.objects.create(
            user=self.user,
            content_type='text',
            text_content='Test post'
        )
        url = reverse('posts-like', kwargs={'pk': post.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Like.objects.count(), 1)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Like.objects.count(), 0)

    def test_add_comment(self):
        """Test adding a comment to a post"""
        post = Post.objects.create(
            user=self.user,
            content_type='text',
            text_content='Test post'
        )
        url = reverse('posts-comments', kwargs={'pk': post.id})
        data = {'content': 'Test comment'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_list_posts(self):
        """Test listing posts"""
        Post.objects.create(user=self.user, content_type='text', text_content='Test post 1')
        Post.objects.create(user=self.user, content_type='text', text_content='Test post 2')
        
        url = reverse('posts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_update_post(self):
        """Test updating a post"""
        post = Post.objects.create(
            user=self.user,
            content_type='text',
            text_content='Original content'
        )
        url = reverse('posts-detail', kwargs={'pk': post.id})
        data = {'text_content': 'Updated content', 'content_type': 'text'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Post.objects.get(id=post.id).text_content, 'Updated content')

    def test_delete_post(self):
        """Test deleting a post"""
        post = Post.objects.create(
            user=self.user,
            content_type='text',
            text_content='Test post'
        )
        url = reverse('posts-detail', kwargs={'pk': post.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_unauthorized_post_modification(self):
        """Test unauthorized post modification"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='pass123',
            first_name='Other',
            last_name='User'
        )
        post = Post.objects.create(
            user=other_user,
            content_type='text',
            text_content='Other user post'
        )
        
        url = reverse('posts-detail', kwargs={'pk': post.id})
        data = {'text_content': 'Try to update', 'content_type': 'text'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_post_creation(self):
        """Test invalid post creation scenarios"""
        url = reverse('posts-list')
        
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {
            'content_type': 'invalid_type',
            'text_content': 'Test content'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_operations(self):
        """Test comment operations"""
        post = Post.objects.create(
            user=self.user,
            content_type='text',
            text_content='Test post'
        )
        
        url = reverse('posts-comments', kwargs={'pk': post.id})
        response = self.client.post(url, {'comment_text': 'Test comment'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
        response = self.client.post(url, {'comment_text': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.first()
        self.assertEqual(comment.comment_text, 'Test comment')
        self.assertEqual(comment.user, self.user)
