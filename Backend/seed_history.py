
import mysql.connector
import datetime
import random

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Uday@2004",
        database="metalcur"
    )

def seed_history():
    bases = {
        "gold": 15260.40,
        "silver": 253.80,
        "platinum": 6182.50,
        "usd_inr": 94.91
    }
    
    conn = get_db()
    cur = conn.cursor()
    
    print("Cleaning old price data...")
    cur.execute("DELETE FROM metal_price")
    
    now = datetime.datetime.now()
    days_to_seed = 3 * 365 # 3 years
    
    print(f"Seeding {days_to_seed} days of history for each metal...")
    
    for metal, current_price in bases.items():
        price = current_price
    for metal, current_price in bases.items():
        price = current_price
        for d in range(days_to_seed):
            # For the most recent day, seed 10 points per hour to make candles look real
            if d == 0:
                hours_to_seed = range(24)
                points_per_hour = 10
            else:
                hours_to_seed = [0, 6, 12, 18]
                points_per_hour = 1
            
            for hour in hours_to_seed:
                for p_idx in range(points_per_hour):
                    # Spread points within the hour
                    minute = p_idx * 6
                    recorded_at = now - datetime.timedelta(days=d, hours=24-hour, minutes=60-minute)
                    
                    if recorded_at > now: continue # Don't seed future
                    
                    # Intraday volatility
                    vol = 0.001
                    price = price * (1 + random.uniform(-vol, vol))
                    
                    cur.execute("INSERT INTO metal_price (metal_type, price_per_gram, currency, recorded_at) VALUES (%s, %s, %s, %s)",
                                (metal, round(price, 2), "INR", recorded_at))
            
            # Daily trend walk backwards
            price = price * (1 + random.uniform(-0.002, 0.002)) * 0.9999
            
            if d % 50 == 0:
                conn.commit()
                
        print(f"DONE: {metal.upper()} seeded with high-fidelity history.")

    conn.commit()
    cur.close()
    conn.close()
    print("3-Year History Seeded Successfully.")

if __name__ == "__main__":
    seed_history()
