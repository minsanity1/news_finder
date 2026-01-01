"""Database migration script to add api_key_index column"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "data", "news.db")

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(ai_analysis_log)")
columns = [col[1] for col in cursor.fetchall()]

if "api_key_index" not in columns:
    print("Adding api_key_index column...")
    cursor.execute("ALTER TABLE ai_analysis_log ADD COLUMN api_key_index INTEGER DEFAULT 0")
    conn.commit()
    print("Done!")
else:
    print("Column api_key_index already exists.")

conn.close()
