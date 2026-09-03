from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='📦')

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    @property
    def display_icon(self):
        if self.icon and self.icon != '??':
            return self.icon
        return '📦'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    hostel = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} Profile'


class Item(models.Model):
    LISTING_TYPE = [
        ('sell', 'For Sale'),
        ('rent', 'For Rent'),
        ('free', 'Free / Giveaway'),
    ]
    CONDITION = [
        ('new', 'Brand New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
    ]
    STATUS = [
        ('active', 'Active'),
        ('sold', 'Sold/Rented'),
        ('inactive', 'Inactive'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE, default='sell')
    condition = models.CharField(max_length=10, choices=CONDITION, default='good')
    status = models.CharField(max_length=10, choices=STATUS, default='active')
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    @property
    def gallery_images(self):
        return self.images.order_by('-is_primary', 'sort_order', 'id')

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).order_by('sort_order', 'id').first()
        if primary:
            return primary
        return self.images.order_by('sort_order', 'id').first()

    @property
    def display_image(self):
        primary = self.primary_image
        if primary:
            return primary.image
        return self.image

    class Meta:
        ordering = ['-created_at']


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='items/')
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.item.title} Image {self.pk}'


class WishList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')

    def __str__(self):
        return f'{self.user.username} -> {self.item.title}'


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} -> {self.receiver}: {self.content[:40]}'

    class Meta:
        ordering = ['created_at']
