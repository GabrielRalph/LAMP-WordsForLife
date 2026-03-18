import sqlite3
conn = sqlite3.connect('lamp.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT rid FROM symbol_links')

rows = cursor.fetchall()
rids = [row[0] for row in rows]
unique_rids = set(rids)

print(f"Total RIDs: {len(rids)}")

# me > me 
# we > us