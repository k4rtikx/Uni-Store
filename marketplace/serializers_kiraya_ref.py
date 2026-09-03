from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Item, Category, UserProfile, WishList, ItemImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class ItemSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    image_url = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'title', 'description', 'price', 'listing_type', 'listing_type_display',
            'condition', 'condition_display', 'status', 'location', 'category', 'category_name',
            'seller', 'image_url', 'gallery', 'views', 'created_at', 'is_wishlisted'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        image = obj.display_image
        if image and request:
            return request.build_absolute_uri(image.url)
        return None

    def get_gallery(self, obj):
        request = self.context.get('request')
        images = []
        for image in obj.gallery_images:
            image_url = request.build_absolute_uri(image.image.url) if request else image.image.url
            images.append({
                'id': image.id,
                'url': image_url,
                'is_primary': image.is_primary,
                'sort_order': image.sort_order,
            })
        return images

    def get_is_wishlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return WishList.objects.filter(user=request.user, item=obj).exists()
        return False


class ItemCreateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Item
        fields = ['title', 'description', 'price', 'listing_type', 'condition', 'category', 'location', 'image']

    def create(self, validated_data):
        image_file = validated_data.get('image')
        validated_data['seller'] = self.context['request'].user
        item = super().create(validated_data)
        if image_file and item.image:
            ItemImage.objects.create(
                item=item,
                image=item.image.name,
                is_primary=True,
                sort_order=0,
            )
        return item
