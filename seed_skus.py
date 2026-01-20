import sqlite3
import random

DB_FILE = "tasks.db"
RETAILERS = ["Amazon", "BestBuy", "Walmart", "Target"]
REGIONS = ["US", "UK", "CA", "EU"]

def seed_data():
    print("Seeding 10,000 SKUs...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Batch insert for speed
    data = []
    for i in range(10000):
        name = f"Product {i}"
        base = f"BASE_{i % 100}"
        sku = f"SKU_{i:05d}"
        ret = random.choice(RETAILERS)
        reg = random.choice(REGIONS)
        link = f"http://{ret.lower()}.com/{sku}"
        rating = round(random.uniform(1.0, 5.0), 1)
        rv = random.randint(0, 5000)
        
        data.append((name, base, sku, ret, reg, link, rating, rv))
        
    try:
        c.executemany('''INSERT OR IGNORE INTO skus (name, base_sku, sku, retailer, region, link, rating, review_count)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
        print("Seeding complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_data()
