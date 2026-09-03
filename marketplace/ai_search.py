"""
marketplace/ai_search.py — Uni-Store AI Search Business Logic
──────────────────────────────────────────────────────────────
This module owns the entire AI-search pipeline:

  1.  SYSTEM_PROMPT           → static system instruction encoding all 6 rules
  2.  search_products()       → queries the Django ORM (SQLite / Postgres)
  3.  _call_gemini()          → wraps multi-turn google.genai calls
  4.  run_ai_search()         → orchestrates everything; called by views.py

The view only has to do:
    items, narration, clarification = run_ai_search(user_query, session)
"""

import json
import os
import re
import logging
from django.conf import settings
from django.db.models import Q

from .models import Category, Item

logger = logging.getLogger(__name__)

# ─── Gemini setup ─────────────────────────────────────────────────────────────

def _get_api_key():
    return os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", "")

_MODEL_NAME = getattr(settings, "GEMINI_MODEL_NAME", "gemini-2.5-flash")


# ─── System prompt (the business rules you specified) ─────────────────────────

SYSTEM_PROMPT = """
You are a product search assistant for Uni-Store, a campus circular-economy
marketplace where students share, lend, donate, or rent items to each other.

## Your job
Understand what the user is looking for and extract structured search parameters
so the backend can query the database. You NEVER invent product details.

## Listing types on this platform
- lend   -> free borrow, must return
- donate -> free, keep it
- share  -> common use
- rent   -> paid per day, must return

## Behavior rules

1. INTENT EXTRACTION
   From the user message extract:
     - keywords      (str)       the main search term(s)
     - category      (str|null)  category name if mentioned
     - min_price     (float|null) minimum rent price per day if mentioned
     - max_price     (float|null) maximum rent price per day if mentioned
     - listing_type  ("lend"|"donate"|"share"|"rent"|null) if mentioned
     - attributes    (object)    any other attributes like condition, colour, etc.
   If the query is vague (e.g. "show me something nice") set needs_clarification=true
   and write ONE short clarifying question in clarification_question.

2. NEVER answer with product names, prices, or availability from memory.
   Always rely on the database results provided to you in the follow-up turn.

3. NO RESULTS HANDLING
   If told that the database returned 0 results, state that the requested product is
   currently not available on campus, and suggest a broader search:
   - drop a filter
   - propose a synonym keyword
   - suggest requesting from fellow students

4. RESULT NARRATION
   When database results ARE provided, write a SHORT, friendly summary paragraph
   (2-4 sentences) that:
     - clearly states whether the requested product is available
     - highlights the best matching items briefly with their listing type (free lend vs rent vs donate)
     - does NOT expose IDs, SQL, or schema
   Then set present_results=true.

5. GUARDRAILS
   - Never fabricate a product, price, discount, or stock status.
   - Never expose SQL, schema, or internal IDs.
   - Stay on product search; if asked about returns/support/account, redirect
     politely and set off_topic=true.

## Output format (always valid JSON, nothing else)
{
  "needs_clarification": false,
  "clarification_question": null,
  "off_topic": false,
  "keywords": "<extracted keywords>",
  "category": null,
  "listing_type": null,
  "min_price": null,
  "max_price": null,
  "attributes": {},
  "present_results": false,
  "narration": null
}
""".strip()


# ─── Database search ──────────────────────────────────────────────────────────

def search_products(query="", category=None, listing_type=None,
                    min_price=None, max_price=None, limit=12):
    """
    Query the Django ORM for Items matching the given filters.
    Returns a list of plain dicts (safe to serialise / pass to templates / JSON API).
    """
    qs = Item.objects.select_related("category", "seller").all()

    if query:
        clean_query = query.strip()
        # Split into key terms to allow flexible partial matches
        terms = [t for t in re.split(r"\s+", clean_query) if len(t) > 2]
        if terms:
            q_obj = Q()
            for term in terms:
                q_obj |= Q(title__icontains=term) | Q(description__icontains=term)
            qs = qs.filter(q_obj)
        else:
            qs = qs.filter(
                Q(title__icontains=clean_query) | Q(description__icontains=clean_query)
            )

    if category:
        try:
            cat_id = int(category)
            qs = qs.filter(category__id=cat_id)
        except (ValueError, TypeError):
            qs = qs.filter(category__name__icontains=str(category).strip())

    if listing_type and listing_type.lower() in ("lend", "donate", "share", "rent"):
        qs = qs.filter(listing_type=listing_type.lower())

    if min_price is not None:
        try:
            qs = qs.filter(rent_price_per_day__gte=float(min_price))
        except (ValueError, TypeError):
            pass

    if max_price is not None:
        try:
            qs = qs.filter(rent_price_per_day__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    qs = qs.order_by("-posted_on")[:limit]

    results = []
    for item in qs:
        badge_color, badge_label = item.listing_type_badge
        image_url = None
        if item.image:
            try:
                image_url = item.image.url
            except Exception:
                image_url = None

        results.append({
            "id":           item.id,
            "title":        item.title,
            "description":  item.description[:160] + ("..." if len(item.description) > 160 else ""),
            "listing_type": item.listing_type,
            "badge_label":  badge_label,
            "badge_color":  badge_color,
            "rent_price":   float(item.rent_price_per_day) if item.rent_price_per_day else 0.0,
            "rent_price_per_day": float(item.rent_price_per_day) if item.rent_price_per_day else 0.0,
            "condition":    item.condition,
            "category":     item.category.name if item.category else "Uncategorised",
            "seller":       item.seller.username,
            "posted_on":    item.posted_on.strftime("%d %b %Y"),
            "image_url":    image_url,
        })
    return results


# ─── Heuristic Fallback (when API key is missing or offline) ──────────────────

def _heuristic_extract_intent(text):
    """
    Intelligent regex/keyword intent extractor used when Gemini API key is absent.
    """
    lowered = text.lower()

    # Off-topic checks
    off_topic_words = ["refund", "customer service", "complaint", "password reset", "hacked", "my account"]
    if any(w in lowered for w in off_topic_words):
        return {
            "needs_clarification": False,
            "clarification_question": None,
            "off_topic": True,
            "keywords": text,
            "category": None,
            "listing_type": None,
            "min_price": None,
            "max_price": None,
            "attributes": {},
            "present_results": False,
            "narration": None,
        }

    # Clarification checks for overly generic queries
    if lowered.strip() in ["something", "stuff", "anything", "show me", "items", "help", "hi", "hello"]:
        return {
            "needs_clarification": True,
            "clarification_question": "What kind of campus resource are you looking for? (e.g. textbooks, lab equipment, electronics)",
            "off_topic": False,
            "keywords": "",
            "category": None,
            "listing_type": None,
            "min_price": None,
            "max_price": None,
            "attributes": {},
            "present_results": False,
            "narration": None,
        }

    # Extract listing type
    listing_type = None
    if "lend" in lowered or "borrow" in lowered:
        listing_type = "lend"
    elif "donate" in lowered or "free" in lowered or "giveaway" in lowered:
        listing_type = "donate"
    elif "rent" in lowered or "hire" in lowered:
        listing_type = "rent"
    elif "share" in lowered or "common" in lowered:
        listing_type = "share"

    # Extract price constraints like "under 50", "below 20", "max 100", "less than 30"
    max_price = None
    min_price = None
    max_match = re.search(r"(?:under|below|less than|max(?:imum)?|up to|within)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)", lowered)
    if max_match:
        try:
            max_price = float(max_match.group(1))
        except ValueError:
            pass

    min_match = re.search(r"(?:above|more than|min(?:imum)?|at least)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)", lowered)
    if min_match:
        try:
            min_price = float(min_match.group(1))
        except ValueError:
            pass

    # Extract clean search keywords (strip conversational noise words)
    stop_phrases = [
        r"\bi need\b", r"\bi want\b", r"\blooking for\b", r"\bis there\b", r"\bany\b",
        r"\bcan i get\b", r"\bshow me\b", r"\bdo you have\b", r"\bavailable\b",
        r"\bfor rent\b", r"\bto rent\b", r"\bto borrow\b", r"\bfor free\b",
        r"\bunder\s*(?:₹|rs\.?)?\s*\d+\b", r"\bbelow\s*(?:₹|rs\.?)?\s*\d+\b",
    ]
    cleaned_keywords = lowered
    for p in stop_phrases:
        cleaned_keywords = re.sub(p, "", cleaned_keywords, flags=re.IGNORECASE)
    cleaned_keywords = re.sub(r"[?!.,]", "", cleaned_keywords).strip()

    if not cleaned_keywords:
        cleaned_keywords = text

    return {
        "needs_clarification": False,
        "clarification_question": None,
        "off_topic": False,
        "keywords": cleaned_keywords,
        "category": None,
        "listing_type": listing_type,
        "min_price": min_price,
        "max_price": max_price,
        "attributes": {},
        "present_results": False,
        "narration": None,
    }


def _heuristic_narrate(user_query, items):
    """
    Intelligent narration generator when Gemini API key is not present.
    Explains product availability, listing types, and options.
    """
    if not items:
        return (
            f"❌ **Currently Unavailable**: No items matching \"{user_query}\" are currently listed by campus students. "
            "You can try broader keywords, check related categories, or post a request so a peer can share theirs!"
        )

    count = len(items)
    free_items = [i for i in items if i.get("listing_type") in ("lend", "donate", "share")]
    rent_items = [i for i in items if i.get("listing_type") == "rent"]

    first_item = items[0]
    badge_label = first_item.get("badge_label") or first_item.get("listing_type", "").capitalize()
    condition = first_item.get("condition", "Good")
    seller = first_item.get("seller", "a student")

    narration_parts = [
        f"✅ **Available!** Found {count} resource{'s' if count > 1 else ''} matching \"{user_query}\"."
    ]

    if free_items and rent_items:
        free_title = free_items[0].get("title", "Item")
        free_badge = free_items[0].get("badge_label") or "Free"
        rent_val = float(rent_items[0].get("rent_price") or rent_items[0].get("rent_price_per_day") or 0)
        narration_parts.append(
            f"You have both free options (like {free_title} for {free_badge}) "
            f"and rental options starting at ₹{rent_val:.0f}/day."
        )
    elif rent_items:
        rent_val = float(rent_items[0].get("rent_price") or rent_items[0].get("rent_price_per_day") or 0)
        narration_parts.append(
            f"Available for rent from ₹{rent_val:.0f}/day "
            f"(e.g., {first_item.get('title')} in {condition} condition)."
        )
    else:
        narration_parts.append(
            f"Top match: {first_item.get('title')} ({badge_label}) in {condition} condition from @{seller}."
        )

    narration_parts.append("You can chat directly with the owner to arrange pickup on campus.")
    return " ".join(narration_parts)


# ─── Gemini conversation helpers ──────────────────────────────────────────────

def _call_gemini(history):
    """
    Send a multi-turn conversation to Gemini using the google.genai SDK
    and return the raw text response.

    history is a list of {"role": "user"|"model", "parts": ["..."]} dicts.
    Falls back to intelligent local heuristics if no API key is configured or on network error.
    """
    api_key = _get_api_key()
    if not api_key:
        return _fallback_turn_response(history)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        contents = [
            types.Content(
                role=turn["role"],
                parts=[types.Part(text=turn["parts"][0])],
            )
            for turn in history
        ]

        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )
        return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini call failed or unavailable (%s). Using heuristic fallback.", exc)
        return _fallback_turn_response(history)


def _fallback_turn_response(history):
    """Generates JSON response when Gemini API is unavailable."""
    last_user_msg = ""
    for turn in reversed(history):
        if turn.get("role") == "user":
            last_user_msg = turn["parts"][0]
            break

    # Check if this is Turn 2 (narration prompt)
    if "The database returned" in last_user_msg:
        m_query = re.search(r'for the user\'s query "([^"]+)"', last_user_msg)
        query = m_query.group(1) if m_query else "your search"
        m_count = re.search(r"The database returned (\d+) result", last_user_msg)
        count = int(m_count.group(1)) if m_count else 0

        items = []
        try:
            json_part = last_user_msg.split("Results:\n")[1].split("\n\nNow write")[0]
            items = json.loads(json_part)
        except Exception:
            pass

        narration = _heuristic_narrate(query, items)
        return json.dumps({
            "needs_clarification": False,
            "clarification_question": None,
            "off_topic": False,
            "keywords": query,
            "category": None,
            "listing_type": None,
            "min_price": None,
            "max_price": None,
            "attributes": {},
            "present_results": count > 0,
            "narration": narration,
        })

    # Turn 1: Intent extraction
    extracted = _heuristic_extract_intent(last_user_msg)
    return json.dumps(extracted)


def _parse_gemini_json(raw):
    """Strip markdown fences and parse the JSON the model returns."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip()).strip()

    if "{" in cleaned and "}" in cleaned:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        cleaned = cleaned[start:end]

    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, Exception):
        return _heuristic_extract_intent(raw[:160])


# ─── Main entry point called by views.py ──────────────────────────────────────

def run_ai_search(user_query, session):
    """
    Orchestrates the AI search pipeline.

    Args:
        user_query  : The raw text the user typed into the search bar.
        session     : Django request.session dict — used to persist chat history.

    Returns a 3-tuple:
        items                  list[dict]   product dicts (may be empty)
        narration              str|None     AI-written summary paragraph on availability
        clarification_question str|None     question to show when query is vague
    """
    clean_query = (user_query or "").strip()
    if not clean_query:
        return [], None, None

    # ── Restore or initialise conversation history ─────────────────────────
    history = session.get("ai_search_history", [])

    # ── Turn 1: extract intent ─────────────────────────────────────────────
    history.append({"role": "user", "parts": [clean_query]})
    raw_intent = _call_gemini(history)
    intent = _parse_gemini_json(raw_intent)
    history.append({"role": "model", "parts": [raw_intent]})

    # ── Off-topic guard ────────────────────────────────────────────────────
    if intent.get("off_topic"):
        session["ai_search_history"] = history[-10:]
        return (
            [],
            ("That sounds like it's outside my product search scope. "
             "For support, returns, or account issues, please contact the student help desk."),
            None,
        )

    # ── Vague query → ask for clarification before searching ──────────────
    if intent.get("needs_clarification"):
        session["ai_search_history"] = history[-10:]
        return [], None, intent.get("clarification_question", "Could you tell me more about what you need?")

    # ── Search the database ────────────────────────────────────────────────
    search_term = intent.get("keywords") or clean_query
    items = search_products(
        query=search_term,
        category=intent.get("category"),
        listing_type=intent.get("listing_type"),
        min_price=intent.get("min_price"),
        max_price=intent.get("max_price"),
        limit=12,
    )

    # ── 0 results: broaden and retry once (drop extra filters) ────────────
    if not items and (
        intent.get("category") or intent.get("listing_type")
        or intent.get("min_price") or intent.get("max_price")
    ):
        items = search_products(
            query=search_term,
            limit=12,
        )

    # ── Turn 2: ask Gemini to narrate the results ──────────────────────────
    items_summary = json.dumps(
        [
            {
                "title":              i["title"],
                "listing_type":       i["listing_type"],
                "badge_label":        i["badge_label"],
                "category":           i["category"],
                "condition":          i["condition"],
                "rent_price_per_day": i["rent_price"],
                "seller":             i["seller"],
            }
            for i in items
        ],
        indent=2,
    ) if items else "[]"

    narrate_prompt = (
        f"The database returned {len(items)} result(s) for the user's query "
        f'"{clean_query}".\n\nResults:\n{items_summary}\n\n'
        "Now write a short, friendly narration paragraph (2-4 sentences) and set "
        "present_results=true in your JSON. Clearly state whether the item is available or not, "
        "mention key details (e.g. free lend vs rent price per day). If 0 results, set present_results=false "
        "and suggest a broader search in the narration field."
    )

    history.append({"role": "user", "parts": [narrate_prompt]})
    raw_narration = _call_gemini(history)
    narration_intent = _parse_gemini_json(raw_narration)
    history.append({"role": "model", "parts": [raw_narration]})

    # Persist history (cap at 20 messages to keep session small)
    session["ai_search_history"] = history[-20:]

    narration = narration_intent.get("narration") or _heuristic_narrate(clean_query, items)

    return items, narration, None
