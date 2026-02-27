import sqlite3

conn = sqlite3.connect('data/smartattend.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('Tables in database:')
for table in tables:
    print(f'  - {table[0]}')
    
if not tables:
    print('  No tables found!')

conn.close()
