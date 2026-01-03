"""
마이그레이션: 커뮤니티 수집 필드 추가

실행: cd backend && python -m migrations.add_community_fields

추가 필드:
- source_type: 소스 타입 (news / community)
- view_count: 조회수
- comment_count: 댓글수
- like_count: 추천수
- author: 작성자
"""
import sqlite3
import os
import sys

# 스크립트 위치 기준으로 DB 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(BACKEND_DIR, "news.db")


def migrate():
    print(f"Database path: {DB_PATH}")
    print(f"Database exists: {os.path.exists(DB_PATH)}")

    if not os.path.exists(DB_PATH):
        print("ℹ️  Database file not found. It will be created when you run the backend.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 테이블 존재 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news'")
    if not cursor.fetchone():
        print("ℹ️  'news' table does not exist yet. It will be created when you run the backend.")
        print("   The new columns will be included automatically.")
        conn.close()
        return

    # 새 컬럼 추가
    new_columns = [
        ("source_type", "VARCHAR(20) DEFAULT 'news'"),
        ("view_count", "INTEGER"),
        ("comment_count", "INTEGER"),
        ("like_count", "INTEGER"),
        ("author", "VARCHAR(100)"),
    ]

    added = 0
    skipped = 0

    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE news ADD COLUMN {col_name} {col_type}")
            print(f"✅ Added column: {col_name}")
            added += 1
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"⏭️  Column already exists: {col_name}")
                skipped += 1
            else:
                raise e

    conn.commit()
    conn.close()

    if added > 0:
        print(f"\n✅ Migration completed! Added {added} columns, skipped {skipped} existing.")
    else:
        print(f"\n✅ All columns already exist. No changes needed.")


if __name__ == "__main__":
    migrate()
