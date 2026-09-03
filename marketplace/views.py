# marketplace/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

from .models import Category

@login_required
def home(request):
    categories = Category.objects.all()
    return render(request, 'home.html', {'categories': categories})
from .models import Item, Category
from .forms import ItemForm
from django.contrib.auth.decorators import login_required

def item_list(request):
    items = Item.objects.all().order_by('-posted_on')
    return render(request, 'item_list.html', {'items': items})

@login_required
def post_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            return redirect('item_list')
    else:
        form = ItemForm()
    return render(request, 'post_item.html', {'form': form})
from django.shortcuts import render
from .models import Item, Category, Wishlist  # Add Wishlist model
from django.contrib.auth.decorators import login_required

def item_list(request):
    query = request.GET.get('q')
    category_id = request.GET.get('category')

    items = Item.objects.all().order_by('-posted_on')

    if query:
        items = items.filter(title__icontains=query)

    if category_id and category_id != 'all':
        items = items.filter(category__id=category_id)

    # Add is_in_wishlist to each item
    user = request.user
    if user.is_authenticated:
        wishlist_item_ids = Wishlist.objects.filter(user=user).values_list('item_id', flat=True)
        for item in items:
            item.is_in_wishlist = item.id in wishlist_item_ids
    else:
        for item in items:
            item.is_in_wishlist = False

    categories = Category.objects.all()

    return render(request, 'item_list.html', {
        'items': items,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    })


@login_required
def my_items(request):
    items = Item.objects.filter(seller=request.user).order_by('-posted_on')
    return render(request, 'my_items.html', {'items': items})
from django.shortcuts import get_object_or_404
from django.contrib import messages

@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated successfully.")
            return redirect('my_items')
    else:
        form = ItemForm(instance=item)
    return render(request, 'edit_item.html', {'form': form})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted.")
        return redirect('my_items')
    return render(request, 'delete_item.html', {'item': item})
from .models import Wishlist

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_to_wishlist(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    Wishlist.objects.get_or_create(user=request.user, item=item)
    messages.success(request, "Item added to wishlist.")
    return redirect('item_list')

@login_required
def remove_from_wishlist(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    Wishlist.objects.filter(user=request.user, item=item).delete()
    messages.info(request, "Item removed from wishlist.")
    return redirect('wishlist')
from .models import Chat, Message
from django.db.models import Q

@login_required
def start_chat(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if item.seller == request.user:
        messages.error(request, "You can't chat about your own item.")
        return redirect('item_list')

    chat, created = Chat.objects.get_or_create(buyer=request.user, seller=item.seller, item=item)
    return redirect('chat_messages', chat_id=chat.id)

@login_required
def chat_messages(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user not in [chat.buyer, chat.seller]:
        return redirect('item_list')  # unauthorized access

    if request.method == 'POST':
        content = request.POST.get('content')
        if content.strip():
            Message.objects.create(chat=chat, sender=request.user, content=content)

    messages_list = chat.messages.order_by('sent_on')
    return render(request, 'chat_messages.html', {
        'chat': chat,
        'messages': messages_list,
    })

@login_required
def inbox(request):
    chats = Chat.objects.filter(Q(buyer=request.user) | Q(seller=request.user)).order_by('-created_on')
    return render(request, 'inbox.html', {'chats': chats})
from django.contrib.auth import logout
from django.shortcuts import redirect

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # redirect after signup
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
from django.shortcuts import render
from .models import Item, Wishlist, Chat  # import your models

def dashboard(request):
    user = request.user
    my_items = Item.objects.filter(owner=user)
    wishlist_items = Wishlist.objects.filter(user=user)
    message_threads = Chat.objects.filter(participants=user)
    recent_items = Item.objects.exclude(owner=user).order_by('-created_on')[:6]

    return render(request, 'dashboard.html', {
        'my_items': my_items,
        'wishlist_items': wishlist_items,
        'message_threads': message_threads,
        'recent_items': recent_items,
    })
from django.shortcuts import render
from .models import Item, Category

def item_list(request):
    query = request.GET.get('q', '')
    selected_category = request.GET.get('category', 'all')

    items = Item.objects.all()

    if query:
        items = items.filter(title__icontains=query)

    if selected_category != 'all':
        items = items.filter(category_id=selected_category)

    categories = Category.objects.all()

    # Optional: Add wishlist context logic here

    return render(request, 'item_list.html', {
        'items': items,
        'query': query,
        'categories': categories,
        'selected_category': selected_category,
    })




