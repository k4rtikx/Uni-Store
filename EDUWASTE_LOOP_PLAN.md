# 🌿 EduWaste Loop — Build Status & Plan
> **Hackathon Build Plan** | Django + React + PostgreSQL + Gemini API  
> Last updated: September 2026

---

## 📋 Quick Status Summary

| Layer | Status |
|---|---|
| Auth (register / login / logout) | ✅ EXISTS — Django templates, needs DRF conversion |
| Item listing (browse / post / edit / delete) | ✅ EXISTS — needs model rename + new fields |
| Category system | ✅ EXISTS — basic, needs expansion |
| Wishlist | ✅ EXISTS — repurpose as Resource Watchlist |
| Chat / Inbox | ✅ EXISTS — keep as-is, lower priority |
| Django REST Framework API | ❌ NOT BUILT |
| JWT Authentication | ❌ NOT BUILT |
| Resource model (Lend/Donate/Share) | ❌ NOT BUILT |
| Gemini Image Analysis | ❌ NOT BUILT |
| Gemini NL Resource Matching | ❌ NOT BUILT |
| Gemini Reuse Advisor | ❌ NOT BUILT |
| Amazon / Flipkart Fallback Links | ❌ NOT BUILT |
| Sustainability Impact Dashboard | ❌ NOT BUILT |
| QR Code Generation | ❌ NOT BUILT |
| Green Points / Badges | ❌ NOT BUILT |
| React Frontend (Vite) | ❌ NOT BUILT |
| PostgreSQL | ❌ NOT CONFIGURED (SQLite only) |

---

## ✅ WHAT ALREADY EXISTS (Audited from Code)

### Project: `campus-market` (this repo)
**Django project name:** `campus_bazar`  
**Main app:** `marketplace/`

---

### ✅ Models (`marketplace/models.py`)

| Model | Fields | Notes |
|---|---|---|
| `Category` | `name` | Simple, working |
| `Item` | `seller`, `title`, `description`, `image`, `price`, `condition`, `category`, `posted_on` | Has `price` field — needs to become free/lend resource |
| `Wishlist` | `user`, `item` | Working, `unique_together` enforced |
| `Chat` | `buyer`, `seller`, `item`, `created_on` | Working |
| `Message` | `chat`, `sender`, `content`, `sent_on` | Working |

> ⚠️ **Known Bug:** `models.py` has duplicate `from django.db import models` import stuck inside the `Wishlist` class body (line 31). File needs cleanup or it will cause import errors.

---

### ✅ Views (`marketplace/views.py`)

| View | Route | Status |
|---|---|---|
| `register` | `/register/` | ✅ Working |
| `home` | `/` | ✅ Working (shows categories) |
| `item_list` | `/items/` | ✅ Working (search + category filter) |
| `post_item` | `/items/new/` | ✅ Working |
| `my_items` | `/my-items/` | ✅ Working |
| `edit_item` | `/items/<id>/edit/` | ✅ Working |
| `delete_item` | `/items/<id>/delete/` | ✅ Working |
| `wishlist_view` | `/wishlist/` | ✅ Working |
| `add_to_wishlist` | `/wishlist/add/<id>/` | ✅ Working |
| `remove_from_wishlist` | `/wishlist/remove/<id>/` | ✅ Working |
| `start_chat` | `/chat/<item_id>/` | ✅ Working |
| `chat_messages` | `/chat/<chat_id>/messages/` | ✅ Working |
| `inbox` | `/inbox/` | ✅ Working |
| `logout_view` | `/logout/` | ✅ Working |
| `signup` | `/signup/` | ✅ Working |
| `dashboard` | `/dashboard/` | ❌ BROKEN — uses `Item.objects.filter(owner=user)` but field is `seller`; also uses `Chat.objects.filter(participants=user)` which doesn't exist |

> ⚠️ **Known Bug:** `views.py` has duplicate function definitions — `item_list` is defined 3 times, and imports are scattered throughout the file instead of at the top. Needs a clean rewrite.

---

### ✅ Settings (`campus_bazar/settings.py`)

| Setting | Value | Notes |
|---|---|---|
| Django version | 5.2.4 | ✅ Good |
| Database | SQLite3 | ⚠️ Upgrade to PostgreSQL for prod |
| `INSTALLED_APPS` | `marketplace` only | ❌ Missing: `rest_framework`, `corsheaders` |
| `MEDIA_URL` / `MEDIA_ROOT` | ✅ Configured | Image uploads work |
| Templates DIR | ✅ Configured | Will be replaced by React frontend |
| Login/Logout redirects | ✅ Configured | Will be replaced by JWT |

---

### ✅ URLs (`marketplace/urls.py`)

All routes are registered and working under Django template-based views.

---

## ❌ WHAT WE ARE BUILDING

---

### Phase 0 — Cleanup & Foundation 🔧
> Fix existing code before adding anything new.

- [ ] Fix `marketplace/models.py` — remove duplicate import block stuck inside `Wishlist` class (around line 31)
- [ ] Fix `marketplace/views.py` — remove duplicate `item_list` definitions, fix `dashboard` view (`owner` → `seller`, remove broken `participants` filter), consolidate all imports at the top
- [ ] Install all required packages:
  ```
  pip install djangorestframework djangorestframework-simplejwt
  pip install django-cors-headers google-generativeai
  pip install qrcode[pil] psycopg2-binary python-decouple Pillow
  ```
- [ ] Add to `INSTALLED_APPS`: `rest_framework`, `corsheaders`, `rest_framework_simplejwt`
- [ ] Add CORS + JWT settings to `campus_bazar/settings.py`
- [ ] Create `.env` with `GEMINI_API_KEY`, `SECRET_KEY`, `DATABASE_URL`
- [ ] Confirm Django starts clean: `python manage.py runserver`

---

### Phase 1 — Core Resource API 🏗️

**New app: `resources/`**

#### Models to build:

| Model | Key Fields |
|---|---|
| `ResourceCategory` | `name`, `slug`, `icon` |
| `Resource` | `posted_by`, `title`, `description`, `category`, `resource_type` (Lend / Donate / Share), `status` (Available / Reserved / Given Away / Expired), `image`, `gemini_metadata` (JSONField), `pickup_location`, `available_until`, `qr_code`, `estimated_value_inr`, `co2_saved_kg` |
| `ResourceTransaction` | `resource`, `given_by`, `received_by`, `transaction_type`, `return_due_date`, `returned`, `value_inr`, `co2_saved_kg` |

#### Extend existing:

- [ ] **`UserProfile`** — add `department`, `year_of_study`, `role` (student / faculty / department), `college_email`, `green_points`
- [ ] **`GreenBadge` model** — `user`, `badge_type`, `awarded_at`

#### DRF endpoints:

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login → JWT token |
| POST | `/api/auth/logout/` | Logout |
| GET/PATCH | `/api/auth/profile/` | View / update profile |
| GET | `/api/resources/` | List all available resources |
| POST | `/api/resources/` | Post a new resource |
| GET | `/api/resources/{id}/` | Resource detail |
| PATCH | `/api/resources/{id}/` | Update resource |
| DELETE | `/api/resources/{id}/` | Delete resource |
| GET | `/api/resources/my/` | My posted resources |
| GET | `/api/resources/categories/` | All categories |

---

### Phase 2 — Gemini AI Integration 🤖

**New app: `ai/`**

#### Functions to build in `ai/gemini.py`:

**1. Resource Photo Analysis**
```
Trigger:  user uploads image when posting a resource
Input:    image file (optional description)
Output:   { resource_name, category, condition, likely_users,
            potential_reuse, safety_notes, estimated_value_inr }
Stored:   Resource.gemini_metadata (JSONField)
UX:       Gemini auto-fills the form — user just confirms/edits
```

**2. Natural Language Resource Matching** ← THE CORE FEATURE
```
Trigger:  student types free-text resource request
Input:    raw_request_text + all available Resources from DB
Output:   { intent, resource_type, subject, topics, urgency,
            reasoning, recommendation_strategy,
            recommended_resources[{resource_id, match_reason, match_score}] }
```

**3. Amazon / Flipkart Fallback** (when no campus match)
```
IF recommendation_strategy == "no_match_found":
    search_query = subject + resource_type + topics
    → amazon.in/s?k=<encoded_query>
    → flipkart.com/search?q=<encoded_query>
    → Show fallback card with CTA: "Buy it → donate it later!"
```

**4. Reuse Advisor** ← add if time allows
```
Trigger:  department admin describes items they want to dispose of
Input:    description + pending campus resource requests
Output:   { item_summary, potential_users, reuse_scenarios,
            estimated_cost_avoided_inr, estimated_waste_kg,
            urgency_to_post, suggested_post_title, suggested_category }
```

#### New models:

| Model | Key Fields |
|---|---|
| `ResourceRequest` | `requested_by`, `raw_request_text`, `gemini_analysis` (JSONField), `status`, `matched_resources` (M2M via ResourceMatch), `fallback_amazon_url`, `fallback_flipkart_url`, `fallback_search_query` |
| `ResourceMatch` | `request`, `resource`, `match_score` (0.0–1.0), `match_reason` |

#### AI endpoints:

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ai/analyze-image/` | Upload photo → Gemini auto-fill metadata |
| POST | `/api/ai/match-request/` | NL text → matched resources + reasoning |
| POST | `/api/ai/reuse-advisor/` | Items description → reuse recommendation |
| POST | `/api/requests/` | Submit a resource request |
| GET | `/api/requests/` | My submitted requests |
| GET | `/api/requests/{id}/` | Request detail + AI matches |

---

### Phase 3 — Sustainability & QR 🌍

**New app: `impact/`**

#### CO₂ Calculation (hardcoded — no Gemini needed):

```python
CO2_FACTORS = {
    'Textbooks': 2.5,        # kg CO2 saved per book reused
    'Lab Equipment': 15.0,
    'Electronics': 8.0,
    'Stationery': 0.3,
    'Research Materials': 1.5,
    'Furniture': 25.0,
    'Other': 3.0,
}
```

#### New model:

| Model | Key Fields |
|---|---|
| `SustainabilityImpact` | `total_resources_posted`, `total_resources_reused`, `total_money_saved_inr`, `total_co2_saved_kg`, `calculated_at` |

#### Dashboard metrics:
- 🌱 Total Resources Shared
- ♻️ Resources Successfully Reused
- 💰 Total Money Saved (₹)
- 🌍 CO₂ Prevented (kg → trees equivalent)
- 🏆 Top Contributors leaderboard
- 📊 Category breakdown chart
- 🗓️ Weekly trend graph

#### QR Code system:
- [ ] Auto-generate QR on resource save (signals.py + `qrcode[pil]`)
- [ ] QR encodes: `https://yourdomain.com/api/qr/verify/{resource_id}/`
- [ ] Scan → see resource details + "Verify Receipt" button
- [ ] Verified receipt marks `ResourceTransaction` as confirmed

#### Impact endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/impact/` | Platform-wide sustainability metrics |
| GET | `/api/impact/my/` | Personal impact metrics |
| GET | `/api/resources/{id}/qr/` | Get / generate QR code for resource |
| GET | `/api/qr/verify/{code}/` | Scan QR → resource detail |

---

### Phase 4 — React Frontend (Vite) ⚛️

**New project: `hackathon-frontend/`** (separate directory, not inside this repo)

#### Pages:

| Page | Route | What it does |
|---|---|---|
| `Home.jsx` | `/` | Browse resources, keyword search, category filter |
| `PostResource.jsx` | `/post` | Post form + "✨ Analyze with Gemini" button |
| `FindResource.jsx` | `/find` | NL search input → AI ranked results OR fallback card |
| `ResourceDetail.jsx` | `/resources/:id` | Full resource detail + QR code + Request button |
| `Dashboard.jsx` | `/dashboard` | Sustainability metrics with charts |
| `Profile.jsx` | `/profile` | Green points, badges, my resources |
| `Login.jsx` | `/login` | JWT login |
| `Register.jsx` | `/register` | Registration |

#### Components:

| Component | Purpose |
|---|---|
| `ResourceCard.jsx` | Card for each resource (type badge, condition, location) |
| `GeminiMatchResult.jsx` | Match score bar + Gemini's reasoning text |
| `FallbackPurchaseCard.jsx` | Amazon / Flipkart card when no campus match |
| `SustainabilityMetric.jsx` | Single metric tile (icon + animated number) |
| `QRCodeDisplay.jsx` | Shows QR image + verify link for a resource |

#### API service layer (`src/api/`):

- [ ] `auth.js` — register, login, logout, profile
- [ ] `resources.js` — CRUD, categories, my resources
- [ ] `ai.js` — analyze-image, match-request, reuse-advisor
- [ ] `requests.js` — submit/view requests
- [ ] `impact.js` — platform metrics, personal metrics

---

### Phase 5 — Polish & Deploy 🚀

- [ ] Seed database with 20+ sample resources across all categories
- [ ] End-to-end test: Post → Gemini Analyze → Browse → NL Search → AI Match → No-match Fallback → QR Verify
- [ ] Deploy backend → Railway or Render (free tier)
- [ ] Deploy frontend → Vercel
- [ ] Record demo video as backup for judges

---

## 🗂️ Final Folder Structure

```
campus-market/              ← THIS REPO (we build here)
├── campus_bazar/           ← Django project config
│   ├── settings.py         ← UPDATE: add DRF, JWT, CORS, Gemini key
│   └── urls.py             ← UPDATE: include all new app URL files
├── marketplace/            ← EXISTING (clean up + convert to DRF)
│   ├── models.py           ← FIX: remove duplicate import block
│   └── views.py            ← FIX: broken dashboard, duplicate defs
├── resources/              ← NEW APP
│   ├── models.py           ← Resource, ResourceCategory, GreenBadge
│   ├── serializers.py
│   ├── views.py            ← DRF ViewSets
│   ├── signals.py          ← auto QR gen + green points on save
│   └── urls.py
├── ai/                     ← NEW APP
│   ├── gemini.py           ← all Gemini API functions
│   ├── views.py            ← analyze-image, match-request, reuse-advisor
│   └── urls.py
├── requests_app/           ← NEW APP (named _app to avoid Python requests conflict)
│   ├── models.py           ← ResourceRequest, ResourceMatch
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── impact/                 ← NEW APP
│   ├── models.py           ← SustainabilityImpact
│   ├── views.py
│   └── urls.py
├── media/                  ← uploaded images + generated QR codes
├── manage.py
├── requirements.txt        ← keep updated after every pip install
└── .env                    ← GEMINI_API_KEY, SECRET_KEY, DATABASE_URL

hackathon-frontend/         ← NEW SEPARATE VITE PROJECT
├── src/
│   ├── api/
│   ├── components/
│   └── pages/
├── index.html
└── vite.config.js
```

---

## ⚡ Immediate First Steps

```
1. Fix marketplace/models.py  → remove duplicate import block
2. Fix marketplace/views.py   → fix dashboard, remove duplicate functions
3. pip install all packages
4. Update campus_bazar/settings.py (INSTALLED_APPS, CORS, JWT)
5. python manage.py makemigrations && python manage.py migrate
6. python manage.py runserver  → must start with zero errors
7. Create resources/ app → build DRF models + serializers + views
```

---

## ❌ Explicitly NOT Building

| Feature | Reason |
|---|---|
| Blockchain verification | QR codes do the job; blockchain is complexity theater |
| Real-time WebSocket chat | Too complex for hackathon timeline |
| Payment system | Free/lend platform — no payments |
| Email domain verification | Time cost not worth it for hackathon |
| Gemini chatbot / welcome messages | Gimmick — judges see through it |
| CO₂ via Gemini | Hardcode formula, faster and more reliable |
| Mobile app | Out of scope |
| Notification system | Out of scope |

---

## 🏆 Judge-Ready Answer

**Q: "Why Gemini? Couldn't a database filter do this?"**

> *"A SQL filter answers 'what resources exist?' — Gemini answers 'given what this student is actually trying to accomplish, which resources are genuinely suitable, and why?' The student typed their project goal in plain English, not a product name. Gemini bridged natural human language to structured campus inventory. No SQL query can do that."*
