import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Uday@2004",
    "database": "metalcur"
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, username, email FROM users LIMIT 10")
    users = cur.fetchall()
    
    print("\n" + "=" * 70)
    print("AVAILABLE USERS IN DATABASE")
    print("=" * 70)
    
    for user in users:
        print(f"\nID: {user['user_id']}")
        print(f"  Username: {user['username']}")
        print(f"  Email: {user['email']}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
