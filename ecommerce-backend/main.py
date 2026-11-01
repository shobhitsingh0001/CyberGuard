import random
import asyncio
import re
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session
from urllib.parse import unquote_plus

from database import engine, Base, get_db
from models import Product, Order, OrderItem
from schemas import (
    ProductCreate, ProductResponse,
    OrderCreate, OrderResponse, OrderStatusUpdate
)
from cyberguard_logger import send_to_cyberguard
from auth import router as auth_router


app = FastAPI()

# Allow frontend (Home.html / script.js) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # dev ke liye sab allow; production me specific origin daalna
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CYBERGUARD MONITORING MIDDLEWARE
# ============================================================

IGNORED_PATHS = {"/docs", "/openapi.json", "/redoc", "/favicon.ico"}
MAX_INSPECTED_BODY_BYTES = 64 * 1024
SQLI_PATTERNS = (
    r"\bunion\b.{0,20}\bselect\b",
    r"\b(?:or|and)\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+",
    r"['\"]\s*(?:or|and)\b",
    r";\s*(?:select|insert|update|delete|drop|alter)\b",
    r"\bselect\b.{0,30}\bfrom\b",
    r"\b(?:sleep|benchmark)\s*\(",
    r"--(?:\s|$)",
)


def contains_sql_injection_pattern(body: bytes) -> bool:
    text = unquote_plus(body.decode("utf-8", errors="replace"))
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in SQLI_PATTERNS)


@app.middleware("http")
async def cyberguard_logging_middleware(request: Request, call_next):
    # Preflight aur docs ka noise log mat karo
    if request.method == "OPTIONS" or request.url.path in IGNORED_PATHS:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    content_length = request.headers.get("content-length")
    sql_injection_suspected = False
    if (
        request.method in {"POST", "PUT", "PATCH"}
        and request.headers.get("content-type", "").lower().startswith(
            ("application/json", "application/x-www-form-urlencoded")
        )
        and content_length
        and content_length.isdigit()
        and int(content_length) <= MAX_INSPECTED_BODY_BYTES
    ):
        sql_injection_suspected = contains_sql_injection_pattern(
            await request.body()
        )

    log_payload = {
        "ip": client_ip,
        "method": request.method,
        "path": request.url.path,
        "query_string": str(request.url.query),
        "user_agent": request.headers.get("user-agent", ""),
        "sql_injection_suspected": sql_injection_suspected,
    }

    # Fire-and-forget: CyberGuard slow/down ho to bhi store na atke
    asyncio.create_task(send_to_cyberguard(log_payload))

    return await call_next(request)


# Create database tables
Base.metadata.create_all(bind=engine)

# Login / Signup routes (/auth/register, /auth/login, ...)
app.include_router(auth_router)


@app.get("/")
def home():
    return {"message": "Product Store API"}


# ============================================================
# PRODUCT ROUTES
# ============================================================

@app.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    new_product = Product(
        name=product.name,
        category=product.category,
        icon=product.icon,
        image_url=product.image_url,
        price=product.price,
        quantity=product.quantity
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@app.get("/products")
def get_products(search: str = "", db: Session = Depends(get_db)):
    query = db.query(Product)
    if search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(Product.name.ilike(term), Product.category.ilike(term))
        )
    products = query.all()
    return products


@app.get("/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = product_data.name
    product.category = product_data.category
    product.icon = product_data.icon
    product.image_url = product_data.image_url
    product.price = product_data.price
    product.quantity = product_data.quantity

    db.commit()
    db.refresh(product)

    return product


@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}


# ============================================================
# ORDER ROUTES
# ============================================================

@app.post("/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    if not order_data.items:
        raise HTTPException(status_code=400, detail="Cart is empty, cannot place order")

    total = sum(item.price for item in order_data.items)
    order_code = "APX-" + str(random.randint(1000, 9999))

    new_order = Order(
        order_code=order_code,
        total=total,
        status="Processing"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in order_data.items:
        db.add(OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            name=item.name,
            image_url=item.image_url,
            price=item.price
        ))

    db.commit()
    db.refresh(new_order)

    return new_order


@app.get("/orders", response_model=list[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return orders


@app.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allowed_statuses = ["Processing", "Shipped", "Delivered", "Cancelled"]
    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(allowed_statuses)}"
        )

    order.status = status_data.status
    db.commit()
    db.refresh(order)

    return order


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order
