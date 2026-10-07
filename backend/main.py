import json
import re
import secrets
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import run_chat
from models import ChatReply, ChatRequest, ChatTurn, HistoryTurn, ProductCard, ShopperDeps
from passwords import DUMMY_HASH, hash_password, verify_password

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_PATH = DATA / "campus_customs.db"
PRODUCTS_DIR = DATA / "products"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_COOKIE = "campus_session"
sessions: dict[str, int] = {}


class AccountIn(BaseModel):
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    password: str = ""


class LoginIn(BaseModel):
    email: str = ""
    password: str = ""


def public_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "first_name": row["first_name"] or "",
        "last_name": row["last_name"] or "",
        "name": row["name"],
        "email": row["email"],
    }


def account_errors(body: AccountIn) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not body.first_name.strip():
        errors["first_name"] = "First name is required."
    if not body.last_name.strip():
        errors["last_name"] = "Last name is required."
    email = body.email.strip()
    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_RE.fullmatch(email):
        errors["email"] = "Enter an email like name@school.edu."
    if not body.password.strip():
        errors["password"] = "Password is required."
    return errors


def set_session(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    sessions[token] = user_id
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
        path="/",
    )


def current_user_id(request: Request) -> int | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    return sessions.get(token)


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def parse_colors(raw: str) -> list[str]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [color for color in parsed if isinstance(color, str) and color.strip()]


def image_url(image_file_path: str) -> str:
    return f"/media/products/{Path(image_file_path).name}"


def sizes_for(connection: sqlite3.Connection, product_id: str) -> list[dict]:
    rows = connection.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?",
        (product_id,),
    ).fetchall()
    by_size = {row["size"]: row["quantity"] for row in rows}
    ordered = SIZE_ORDER + [size for size in by_size if size not in SIZE_ORDER]
    return [
        {"size": size, "quantity": by_size[size]}
        for size in ordered
        if size in by_size
    ]


def product_summary(row: sqlite3.Row, total_stock: int) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
        "total_stock": total_stock,
    }


@app.get("/api/products")
def list_products() -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                c.product_id,
                c.name,
                c.garment_type,
                c.description,
                c.price,
                c.image_file_path,
                COALESCE(SUM(i.quantity), 0) AS total_stock
            FROM catalogue c
            LEFT JOIN inventory i ON i.product_id = c.product_id
            GROUP BY c.product_id
            ORDER BY c.name
            """
        ).fetchall()
    return [product_summary(row, row["total_stock"]) for row in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT product_id, name, garment_type, description, colors, price, image_file_path
            FROM catalogue
            WHERE product_id = ?
            """,
            (product_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        sizes = sizes_for(connection, product_id)
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": parse_colors(row["colors"]),
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
        "sizes": sizes,
        "total_stock": sum(size["quantity"] for size in sizes),
    }


@app.post("/api/accounts")
def create_account(body: AccountIn) -> JSONResponse:
    errors = account_errors(body)
    if errors:
        return JSONResponse(status_code=400, content={"errors": errors})
    first_name = body.first_name.strip()
    last_name = body.last_name.strip()
    email = body.email.strip().lower()
    with connect() as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()
        if existing is not None:
            return JSONResponse(
                status_code=409,
                content={"errors": {"email": "An account with that email already exists."}},
            )
        connection.execute(
            """
            INSERT INTO users (name, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                f"{first_name} {last_name}",
                email,
                hash_password(body.password),
                first_name,
                last_name,
            ),
        )
        connection.commit()
    return JSONResponse(status_code=201, content={"ok": True})


@app.post("/api/login")
def login(body: LoginIn) -> Response:
    email = body.email.strip().lower()
    password = body.password
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, email, password_hash, first_name, last_name FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()
    # Always run a hash compare so a missing account is not obvious from timing.
    stored = row["password_hash"] if row is not None else DUMMY_HASH
    if row is None or not verify_password(password, stored):
        raise HTTPException(status_code=401, detail="That email and password don't match.")
    response = JSONResponse(public_user(row))
    set_session(response, row["id"])
    return response


@app.get("/api/me")
def me(request: Request) -> dict:
    user_id = current_user_id(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Log in first.")
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, email, first_name, last_name FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Log in first.")
    return public_user(row)


def page_product_id(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    return cleaned or None


def saved_cards(raw: str | None) -> list[ProductCard]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    cards: list[ProductCard] = []
    for item in parsed:
        if not isinstance(item, dict) or not item.get("product_id") or item.get("price") is None:
            continue
        image = item.get("image_url") or ""
        if not image and item.get("image_file_path"):
            image = image_url(str(item["image_file_path"]))
        colors = item.get("colors") if isinstance(item.get("colors"), list) else []
        try:
            cards.append(
                ProductCard(
                    product_id=str(item["product_id"]),
                    name=str(item.get("name") or ""),
                    garment_type=str(item.get("garment_type") or ""),
                    description=str(item.get("description") or ""),
                    colors=[color for color in colors if isinstance(color, str)],
                    price=float(item["price"]),
                    image_url=str(image),
                    total_stock=item["total_stock"] if isinstance(item.get("total_stock"), int) else None,
                )
            )
        except (TypeError, ValueError):
            continue
    return cards


def load_history(user_id: int) -> list[HistoryTurn]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, role, content, products_json
            FROM chat_messages
            WHERE user_id = ? AND role IN ('user', 'assistant')
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()
    return [
        HistoryTurn(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            products=saved_cards(row["products_json"]),
        )
        for row in rows
    ]


def save_exchange(user_id: int, message: str, reply: ChatReply) -> None:
    products_json = json.dumps([card.model_dump() for card in reply.products])
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO chat_messages (user_id, role, content, products_json)
            VALUES (?, 'user', ?, NULL)
            """,
            (user_id, message),
        )
        connection.execute(
            """
            INSERT INTO chat_messages (user_id, role, content, products_json)
            VALUES (?, 'assistant', ?, ?)
            """,
            (user_id, reply.message, products_json),
        )
        connection.commit()


def shopper_deps(request: Request, product_id: str | None) -> ShopperDeps:
    user_id = current_user_id(request)
    if user_id is None:
        return ShopperDeps(page_product_id=product_id)
    with connect() as connection:
        row = connection.execute(
            "SELECT id, first_name, last_name, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return ShopperDeps(page_product_id=product_id)
    return ShopperDeps(
        user_id=row["id"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or "",
        email=row["email"] or "",
        page_product_id=product_id,
    )


@app.get("/api/chat/history", response_model=list[HistoryTurn])
def chat_history(request: Request) -> list[HistoryTurn]:
    user_id = current_user_id(request)
    if user_id is None:
        return []
    return load_history(user_id)


@app.post("/api/chat", response_model=ChatReply)
async def chat(body: ChatRequest, request: Request) -> ChatReply:
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")
    deps = shopper_deps(request, page_product_id(body.page_product_id))
    if deps.user_id is None:
        history = body.history
    else:
        history = [ChatTurn(role=turn.role, content=turn.content) for turn in load_history(deps.user_id)]
    try:
        reply = await run_chat(message, history, deps)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The shop assistant couldn't answer.") from exc
    if deps.user_id is not None:
        save_exchange(deps.user_id, message, reply)
    return reply


@app.post("/api/logout")
def logout(request: Request) -> Response:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        sessions.pop(token, None)
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


if PRODUCTS_DIR.is_dir():
    app.mount("/media/products", StaticFiles(directory=PRODUCTS_DIR), name="product-images")
