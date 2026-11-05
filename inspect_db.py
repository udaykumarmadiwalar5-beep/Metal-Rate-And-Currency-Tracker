import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='Uday@2004', database='metalcur')
cur = conn.cursor()
for metal, thresh in [('gold', 30000), ('silver', 1000), ('platinum', 20000)]:
    cur.execute('SELECT COUNT(*), MIN(price_per_gram), MAX(price_per_gram) FROM metal_price WHERE metal_type=%s', (metal,))
    c, minv, maxv = cur.fetchone()
    print(metal, 'count', c, 'min', minv, 'max', maxv)
    cur.execute('SELECT recorded_at, price_per_gram FROM metal_price WHERE metal_type=%s AND price_per_gram > %s ORDER BY recorded_at DESC LIMIT 10', (metal, thresh))
    rows = cur.fetchall()
    print('outliers >', thresh, len(rows), rows[:5])
conn.close()