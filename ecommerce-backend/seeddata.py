"""
Ye script store.db me 10 products daal deta hai - ek har category ke liye.
Chalane se pehle backend ek baar run kar lo taaki tables ban jayein, phir:
    python seeddata.py
"""

from database import SessionLocal, engine, Base
from models import Product

Base.metadata.create_all(bind=engine)

seed_products = [
    {"name": "Wireless Headphones",       "category": "Audio",              "image_url": "https://m.media-amazon.com/images/I/61JU2HicMQL._AC_UY327_FMwebp_QL65_.jpg", "price": 1999,  "quantity": 25},
    {"name": "Smart Fitness Watch",       "category": "Wearables",          "image_url": "https://m.media-amazon.com/images/I/61sFBIcJAqL._AC_UL480_FMwebp_QL65_.jpg", "price": 3499,  "quantity": 40},
    {"name": "14-inch Laptop",            "category": "Computers",          "image_url": "https://m.media-amazon.com/images/I/61vTx-Qa1QL._AC_UY327_FMwebp_QL65_.jpg", "price": 54999, "quantity": 10},
    {"name": "Ergonomic Backpack",        "category": "Accessories",        "image_url": "https://m.media-amazon.com/images/I/61jI4jxdGmL._AC_UY327_FMwebp_QL65_.jpg", "price": 1299,  "quantity": 60},
    {"name": "Cotton Casual Shirt",       "category": "Fashion",            "image_url": "https://m.media-amazon.com/images/I/61ExjDlFXML._AC_SX416_CB1169409_QL70_.jpg", "price": 899,   "quantity": 50},
    {"name": "Cricket Kit",               "category": "Sports",             "image_url": "https://m.media-amazon.com/images/I/71Tjs7ey+lL._AC_UL480_FMwebp_QL65_.jpg", "price": 2499,  "quantity": 20},
    {"name": "Non-Stick Cookware Set",    "category": "Home & Kitchen",     "image_url": "https://m.media-amazon.com/images/I/81SMWpeF6pL._AC_SX416_CB1169409_QL70_.jpg", "price": 1799,  "quantity": 30},
    {"name": "Herbal Face Serum",         "category": "Beauty",             "image_url": "https://m.media-amazon.com/images/I/613M5P9hUGL._AC_SX416_CB1169409_QL70_.jpg", "price": 549,   "quantity": 45},
    {"name": "Organic Grocery Combo",     "category": "Grocery",            "image_url": "https://m.media-amazon.com/images/I/71J-C6RDaeL._AC_SX416_CB1169409_QL70_.jpg", "price": 699,   "quantity": 70},
    {"name": "Notebook & Stationery Set", "category": "Books & Stationery", "image_url": "https://m.media-amazon.com/images/I/81T05w0B3lL._AC_UY327_FMwebp_QL65_.jpg", "price": 349,   "quantity": 100},
]

db = SessionLocal()
try:
    db.query(Product).delete()
    for p in seed_products:
        db.add(Product(**p))
    db.commit()
    print(f"Seeded {len(seed_products)} products into store.db")
finally:
    db.close()
