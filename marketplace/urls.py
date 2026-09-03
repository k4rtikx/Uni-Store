# marketplace/urls.py
from django.urls import path
from . import views
   

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('items/', views.item_list, name='item_list'),
    path('items/new/', views.post_item, name='post_item'),
    path('my-items/', views.my_items, name='my_items'),
    path('items/<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('items/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:item_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('chat/<int:item_id>/', views.start_chat, name='start_chat'),
    path('chat/<int:chat_id>/messages/', views.chat_messages, name='chat_messages'),
    path('inbox/', views.inbox, name='inbox'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),


]


