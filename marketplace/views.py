# marketplace/views.py — Uni-Store (EduWaste Loop)
# Clean rewrite: removed duplicate function definitions, fixed broken dashboard

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Category, Item, Wishlist, Chat, Message
from .forms import ItemForm
from .ai_search import run_ai_search


# ─── Auth ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email_or_user = request.POST.get('email') or request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=email_or_user, password=password)
        if user is None:
            user_obj = User.objects.filter(email=email_or_user).first() or User.objects.filter(username=email_or_user).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'registration/login.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Account created successfully!")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def signup(request):
    return register(request)


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('home')


# ─── Home / Browse ───────────────────────────────────────────────────────────

@login_required
def home(request):
    categories = Category.objects.all()
    return render(request, 'home.html', {'categories': categories})


def item_list(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', 'all')
    listing_type = request.GET.get('type', 'all')

    ai_narration = None
    ai_clarification = None

    if query:
        # Run unified AI search
        ai_items, ai_narration, ai_clarification = run_ai_search(query, request.session)
        item_ids = [item['id'] for item in ai_items]

        if item_ids:
            items_dict = {
                item.id: item
                for item in Item.objects.filter(id__in=item_ids).select_related('category', 'seller')
            }
            items = [items_dict[iid] for iid in item_ids if iid in items_dict]
        else:
            items = []
    else:
        items = list(Item.objects.select_related('category', 'seller').all().order_by('-posted_on'))

    # Optional Category filter refinement
    if category_id and category_id != 'all':
        try:
            cat_id = int(category_id)
            items = [i for i in items if i.category and i.category.id == cat_id]
        except (ValueError, TypeError):
            items = [i for i in items if i.category and category_id.lower() in i.category.name.lower()]

    # Optional Listing type filter refinement
    if listing_type and listing_type != 'all':
        items = [i for i in items if i.listing_type == listing_type]

    # Wishlist status per item for authenticated users
    if request.user.is_authenticated:
        wishlist_item_ids = set(Wishlist.objects.filter(user=request.user).values_list('item_id', flat=True))
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
        'selected_type': listing_type,
        'ai_narration': ai_narration,
        'ai_clarification': ai_clarification,
    })


# ─── Unified AI Search API ───────────────────────────────────────────────────

@csrf_exempt
def ai_search_api(request):
    """
    Unified AI Search endpoint.
    Accepts GET / POST with query string or JSON payload.
    Returns JSON with products, AI narration on availability, and clarification questions.
    """
    query = ""
    if request.method == "POST":
        try:
            if request.content_type and "application/json" in request.content_type:
                data = json.loads(request.body.decode("utf-8"))
                query = data.get("query", "")
            else:
                query = request.POST.get("q", "") or request.POST.get("query", "")
        except Exception:
            query = request.POST.get("q", "")
    else:
        query = request.GET.get("q", "") or request.GET.get("query", "")

    query = (query or "").strip()
    if not query:
        return JsonResponse({
            "success": False,
            "error": "Query cannot be empty",
            "items": [],
            "narration": None,
            "clarification": None,
        })

    items, narration, clarification = run_ai_search(query, request.session)

    return JsonResponse({
        "success": True,
        "query": query,
        "items": items,
        "narration": narration,
        "clarification": clarification,
        "count": len(items),
    })


def ai_search_clear(request):
    """Resets the AI chat search conversation history in session."""
    if "ai_search_history" in request.session:
        request.session["ai_search_history"] = []
        request.session.modified = True
    return JsonResponse({"success": True, "message": "Conversation history cleared"})


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
    my_items = Item.objects.filter(seller=user).order_by('-posted_on')
    purchased_items = Item.objects.filter(buyer=user).order_by('-posted_on')
    wishlist_items = Wishlist.objects.filter(user=user).select_related('item')
    message_threads = Chat.objects.filter(
        Q(buyer=user) | Q(seller=user)
    ).order_by('-created_on')
    recent_items = Item.objects.exclude(seller=user).order_by('-posted_on')[:6]

    return render(request, 'dashboard.html', {
        'my_items': my_items,
        'purchased_items': purchased_items,
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
