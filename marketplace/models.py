from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Item(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='item_images/')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    posted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'item')  # prevent duplicates

    def __str__(self):
        return f"{self.user.username} → {self.item.title}"
    from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return f"Message from {self.sender.username} on {self.sent_on.strftime('%Y-%m-%d %H:%M')}"


