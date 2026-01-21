import sqlite3

conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS skus")

cursor.execute('''CREATE TABLE IF NOT EXISTS skus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    base_sku TEXT NOT NULL,
                    sku TEXT UNIQUE NOT NULL,
                    retailer TEXT NOT NULL,
                    region TEXT NOT NULL,
                    link TEXT NOT NULL,
                    rating REAL,
                    rating_count INTEGER,
                    review_count INTEGER,
                    review_count_fresh INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')  


conn.commit()
conn.close()