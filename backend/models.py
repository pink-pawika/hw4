"""Structured types for the Campus Customs shop assistant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class SizeStock(BaseModel):
    """One size row from inventory. quantity 0 and sold_out true mean that size is gone."""

    size: str
    quantity: int
    sold_out: bool


class ProductMatch(BaseModel):
    """A search hit. Enough to pick a product_id. Not a price or a stock count."""

    product_id: str
    name: str
    garment_type: str


class ProductInfo(BaseModel):
    """Catalogue facts for one product. description and price are the only ones to quote."""

    found: bool
    product_id: str
    name: str = ""
    garment_type: str = ""
    description: str = ""
    colors: list[str] = Field(default_factory=list)
    price: float | None = None
    image_url: str = ""
    note: str = ""


class StockResult(BaseModel):
    """Inventory for one product. Read quantity and sold_out. Do not fill in a missing size."""

    found: bool
    product_id: str
    name: str = ""
    asked_size: str | None = None
    sizes: list[SizeStock] = Field(default_factory=list)
    note: str = ""


class ProductCard(BaseModel):
    """One catalogue product the page can show. Price comes from ProductInfo."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str] = Field(default_factory=list)
    price: float
    image_url: str
    sizes: list[SizeStock] = Field(default_factory=list)
    total_stock: int | None = None


class SearchResult(BaseModel):
    """What search_products returns. Matches name the product. They do not include price or stock."""

    query: str
    returned: int
    note: str = ""
    products: list[ProductMatch] = Field(default_factory=list)


class PricePick(BaseModel):
    """One piece at the lowest catalogue price. price is that shared number, not a discount."""

    product_id: str
    name: str
    garment_type: str
    price: float


class LowestPrice(BaseModel):
    """The cheapest match for a query. Quote price. Every product in the list costs that much."""

    query: str
    compared: int
    price: float | None = None
    products: list[PricePick] = Field(default_factory=list)
    note: str = ""


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


@dataclass
class ShopperDeps:
    """Injected on every run. The model sees name and email only through the turn note and current_customer.

    user_id is for saving chat_messages. It is not a customer field the model is given.
    page_product_id is the product page open in the browser, or None.
    """

    user_id: int | None = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    page_product_id: str | None = None


class CustomerView(BaseModel):
    """Who is chatting, and which product page is open. No password."""

    logged_in: bool
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    page_product_id: str | None = None
    page_product_name: str = ""


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = Field(default_factory=list)
    page_product_id: str | None = None


class HistoryTurn(BaseModel):
    """One saved turn the widget can show again."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatOutput(BaseModel):
    """What the model fills in. product_ids are catalogue ids from a tool on this turn.

    The page does not render this type. run_chat turns the ids into ChatReply cards.
    """

    message: str
    product_ids: list[str] = Field(default_factory=list)


class ChatReply(BaseModel):
    """What /api/chat returns. products is the list the products page draws.

    Each card's price, description, and image come from the catalogue row for a
    product_id that search_products or get_product_info returned on this turn.
    """

    message: str
    products: list[ProductCard] = Field(default_factory=list)
