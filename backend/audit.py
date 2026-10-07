"""Append-only log of one shop-assistant turn.

output/audit_trail.json is a JSON list. New turns are added at the end.
A run never replaces the list with a shorter one.
"""

from __future__ import annotations

import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "output" / "audit_trail.json"
_LOCK_PATH = AUDIT_PATH.with_name(".audit_trail.lock")
_MAX = 220
_SECRET = ("password", "hash", "api_key", "apikey", "token", "secret", "authorization")


def append_event(*, tool: str, args: str, result: str, stop_reason: str, path: Path | None = None) -> None:
    """Add one row. If the file is not a JSON list, leave it untouched."""
    target = path or AUDIT_PATH
    event = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": tool,
        "args": _clip(args),
        "result": _clip(result),
        "stop_reason": stop_reason,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.with_name(".audit_trail.lock") if path else _LOCK_PATH
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            events = _load(target)
            if events is None:
                return
            events.append(event)
            temporary = target.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, target)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def short_args(args: Any) -> str:
    parsed = args
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
        except json.JSONDecodeError:
            return _clip(args)
    if isinstance(parsed, dict):
        parts: list[str] = []
        for key, value in parsed.items():
            shown = "[redacted]" if _secret(str(key)) else _clip(value, 80)
            parts.append(f"{key}={shown}")
        return _clip(", ".join(parts))
    if parsed is None:
        return ""
    return _clip(parsed)


def short_result(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            return _clip(content)
    data = content.model_dump() if hasattr(content, "model_dump") else content
    if not isinstance(data, dict):
        return _clip(data)
    if any(_secret(str(key)) for key in data):
        data = {key: ("[redacted]" if _secret(str(key)) else value) for key, value in data.items()}
    products = data.get("products")
    names = _names(products)
    if "returned" in data and isinstance(products, list):
        listed = f"; {', '.join(names)}" if names else ""
        return _clip(f"{data.get('returned')} matches for {data.get('query')}{listed}")
    if "compared" in data and isinstance(products, list):
        price = _money(data.get("price"))
        listed = ", ".join(names) if names else "none"
        return _clip(f"lowest {price} among {data.get('compared')}: {listed}")
    if "sizes" in data and "found" in data:
        if not data.get("found"):
            return _clip(str(data.get("note") or "not found"))
        bits = []
        for size in data.get("sizes") or []:
            if not isinstance(size, dict):
                continue
            label = f"{size.get('size')} {size.get('quantity')}"
            if size.get("sold_out"):
                label += " sold out"
            bits.append(label)
        detail = ", ".join(bits) if bits else str(data.get("note") or "")
        return _clip(f"{data.get('name') or data.get('product_id')}: {detail}")
    if "price" in data and "found" in data and "description" in data:
        if not data.get("found"):
            return _clip(str(data.get("note") or "not found"))
        colors = data.get("colors") or []
        color_bit = ", ".join(colors) if colors else "colors not listed"
        return _clip(f"{data.get('name')} {_money(data.get('price'))}; {color_bit}")
    if "logged_in" in data:
        who = data.get("first_name") or "guest"
        page = data.get("page_product_name") or "no product page"
        return _clip(f"logged_in={data.get('logged_in')} name={who} page={page}")
    return _clip(json.dumps(data, default=str))


def _load(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
        return None
    return parsed


def _names(products: Any) -> list[str]:
    if not isinstance(products, list):
        return []
    names: list[str] = []
    for item in products[:3]:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    extra = len(products) - len(names)
    if extra > 0 and names:
        names.append(f"+{extra} more")
    return names


def _money(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"${value:g}"
    if value is None:
        return "no price"
    return str(value)


def _secret(key: str) -> bool:
    lowered = key.lower().replace("-", "_")
    return any(part in lowered for part in _SECRET)


def _clip(value: Any, limit: int = _MAX) -> str:
    text = value if isinstance(value, str) else str(value)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
