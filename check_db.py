import sqlite3

conn = sqlite3.connect("fepal.db")
cur = conn.cursor()

print("TABUĽKY:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
for row in cur.fetchall():
    print("-", row[0])

print("\nSTOCK_MOVES STĹPCE:")
cur.execute("PRAGMA table_info(stock_moves);")
for row in cur.fetchall():
    print(row)
cur.execute("SELECT version_num FROM alembic_version;")
print("\nALEMBIC VERSION:", cur.fetchall())
conn.close()
