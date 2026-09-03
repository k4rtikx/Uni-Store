# marketplace/views.py — Uni-Store (EduWaste Loop)
# Clean rewrite: removed duplicate function definitions, fixed broken dashboard

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Category, Item, Wishlist, Chat, Message
from .forms import ItemForm


# ─── Auth ────────────────────────────────────────────────────────────────────

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


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Home / Browse ───────────────────────────────────────────────────────────

@login_required
def home(request):
    categories = Category.objects.all()
    return render(request, 'home.html', {'categories': categories})


def item_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', 'all')

    items = Item.objects.all().order_by('-posted_on')

    if query:
        items = items.filter(title__icontains=query)

    if category_id and category_id != 'all':
        items = items.filter(category__id=category_id)

    # Wishlist status per item for authenticated users
    if request.user.is_authenticated:
        wishlist_item_ids = Wishlist.objects.filter(user=request.user).values_list('item_id', flat=True)
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


# ─── Item CRUD ───────────────────────────────────────────────────────────────

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


@login_required
def my_items(request):
    items = Item.objects.filter(seller=request.user).order_by('-posted_on')
    return render(request, 'my_items.html', {'items': items})


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


# ─── Dashboard ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    # Fixed: use 'seller' (not 'owner'), use correct Chat query
    my_items = Item.objects.filter(seller=user).order_by('-posted_on')
    wishlist_items = Wishlist.objects.filter(user=user).select_related('item')
    message_threads = Chat.objects.filter(
        Q(buyer=user) | Q(seller=user)
    ).order_by('-created_on')
    recent_items = Item.objects.exclude(seller=user).order_by('-posted_on')[:6]

    return render(request, 'dashboard.html', {
        'my_items': my_items,
        'wishlist_items': wishlist_items,
        'message_threads': message_threads,
        'recent_items': recent_items,
    })


# ─── Wishlist ────────────────────────────────────────────────────────────────

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('item')
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


# ─── Chat / Inbox ─────────────────────────────────────────────────────────────

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
        return redirect('item_list')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(chat=chat, sender=request.user, content=content)

    messages_list = chat.messages.order_by('sent_on')
    return render(request, 'chat_messages.html', {
        'chat': chat,
        'messages': messages_list,
    })


@login_required
def inbox(request):
    chats = Chat.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_on')
    return render(request, 'inbox.html', {'chats': chats})

