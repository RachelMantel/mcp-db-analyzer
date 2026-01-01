import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random

DB_PATH = Path(__file__).parent / "test.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def recreate_schema(conn: sqlite3.Connection):
    cur = conn.cursor()

    # Drop in reverse dependency order (safe for dev DB)
    cur.executescript("""
    DROP TABLE IF EXISTS shipment_items;
    DROP TABLE IF EXISTS shipments;
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS order_discounts;
    DROP TABLE IF EXISTS discounts;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS inventory;
    DROP TABLE IF EXISTS supplier_products;
    DROP TABLE IF EXISTS suppliers;
    DROP TABLE IF EXISTS product_categories;
    DROP TABLE IF EXISTS categories;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS customer_addresses;
    DROP TABLE IF EXISTS addresses;
    DROP TABLE IF EXISTS customer_tags;
    DROP TABLE IF EXISTS tags;
    DROP TABLE IF EXISTS customers;
    """)

    # Schema
    cur.executescript("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE addresses (
        id INTEGER PRIMARY KEY,
        city TEXT NOT NULL,
        street TEXT NOT NULL,
        zip TEXT
    );

    -- Many-to-many: customers <-> addresses
    CREATE TABLE customer_addresses (
        customer_id INTEGER NOT NULL,
        address_id INTEGER NOT NULL,
        is_primary INTEGER NOT NULL DEFAULT 0,
        label TEXT,
        PRIMARY KEY (customer_id, address_id),
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
        FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE
    );

    CREATE TABLE tags (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );

    -- Many-to-many: customers <-> tags
    CREATE TABLE customer_tags (
        customer_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (customer_id, tag_id),
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    );

    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        sku TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );

    -- Many-to-many: products <-> categories
    CREATE TABLE product_categories (
        product_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (product_id, category_id),
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
    );

    CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        country TEXT NOT NULL
    );

    -- Many-to-many: suppliers <-> products (with extra columns)
    CREATE TABLE supplier_products (
        supplier_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        supplier_sku TEXT NOT NULL,
        lead_time_days INTEGER NOT NULL DEFAULT 7,
        PRIMARY KEY (supplier_id, product_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    -- Inventory per product per location (simple: location as text)
    CREATE TABLE inventory (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        location TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity >= 0),
        updated_at TEXT NOT NULL,
        UNIQUE(product_id, location),
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('draft','paid','shipped','cancelled')),
        currency TEXT NOT NULL DEFAULT 'ILS',
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    );

    CREATE TABLE order_items (
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price REAL NOT NULL CHECK(unit_price >= 0),
        PRIMARY KEY (order_id, product_id),
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE discounts (
        id INTEGER PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL CHECK(type IN ('percent','fixed')),
        value REAL NOT NULL CHECK(value > 0),
        active INTEGER NOT NULL DEFAULT 1
    );

    -- Many-to-many: orders <-> discounts
    CREATE TABLE order_discounts (
        order_id INTEGER NOT NULL,
        discount_id INTEGER NOT NULL,
        PRIMARY KEY (order_id, discount_id),
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (discount_id) REFERENCES discounts(id)
    );

    CREATE TABLE shipments (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        carrier TEXT NOT NULL,
        tracking_number TEXT UNIQUE,
        shipped_at TEXT,
        delivered_at TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
    );

    -- One shipment can contain many items (products), and product can be in many shipments => many-to-many
    CREATE TABLE shipment_items (
        shipment_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        PRIMARY KEY (shipment_id, product_id),
        FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    -- Helpful indexes
    CREATE INDEX idx_orders_customer_id ON orders(customer_id);
    CREATE INDEX idx_order_items_product_id ON order_items(product_id);
    CREATE INDEX idx_inventory_product_id ON inventory(product_id);
    """)

    conn.commit()

def seed_data(conn: sqlite3.Connection, customers_n=80, products_n=120, orders_n=260):
    rnd = random.Random(42)
    cur = conn.cursor()

    now = datetime.utcnow()

    # Tags
    tag_names = ["vip", "new", "returning", "b2b", "newsletter", "high-risk", "wholesale", "student"]
    cur.executemany("INSERT INTO tags(name) VALUES (?)", [(t,) for t in tag_names])

    # Categories
    category_names = ["Electronics", "Home", "Sports", "Books", "Kids", "Office", "Fashion", "Beauty", "Food", "Garden"]
    cur.executemany("INSERT INTO categories(name) VALUES (?)", [(c,) for c in category_names])

    # Suppliers
    suppliers = [("Delta Supply", "IL"), ("NorthStar", "US"), ("EuroTrade", "DE"), ("Pacific Goods", "CN"), ("Local Hub", "IL")]
    cur.executemany("INSERT INTO suppliers(name, country) VALUES (?,?)", suppliers)

    # Customers + addresses + tags
    cities = ["Jerusalem", "Tel Aviv", "Haifa", "Rishon LeZion", "Petah Tikva", "Beer Sheva", "Netanya", "Ashdod"]
    streets = ["Herzl", "Jaffa", "Ben Yehuda", "Dizengoff", "Rothschild", "King George", "Weizmann", "Begin"]

    for i in range(1, customers_n + 1):
        created = (now - timedelta(days=rnd.randint(0, 900))).isoformat()
        name = f"Customer {i:03d}"
        email = f"customer{i:03d}@example.com"
        phone = f"+972-50-{rnd.randint(1000000, 9999999)}"
        cur.execute(
            "INSERT INTO customers(name,email,phone,created_at) VALUES (?,?,?,?)",
            (name, email, phone, created),
        )
        customer_id = cur.lastrowid

        # 1-3 addresses per customer
        addr_count = rnd.randint(1, 3)
        addr_ids = []
        for a in range(addr_count):
            city = rnd.choice(cities)
            street = rnd.choice(streets)
            zip_code = str(rnd.randint(10000, 99999))
            cur.execute("INSERT INTO addresses(city,street,zip) VALUES (?,?,?)", (city, street, zip_code))
            addr_id = cur.lastrowid
            addr_ids.append(addr_id)

        for idx, addr_id in enumerate(addr_ids):
            is_primary = 1 if idx == 0 else 0
            label = "Home" if idx == 0 else ("Work" if idx == 1 else "Other")
            cur.execute(
                "INSERT INTO customer_addresses(customer_id,address_id,is_primary,label) VALUES (?,?,?,?)",
                (customer_id, addr_id, is_primary, label),
            )

        # 0-3 tags per customer
        tag_pick = rnd.sample(range(1, len(tag_names) + 1), k=rnd.randint(0, 3))
        for tag_id in tag_pick:
            cur.execute("INSERT INTO customer_tags(customer_id,tag_id) VALUES (?,?)", (customer_id, tag_id))

    # Products + categories + supplier_products + inventory
    for i in range(1, products_n + 1):
        created = (now - timedelta(days=rnd.randint(0, 1200))).isoformat()
        sku = f"SKU-{i:05d}"
        name = f"Product {i:03d}"
        price = round(rnd.uniform(5, 1500), 2)
        is_active = 1 if rnd.random() > 0.05 else 0

        cur.execute(
            "INSERT INTO products(sku,name,price,is_active,created_at) VALUES (?,?,?,?,?)",
            (sku, name, price, is_active, created),
        )
        product_id = cur.lastrowid

        # 1-3 categories per product
        cat_ids = rnd.sample(range(1, len(category_names) + 1), k=rnd.randint(1, 3))
        for cat_id in cat_ids:
            cur.execute("INSERT INTO product_categories(product_id,category_id) VALUES (?,?)", (product_id, cat_id))

        # 1-2 suppliers per product
        supp_ids = rnd.sample(range(1, len(suppliers) + 1), k=rnd.randint(1, 2))
        for supp_id in supp_ids:
            supplier_sku = f"S{supp_id}-P{product_id}"
            lead = rnd.randint(2, 21)
            cur.execute(
                "INSERT INTO supplier_products(supplier_id,product_id,supplier_sku,lead_time_days) VALUES (?,?,?,?)",
                (supp_id, product_id, supplier_sku, lead),
            )

        # inventory in 2 locations
        for location in ["WH-A", "WH-B"]:
            qty = rnd.randint(0, 300)
            cur.execute(
                "INSERT INTO inventory(product_id,location,quantity,updated_at) VALUES (?,?,?,?)",
                (product_id, location, qty, now.isoformat()),
            )

    # Discounts
    discounts = [
        ("WELCOME10", "percent", 10),
        ("VIP15", "percent", 15),
        ("FREESHIP", "fixed", 25),
        ("BLACK50", "percent", 50),
        ("SAVE40", "fixed", 40),
    ]
    cur.executemany("INSERT INTO discounts(code,type,value) VALUES (?,?,?)", discounts)

    # Orders + order_items + order_discounts + shipments + shipment_items
    statuses = ["draft", "paid", "shipped", "cancelled"]
    carriers = ["DHL", "Israel Post", "UPS", "FedEx"]

    for _ in range(orders_n):
        customer_id = rnd.randint(1, customers_n)
        status = rnd.choices(statuses, weights=[10, 50, 30, 10], k=1)[0]
        created = (now - timedelta(days=rnd.randint(0, 365))).isoformat()

        cur.execute(
            "INSERT INTO orders(customer_id,status,currency,created_at) VALUES (?,?,?,?)",
            (customer_id, status, "ILS", created),
        )
        order_id = cur.lastrowid

        # 1-6 items in each order (unique product per order because PK(order_id, product_id))
        item_count = rnd.randint(1, 6)
        product_ids = rnd.sample(range(1, products_n + 1), k=item_count)
        for pid in product_ids:
            # unit price snapshot from products table
            cur.execute("SELECT price FROM products WHERE id = ?", (pid,))
            unit_price = float(cur.fetchone()["price"])
            qty = rnd.randint(1, 5)
            cur.execute(
                "INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES (?,?,?,?)",
                (order_id, pid, qty, unit_price),
            )

        # 0-2 discounts per order
        if rnd.random() < 0.35:
            disc_count = rnd.randint(1, 2)
            disc_ids = rnd.sample(range(1, len(discounts) + 1), k=disc_count)
            for did in disc_ids:
                cur.execute("INSERT INTO order_discounts(order_id,discount_id) VALUES (?,?)", (order_id, did))

        # shipment for shipped orders (sometimes split into 1-2 shipments)
        if status == "shipped":
            shipment_count = 1 if rnd.random() < 0.8 else 2
            remaining = product_ids[:]
            for s in range(shipment_count):
                carrier = rnd.choice(carriers)
                tracking = f"TRK-{order_id}-{s+1}-{rnd.randint(1000,9999)}"
                shipped_at = (now - timedelta(days=rnd.randint(1, 30))).isoformat()
                delivered_at = (now - timedelta(days=rnd.randint(0, 10))).isoformat() if rnd.random() < 0.7 else None

                cur.execute(
                    "INSERT INTO shipments(order_id,carrier,tracking_number,shipped_at,delivered_at) VALUES (?,?,?,?,?)",
                    (order_id, carrier, tracking, shipped_at, delivered_at),
                )
                shipment_id = cur.lastrowid

                # put some items in this shipment
                take = max(1, len(remaining) // (shipment_count - s))
                chunk = remaining[:take]
                remaining = remaining[take:]
                for pid in chunk:
                    # quantity shipped - use a random 1-3 (not necessarily equal to ordered; fine for demo)
                    cur.execute(
                        "INSERT INTO shipment_items(shipment_id,product_id,quantity) VALUES (?,?,?)",
                        (shipment_id, pid, rnd.randint(1, 3)),
                    )

    conn.commit()

def quick_sanity(conn: sqlite3.Connection):
    cur = conn.cursor()
    tables = [
        "customers", "addresses", "customer_addresses",
        "tags", "customer_tags",
        "products", "categories", "product_categories",
        "suppliers", "supplier_products", "inventory",
        "orders", "order_items", "discounts", "order_discounts",
        "shipments", "shipment_items"
    ]
    print("📊 Row counts:")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) AS c FROM {t}")
        c = cur.fetchone()[0]
        print(f"  - {t}: {c}")

    print("\n🔎 Example join (customer -> orders -> items -> products):")
    cur.execute("""
    SELECT c.name AS customer, o.id AS order_id, o.status,
           SUM(oi.quantity * oi.unit_price) AS order_total,
           COUNT(*) AS distinct_products
    FROM customers c
    JOIN orders o ON o.customer_id = c.id
    JOIN order_items oi ON oi.order_id = o.id
    GROUP BY c.id, o.id
    ORDER BY o.id DESC
    LIMIT 5;
    """)
    for row in cur.fetchall():
        print(dict(row))

def main():
    conn = connect()
    recreate_schema(conn)
    seed_data(conn, customers_n=80, products_n=120, orders_n=260)
    quick_sanity(conn)
    conn.close()
    print(f"\n✅ Database created at: {DB_PATH}")

if __name__ == "__main__":
    main()
