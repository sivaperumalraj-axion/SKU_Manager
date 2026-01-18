import sqlite3

def fix():
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    
    print("Removing duplicate process items for VerifyProcess_01...")
    
    # Check current items
    c.execute("""
        SELECT id, sequence_order 
        FROM process_items 
        WHERE process_id = (SELECT id FROM processes WHERE name='VerifyProcess_01')
        ORDER BY sequence_order
    """)
    rows = c.fetchall()
    print(f"Current items: {rows}")
    
    if len(rows) > 1:
        # Keep the first one (lowest ID or lowest sequence)
        # rows is list of (id, seq)
        # We want to delete the second one
        to_delete = rows[1][0]
        print(f"Deleting item ID: {to_delete}")
        
        c.execute("DELETE FROM process_items WHERE id = ?", (to_delete,))
        conn.commit()
        print("Deleted.")
    else:
        print("No duplicates found (or already fixed).")
        
    conn.close()

if __name__ == "__main__":
    fix()
