from django.contrib import admin
from .models import Item, Category, Wishlist, Chat, Message

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'listing_type', 'price', 'rent_price_per_day', 'condition', 'category', 'posted_on']
    search_fields = ['title', 'description']
    list_filter = ['listing_type', 'category', 'condition']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'item']

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'seller', 'item', 'created_on']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['chat', 'sender', 'content', 'sent_on']
