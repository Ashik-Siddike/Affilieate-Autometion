import sqlite3
import datetime

DB_NAME = "amazon_products.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initializes the database with the products table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT UNIQUE,
            title TEXT,
            price TEXT,
            rating TEXT,
            review_count TEXT,
            image_url TEXT,
            product_url TEXT,
            is_published INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def check_product_status(asin):
    """
    Checks product status.
    Returns:
        None if not exists
        0 if exists but not published
        1 if exists and published
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_published FROM products WHERE asin = ?", (asin,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0] # Returns 0 or 1
    return None

def save_product(data_dict):
    """Saves a new product to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (asin, title, price, rating, review_count, image_url, product_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data_dict.get('asin'),
            data_dict.get('title'),
            data_dict.get('price'),
            data_dict.get('rating'),
            data_dict.get('review_count'),
            data_dict.get('image_url'),
            data_dict.get('product_url')
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Product with ASIN {data_dict.get('asin')} already exists.")
    finally:
        conn.close()

def mark_as_published(asin):
    """Marks a product as published."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_published = 1 WHERE asin = ?", (asin,))
    conn.commit()
    conn.close()

def get_similar_products(current_asin, limit=2):
    """
    Fetches random other products from the DB for comparison.
    Excludes the current product.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Fetch random products that are NOT the current one
    cursor.execute("""
        SELECT title, price, rating, review_count, image_url, product_url 
        FROM products 
        WHERE asin != ? 
        ORDER BY RANDOM() 
        LIMIT ?
    """, (current_asin, limit))
    rows = cursor.fetchall()
    conn.close()
    
    similar_products = []
    for row in rows:
        similar_products.append({
            'title': row[0],
            'price': row[1],
            'rating': row[2],
            'review_count': row[3],
            'image_url': row[4],
            'product_url': row[5]
        })
    return similar_products

def get_published_posts(limit=5):
    """
    Fetches a list of recently published posts for internal linking.
    Assuming we store the post link in the DB (we need to add a column for this or just use title).
    Wait, the current DB schema doesn't store the WordPress Post Link. 
    It only stores 'is_published'. 
    
    WE NEED TO UPDATE THE SCHEMA TO STORE THE WP LINK.
    For now, let's fetch published products and we'll have to rely on a search or just skip linking if we don't have the URL.
    
    Actually, let's modify the schema to add 'post_link' column.
    But for now to avoid migration headaches, I will just return the Title and ASIN.
    If we can't link to them without the URL, this feature is limited.
    
    Correction: The prompt said "Update database.py to fetch published post links".
    I must update Schema to store post_link.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Check if column exists, if not return empty for now (migration needed)
    try:
        cursor.execute("SELECT post_link FROM products LIMIT 1")
    except sqlite3.OperationalError:
        # Column missing
        return []

    cursor.execute("""
        SELECT title, post_link 
        FROM products 
        WHERE is_published = 1 AND post_link IS NOT NULL 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    posts = []
    for row in rows:
        posts.append({
            'title': row[0],
            'link': row[1]
        })
    return posts

def update_post_link(asin, post_link):
    """Updates the post_link for a published product."""
    conn = get_connection()
    cursor = conn.cursor()
    # First ensure column exists
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN post_link TEXT")
    except sqlite3.OperationalError:
        pass # Column likely exists
        
    cursor.execute("UPDATE products SET post_link = ? WHERE asin = ?", (post_link, asin))
    conn.commit()
    conn.close()
