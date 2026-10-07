"""Campus Customs shop assistant.

Loads prompts/prompt.md. Model calls use Portkey and gpt-5.6-lunar.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from portkey_ai import PORTKEY_GATEWAY_URL, createHeaders
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from audit import append_event, short_args, short_result
from models import ChatOutput, ChatReply, ChatTurn, CustomerView, LowestPrice, ProductInfo, SearchResult, ShopperDeps
from tools import catalogue_cards, get_product_info, get_stock, lowest_price, products_in_color, search_products

BACKEND = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND / "prompts" / "prompt.md"
ROOT = BACKEND.parent

load_dotenv(ROOT / ".env")
if not os.getenv("PORTKEY_API_KEY", "").strip():
    load_dotenv(ROOT.parent / ".env")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.6-lunar").strip() or "gpt-5.6-lunar"
MAX_MODEL_REQUESTS = 8

_agent: Agent[ShopperDeps, ChatOutput] | None = None


def shopper_note(deps: ShopperDeps) -> str:
    """Turn note built from deps. Name and email come from the users row. The open product comes from the page."""
    if deps.email.strip():
        who = (
            "The shopper is logged in. "
            f"First name: {deps.first_name}. Last name: {deps.last_name}. Email: {deps.email}. "
            "These are the only customer fields you have. There is no password."
        )
    else:
        who = "The shopper is a guest. You do not have a name or an email for them. Do not guess either."
    product_id = (deps.page_product_id or "").strip()
    if not product_id:
        page = "They are not on a product page. If they say this or it without naming a piece, ask which one."
        return f"{who}\n{page}"
    info = get_product_info(product_id)
    if not info.found:
        page = f"They sent product id {product_id}, which is not in the catalogue."
        return f"{who}\n{page}"
    colors = ", ".join(info.colors) if info.colors else "not listed"
    page = (
        f"They are looking at {info.name}. product_id: {info.product_id}. "
        f"Catalogue colors: {colors}. "
        "When they say this, that, or it, they mean this product. "
        "Use this product_id with get_product_info and get_stock. Do not pick a different product."
    )
    return f"{who}\n{page}"


def build_agent() -> Agent[ShopperDeps, ChatOutput]:
    api_key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=PORTKEY_GATEWAY_URL,
        default_headers=createHeaders(provider="openai"),
    )
    model = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    agent = Agent(
        model,
        deps_type=ShopperDeps,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=[search_products, get_product_info, get_stock, lowest_price, products_in_color],
        output_type=ChatOutput,
    )

    @agent.instructions
    def add_shopper_context(ctx: RunContext[ShopperDeps]) -> str:
        return shopper_note(ctx.deps)

    @agent.tool
    def current_customer(ctx: RunContext[ShopperDeps]) -> CustomerView:
        """Return the logged-in shopper's first name, last name, and email, plus the open product page.

        Guests come back with logged_in false and empty name and email. Do not invent those.
        This does not return a password or another shopper's account.
        """
        deps = ctx.deps
        product_id = (deps.page_product_id or "").strip()
        name = ""
        if product_id:
            info = get_product_info(product_id)
            if info.found:
                product_id = info.product_id
                name = info.name
        return CustomerView(
            logged_in=bool(deps.email.strip()),
            first_name=deps.first_name,
            last_name=deps.last_name,
            email=deps.email,
            page_product_id=product_id or None,
            page_product_name=name,
        )

    return agent


def get_agent() -> Agent[ShopperDeps, ChatOutput]:
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def _history(turns: list[ChatTurn]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for turn in turns[-12:]:
        text = turn.content.strip()
        if not text:
            continue
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=text)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=text)]))
    return messages


def _ids_from(content: object) -> list[str]:
    if isinstance(content, SearchResult):
        return [item.product_id for item in content.products]
    if isinstance(content, LowestPrice):
        return [item.product_id for item in content.products]
    if isinstance(content, ProductInfo):
        return [content.product_id] if content.found else []
    if isinstance(content, dict):
        products = content.get("products")
        if isinstance(products, list) and "query" in content:
            return [
                str(item["product_id"])
                for item in products
                if isinstance(item, dict) and item.get("product_id")
            ]
        if content.get("found") is True and content.get("product_id"):
            return [str(content["product_id"])]
        if "compared" in content and isinstance(content.get("products"), list):
            return [
                str(item["product_id"])
                for item in content["products"]
                if isinstance(item, dict) and item.get("product_id")
            ]
        return []
    if isinstance(content, list):
        found: list[str] = []
        for item in content:
            found.extend(_ids_from(item))
        return found
    return []


def _tool_ids(messages: list[ModelMessage]) -> tuple[list[str], list[str], list[str]]:
    """Product ids from this turn: search or color, lowest price, then one-product info."""
    search_ids: list[str] = []
    lowest_ids: list[str] = []
    info_ids: list[str] = []
    for message in messages:
        for part in getattr(message, "parts", []):
            if not isinstance(part, ToolReturnPart):
                continue
            if part.tool_name in {"search_products", "products_in_color"}:
                search_ids.extend(_ids_from(part.content))
            elif part.tool_name == "lowest_price":
                lowest_ids.extend(_ids_from(part.content))
            elif part.tool_name == "get_product_info":
                info_ids.extend(_ids_from(part.content))
    return _unique(search_ids), _unique(lowest_ids), _unique(info_ids)


def _unique(product_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for product_id in product_ids:
        if product_id in seen:
            continue
        seen.add(product_id)
        ordered.append(product_id)
    return ordered


async def _audit_tools(_ctx: RunContext[ShopperDeps], events) -> None:
    """Write one trail row when a model tool call returns. Does not log the final answer tool."""
    pending: dict[str, tuple[str, str]] = {}
    async for event in events:
        if isinstance(event, FunctionToolCallEvent):
            pending[event.tool_call_id] = (event.part.tool_name, short_args(event.part.args))
        elif isinstance(event, FunctionToolResultEvent):
            fallback = getattr(event.part, "tool_name", "")
            name, args = pending.pop(event.tool_call_id, (fallback, ""))
            if isinstance(event.part, RetryPromptPart):
                result_text = "tool arguments were rejected"
            else:
                result_text = short_result(getattr(event.part, "content", ""))
            append_event(tool=name, args=args, result=result_text, stop_reason="")


def _finish_reason(result) -> str:
    for message in reversed(result.new_messages()):
        reason = getattr(message, "finish_reason", None)
        if reason:
            return str(reason)
    return "stop"


async def run_chat(message: str, history: list[ChatTurn], deps: ShopperDeps) -> ChatReply:
    try:
        result = await get_agent().run(
            message.strip(),
            deps=deps,
            message_history=_history(history),
            usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS),
            event_stream_handler=_audit_tools,
        )
    except UsageLimitExceeded:
        append_event(tool="", args="", result="model request cap reached", stop_reason="request_limit")
        raise
    except Exception as exc:
        append_event(tool="", args="", result=type(exc).__name__, stop_reason="error")
        raise
    reply = result.output
    search_ids, lowest_ids, info_ids = _tool_ids(result.all_messages())
    allowed = set(search_ids + lowest_ids + info_ids)
    named = _unique([product_id.strip() for product_id in reply.product_ids if product_id.strip() in allowed])
    if named:
        chosen_ids = named
    elif lowest_ids:
        chosen_ids = lowest_ids
    elif info_ids:
        chosen_ids = info_ids
    else:
        chosen_ids = search_ids
    by_id = {card.product_id: card for card in catalogue_cards(chosen_ids)}
    chosen = [by_id[product_id] for product_id in chosen_ids if product_id in by_id]
    append_event(
        tool="",
        args="",
        result=f"answered with {len(chosen)} cards",
        stop_reason=_finish_reason(result),
    )
    return ChatReply(message=reply.message, products=chosen)
