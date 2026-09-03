from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Item(models.Model):
    LISTING_TYPE_CHOICES = [
        ('lend',   'Lend (Free, return needed)'),
        ('donate', 'Donate (Free, keep it)'),
        ('share',  'Share / Common Use'),
        ('rent',   'Rent (Paid, return needed)'),
        ('buy',    'Buy / Sell (One-time purchase)'),
    ]
    CONDITION_CHOICES = [
        ('New',  'New'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)

    # Listing type — Lend / Donate / Share / Rent / Buy
    listing_type = models.CharField(
        max_length=10,
        choices=LISTING_TYPE_CHOICES,
        default='donate',
        verbose_name='Listing Type',
    )

    # Price when listing_type == 'buy'
    price = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=0,
        verbose_name='Buy Price (₹)',
        help_text='Price if listing for sale/buy',
    )

    # Price per day when listing_type == 'rent'
    rent_price_per_day = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=0,
        verbose_name='Rent Price per Day (₹)',
        help_text='Only fill this if you are renting the item',
    )

    condition = models.CharField(
        max_length=10,
        choices=CONDITION_CHOICES,
        default='Good',
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    posted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_rentable(self):
        return self.listing_type == 'rent'

    @property
    def is_for_sale(self):
        return self.listing_type == 'buy'

    @property
    def listing_type_badge(self):
        colors = {
            'lend':   ('#34d399', '🔄 Lend'),
            'donate': ('#6ee7b7', '🎁 Donate'),
            'share':  ('#818cf8', '🤝 Share'),
            'rent':   ('#fbbf24', '💰 Rent'),
            'buy':    ('#38bdf8', '🏷️ Buy'),
        }
        return colors.get(self.listing_type, ('#94a3b8', self.listing_type))

    class Meta:
        ordering = ['-posted_on']


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'item')

    def __str__(self):
        return f"{self.user.username} → {self.item.title}"


class Chat(models.Model):
    buyer = models.ForeignKey(User, related_name='chats_started', on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='chats_received', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat: {self.buyer.username} → {self.seller.username} ({self.item.title})"


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    sent_on = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} on {self.sent_on.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['sent_on']
