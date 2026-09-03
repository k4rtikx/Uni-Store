# 🎓 Campus Market

A Django-powered peer-to-peer marketplace built for college students to **buy, sell, and chat** about second-hand items — all within their campus community.

---

## 🚀 Features

- **User Authentication** — Register, login, logout with Django's built-in auth system
- **Post Listings** — Sell books, gadgets, furniture, and more with images, price, and condition
- **Browse & Search** — Filter items by keyword or category
- **Wishlist** — Save items you're interested in for later
- **Real-time Inbox** — Built-in chat system between buyers and sellers per item
- **My Listings** — Manage your own posted items (edit / delete)
- **Category Browsing** — Explore items by category from the home page
- **Admin Panel** — Django admin for staff/superusers

---

## 🛠️ Tech Stack

| Layer      | Technology                  |
|------------|-----------------------------|
| Backend    | Python 3, Django 5.x        |
| Database   | SQLite (dev)                |
| Frontend   | Bootstrap 5, HTML/CSS       |
| Media      | Django media file handling  |
| Auth       | Django built-in auth        |

---

## 📁 Project Structure

```
campus_bazar/          # Django project config (settings, urls, wsgi)
marketplace/           # Main app (models, views, urls, forms)
  migrations/          # Database migrations
templates/             # HTML templates (base, home, item_list, chat, etc.)
  registration/        # Login, signup templates
media/                 # Uploaded item images
manage.py
```

---

## ⚙️ Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/campus-bazar.git
cd campus-bazar
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install django pillow
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (optional, for admin access)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

## 📸 Screenshots

> _Add screenshots of your home page, item listings, chat, and wishlist here._

---

## 🗂️ Data Models

| Model     | Description                                      |
|-----------|--------------------------------------------------|
| `Item`    | A listing with title, price, image, condition    |
| `Category`| Item categories (Books, Electronics, etc.)       |
| `Wishlist`| User's saved items                               |
| `Chat`    | Conversation thread between buyer and seller     |
| `Message` | Individual messages within a chat                |

---

## 🔐 Environment & Security Notes

- The `SECRET_KEY` in `settings.py` is for **development only** — replace it before deploying
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` for your domain
- Use PostgreSQL or another production-grade DB for deployment

---

## 📦 Requirements

```
Django>=5.0
Pillow
```

You can generate a full requirements file with:

```bash
pip freeze > requirements.txt
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

---

## 📄 License

[MIT](LICENSE)

---

> Built with ❤️ for campus communities.
