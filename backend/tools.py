"""Tools the shop assistant can call. They read the local catalogue and inventory only."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from models import LowestPrice, PricePick, ProductCard, ProductInfo, ProductMatch, SearchResult, SizeStock, StockResult

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
SIZE_ALIASES = {
    "xs": "XS",
    "xsmall": "XS",
    "extrasmall": "XS",
    "s": "S",
    "small": "S",
    "m": "M",
    "medium": "M",
    "med": "M",
    "l": "L",
    "large": "L",
    "xl": "XL",
    "xlarge": "XL",
    "extralarge": "XL",
    "xxl": "XXL",
    "2xl": "XXL",
    "xxlarge": "XXL",
}
MAX_RESULTS = 30
SKIP_WORDS = {
    "a",
    "an",
    "the",
    "me",
    "my",
    "you",
    "your",
    "do",
    "does",
    "have",
    "has",
    "any",
    "some",
    "in",
    "of",
    "and",
    "or",
    "with",
    "for",
    "to",
    "what",
    "which",
    "show",
    "looking",
    "look",
    "want",
    "need",
}


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _colors(raw: str) -> list[str]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [color for color in parsed if isinstance(color, str) and color.strip()]


def _normalize_size(size: str | None) -> str | None:
    if size is None or not size.strip():
        return None
    key = "".join(ch for ch in size.lower() if ch.isalnum())
    if key in SIZE_ALIASES:
        return SIZE_ALIASES[key]
    upper = size.strip().upper()
    if upper in SIZE_ORDER:
        return upper
    return None


def _sizes(connection: sqlite3.Connection, product_id: str) -> list[SizeStock]:
    rows = connection.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?",
        (product_id,),
    ).fetchall()
    by_size = {row["size"]: row["quantity"] for row in rows}
    ordered = SIZE_ORDER + [size for size in by_size if size not in SIZE_ORDER]
    return [
        SizeStock(size=size, quantity=by_size[size], sold_out=by_size[size] == 0)
        for size in ordered
        if size in by_size
    ]


def _terms(query: str) -> list[str]:
    words = []
    for word in query.lower().replace("-", " ").split():
        if word in SKIP_WORDS or len(word) < 2:
            continue
        if word in {"hoodie", "hoodies"}:
            words.append("hoodie")
            continue
        if word in {"pullover", "pullovers"}:
            words.append("pullover")
            continue
        if word in {"crewneck", "crewnecks"}:
            words.append("crewneck")
            continue
        if word in {"tshirt", "tshirts", "tee", "tees", "shirt", "shirts"} or word.startswith("tshirt"):
            words.append("tshirt")
            continue
        words.append(word)
    lowered = query.lower()
    if "t shirt" in lowered or "tshirt" in lowered.replace("-", ""):
        words.append("tshirt")
    return list(dict.fromkeys(words))


def _haystack(row: sqlite3.Row) -> str:
    garment = row["garment_type"].lower()
    aliases = [garment]
    if "hoodie" in garment:
        aliases.append("hoodie pullover")
    if "t-shirt" in garment:
        aliases.append("tshirt t-shirt tee")
    return " ".join(
        [
            row["product_id"],
            row["name"],
            row["description"],
            row["colors"],
            row["search_tags"],
            " ".join(aliases),
        ]
    ).lower()


def _ranked_rows(query: str) -> list[sqlite3.Row]:
    terms = _terms(query)
    if not terms:
        return []
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT product_id, name, garment_type, description, colors, search_tags, image_file_path, price
            FROM catalogue
            """
        ).fetchall()
    scored: list[tuple[int, str, sqlite3.Row]] = []
    for row in rows:
        haystack = _haystack(row)
        score = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", haystack))
        if score:
            scored.append((score, row["name"], row))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [row for _, _, row in scored]


def _color_phrase(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").replace("grey", "gray").split())


def _listed_colors(raw: str) -> list[str]:
    return [_color_phrase(color) for color in _colors(raw)]


def _color_hit(asked: str, listed: list[str]) -> bool:
    phrase = _color_phrase(asked)
    if not phrase:
        return False
    for color in listed:
        if not color:
            continue
        if phrase == color or phrase in color.split():
            return True
        if f" {phrase} " in f" {color} ":
            return True
    return False


def search_products(query: str) -> SearchResult:
    """Find Campus Customs products by garment, school, sport, color, or name.

    Hoodie and pullover hoodie match each other. T-shirt matches regardless of capitalization.
    This does not return a price or a quantity. Call get_product_info and get_stock for those.

    Args:
        query: What the shopper asked for, in plain language.
    """
    rows = _ranked_rows(query)
    if not _terms(query):
        return SearchResult(query=query, returned=0, note="Ask for a garment, school, sport, or color.")
    products = [
        ProductMatch(product_id=row["product_id"], name=row["name"], garment_type=row["garment_type"])
        for row in rows[:MAX_RESULTS]
    ]
    note = "" if products else "Nothing in the catalogue matched."
    if products:
        note = "Matches only. Call get_product_info for description and price, and get_stock for quantities."
        if len(rows) > len(products):
            note = f"Closest {len(products)} matches. " + note
    return SearchResult(query=query, returned=len(products), note=note, products=products)


def lowest_price(query: str) -> LowestPrice:
    """Return the lowest catalogue price for products that match the query.

    Call this for cheapest, lowest, or least expensive. Quote price from this result.
    Every product in the list costs that same price. This is not a sale or a discount.

    Args:
        query: The kind of item, such as hoodie or crewneck.
    """
    if not _terms(query):
        return LowestPrice(query=query, compared=0, note="Ask for a garment, school, sport, or name.")
    rows = _ranked_rows(query)
    if not rows:
        return LowestPrice(query=query, compared=0, note="Nothing in the catalogue matched.")
    cheapest = min(row["price"] for row in rows)
    picks = [
        PricePick(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=row["garment_type"],
            price=row["price"],
        )
        for row in rows
        if row["price"] == cheapest
    ]
    picks.sort(key=lambda item: item.name)
    note = f"Lowest catalogue price is ${cheapest:g} across {len(rows)} matches."
    if len(picks) > 1:
        note += f" {len(picks)} pieces share that price."
    return LowestPrice(query=query, compared=len(rows), price=cheapest, products=picks, note=note)


def products_in_color(color: str, garment: str | None = None) -> SearchResult:
    """Find products whose catalogue color list includes this color.

    Use this when the shopper asks for a color. Do not match a color from the description or the photo.
    An empty color list does not match. If nothing comes back, say the shop does not list that color.
    This does not return a price or a quantity.

    Args:
        color: The color they asked for, such as navy or pink.
        garment: Optional garment, such as hoodie or t-shirt. Leave empty to search every garment.
    """
    phrase = _color_phrase(color)
    if not phrase:
        return SearchResult(query=color, returned=0, note="Name a color.")
    garment_terms = _terms(garment or "")
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT product_id, name, garment_type, description, colors, search_tags, image_file_path, price
            FROM catalogue
            ORDER BY name
            """
        ).fetchall()
    matched: list[ProductMatch] = []
    for row in rows:
        if not _color_hit(phrase, _listed_colors(row["colors"])):
            continue
        if garment_terms:
            garment_text = row["garment_type"].lower()
            if "hoodie" in garment_text or "hooded" in garment_text:
                garment_text += " hoodie pullover"
            if "t-shirt" in garment_text:
                garment_text += " tshirt t-shirt tee"
            if not all(re.search(rf"\b{re.escape(term)}\b", garment_text) for term in garment_terms):
                continue
        matched.append(
            ProductMatch(product_id=row["product_id"], name=row["name"], garment_type=row["garment_type"])
        )
    shown = matched[:MAX_RESULTS]
    label = f"{phrase} {garment}".strip() if garment else phrase
    if not shown:
        note = f"No catalogue color list includes {phrase}."
    else:
        note = "Color matches from the catalogue color list only. No price or quantity."
        if len(matched) > len(shown):
            note = f"Closest {len(shown)} color matches. " + note
    return SearchResult(query=label, returned=len(shown), note=note, products=shown)
    return SearchResult(query=query, returned=len(products), note=note, products=products)


def catalogue_cards(product_ids: list[str]) -> list[ProductCard]:
    """Build page cards from catalogue rows for ids a tool already returned.

    The model does not supply the price or the description. Both are read here.
    """
    ordered: list[str] = []
    seen: set[str] = set()
    for product_id in product_ids:
        cleaned = product_id.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    if not ordered:
        return []
    cards: list[ProductCard] = []
    with _connect() as connection:
        for product_id in ordered:
            row = _catalogue_row(connection, product_id)
            if row is None or row["price"] is None:
                continue
            total = connection.execute(
                "SELECT COALESCE(SUM(quantity), 0) AS total FROM inventory WHERE product_id = ?",
                (row["product_id"],),
            ).fetchone()
            cards.append(
                ProductCard(
                    product_id=row["product_id"],
                    name=row["name"],
                    garment_type=row["garment_type"],
                    description=row["description"],
                    colors=_colors(row["colors"]),
                    price=row["price"],
                    image_url=f"/media/products/{Path(row['image_file_path']).name}",
                    total_stock=int(total["total"]),
                )
            )
    return cards


def _catalogue_row(connection: sqlite3.Connection, product_id: str) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT product_id, name, garment_type, description, colors, image_file_path, price
        FROM catalogue
        WHERE product_id = ?
        """,
        (product_id.strip(),),
    ).fetchone()


def get_product_info(product_id: str) -> ProductInfo:
    """Look up one product's description and price from the catalogue.

    Call this before you say what a piece is or what it costs.
    Use description and price from this result only. Do not invent either.
    An empty colors list stays empty.

    Args:
        product_id: The catalogue id, such as basic-hoodie-big-yale.
    """
    with _connect() as connection:
        row = _catalogue_row(connection, product_id)
    if row is None:
        return ProductInfo(
            found=False,
            product_id=product_id.strip(),
            note="No product with that id is in the catalogue.",
        )
    return ProductInfo(
        found=True,
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=_colors(row["colors"]),
        price=row["price"],
        image_url=f"/media/products/{Path(row['image_file_path']).name}",
    )


def get_stock(product_id: str, size: str | None = None) -> StockResult:
    """Look up how many are left, from the inventory table, by size.

    Call this before you say a quantity or whether a size is in stock.
    Pass size when the shopper names one. sold_out true, or quantity 0, means that size is sold out.
    Say so. Do not invent a count.

    Args:
        product_id: The catalogue id from search_products or get_product_info.
        size: Optional size, such as XS, small, or XL. Leave empty to get every size.
    """
    with _connect() as connection:
        row = _catalogue_row(connection, product_id)
        if row is None:
            return StockResult(
                found=False,
                product_id=product_id.strip(),
                note="No product with that id is in the catalogue.",
            )
        sizes = _sizes(connection, row["product_id"])
    asked = _normalize_size(size)
    if size and size.strip() and asked is None:
        return StockResult(
            found=True,
            product_id=row["product_id"],
            name=row["name"],
            asked_size=size.strip(),
            sizes=sizes,
            note="That size is not one we stock. Sizes are XS, S, M, L, XL, and XXL.",
        )
    shown = sizes
    if asked is not None:
        shown = [item for item in sizes if item.size == asked]
        if not shown:
            return StockResult(
                found=True,
                product_id=row["product_id"],
                name=row["name"],
                asked_size=asked,
                sizes=sizes,
                note=f"{asked} is not on the inventory row for this product.",
            )
        item = shown[0]
        note = f"{asked} is sold out." if item.sold_out else f"{asked} has {item.quantity} in stock."
    else:
        sold = [item.size for item in sizes if item.sold_out]
        note = "Sold out in " + ", ".join(sold) + "." if sold else "Every listed size has stock."
    return StockResult(
        found=True,
        product_id=row["product_id"],
        name=row["name"],
        asked_size=asked,
        sizes=shown if asked else sizes,
        note=note,
    )
