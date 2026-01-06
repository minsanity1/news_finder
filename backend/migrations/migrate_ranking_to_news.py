#!/usr/bin/env python3
"""
기존 source_type='ranking' 데이터를 'news'로 마이그레이션

실행:
  cd backend
  python migrations/migrate_ranking_to_news.py
"""
import sqlite3
from pathlib import Path

# DB 경로
DB_PATH = Path(__file__).parent.parent / "data" / "news.db"


def migrate():
    if not DB_PATH.exists():
        print(f"❌ DB 파일이 없습니다: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 현재 분포 확인
    print("📊 현재 source_type 분포:")
    cursor.execute("SELECT source_type, COUNT(*) FROM news GROUP BY source_type")
    for row in cursor.fetchall():
        print(f"   {row[0] or 'NULL'}: {row[1]}개")

    # ranking → news 업데이트
    cursor.execute("SELECT COUNT(*) FROM news WHERE source_type = 'ranking'")
    count = cursor.fetchone()[0]

    if count == 0:
        print("\n✅ 마이그레이션 대상이 없습니다.")
        conn.close()
        return

    print(f"\n🔄 {count}개의 'ranking' 레코드를 'news'로 변경합니다...")

    cursor.execute("UPDATE news SET source_type = 'news' WHERE source_type = 'ranking'")
    conn.commit()

    # 결과 확인
    print("\n📊 변경 후 source_type 분포:")
    cursor.execute("SELECT source_type, COUNT(*) FROM news GROUP BY source_type")
    for row in cursor.fetchall():
        print(f"   {row[0] or 'NULL'}: {row[1]}개")

    print("\n✅ 마이그레이션 완료!")
    conn.close()


if __name__ == "__main__":
    migrate()
