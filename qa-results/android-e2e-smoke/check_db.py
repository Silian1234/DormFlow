import sqlite3
import sys
from pathlib import Path

db = Path(sys.argv[1])
connection = sqlite3.connect(db)
connection.row_factory = sqlite3.Row
users = [dict(row) for row in connection.execute("SELECT email, name, room, role FROM users ORDER BY id")]
sessions = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
print(f"users={len(users)} sessions={sessions}")
for user in users:
    print(user)
if not users or sessions < 1:
    raise SystemExit(2)
