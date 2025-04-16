from rest_framework import serializers

from account.models import Category, UserCategory
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name','created_at']

class UserCategorySerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = UserCategory
        fields = ['id', 'user', 'category', 'category_name', 'created_at']
        read_only_fields = ['id', 'created_at']
