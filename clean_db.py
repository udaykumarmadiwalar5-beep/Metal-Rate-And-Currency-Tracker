import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='Uday@2004', database='metalcur')
cur = conn.cursor()
# Check max prices
cur.execute("SELECT metal_type, MAX(price_per_gram) as max_price FROM metal_price GROUP BY metal_type")
rows = cur.fetchall()
for row in rows:
    print(f"{row[0]}: max {row[1]}")
# Delete bad gold prices
cur.execute("DELETE FROM metal_price WHERE metal_type='gold' AND price_per_gram > 30000")
print("Deleted", cur.rowcount, "bad gold prices")
# Delete bad silver
cur.execute("DELETE FROM metal_price WHERE metal_type='silver' AND price_per_gram > 1000")
print("Deleted", cur.rowcount, "bad silver prices")
# Delete bad platinum
cur.execute("DELETE FROM metal_price WHERE metal_type='platinum' AND price_per_gram > 20000")
print("Deleted", cur.rowcount, "bad platinum prices")
conn.commit()
cur.close()
conn.close()
print('Cleaned bad price data')