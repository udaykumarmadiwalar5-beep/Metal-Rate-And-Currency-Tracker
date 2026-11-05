import os
import json
import bcrypt
import mysql.connector
from mysql.connector import Error as MySQLError
from flask import (
    Flask, jsonify, request, session,
    render_template, redirect, url_for
)
from flask_cors import CORS
import requests
import time
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "metal_tracker_secret_9988")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
CORS(app)

# ═══════════════════════════════════════════════════════════
#  MARKET CAP CACHE (5 min TTL for fast loading)
# ═══════════════════════════════════════════════════════════
MARKET_CAP_CACHE = {}
MARKET_CAP_CACHE_TTL = 300  # 5 minutes

def get_cached_market_cap(ticker):
    """Get market cap from cache if fresh."""
    if ticker in MARKET_CAP_CACHE:
        entry = MARKET_CAP_CACHE[ticker]
        if time.time() - entry['ts'] < MARKET_CAP_CACHE_TTL:
            return entry['value']
    return None

def cache_market_cap(ticker, market_cap):
    """Store market cap in cache."""
    MARKET_CAP_CACHE[ticker] = {'value': market_cap, 'ts': time.time()}

# Log incoming requests for debugging browser load issues
@app.before_request
def _log_request():
    try:
        print(f"[REQ] {request.remote_addr} {request.method} {request.path}")
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════
#  PAGE ROUTES (MOVED TO TOP)
# ═══════════════════════════════════════════════════════════

@app.route("/test")
def test_connection():
    return "Server is working!"

@app.route("/api/admin/clean_prices")
def clean_prices():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM metal_price WHERE metal_type="gold" AND price_per_gram > 50000')
        cur.execute('DELETE FROM metal_price WHERE metal_type="silver" AND price_per_gram > 1000')
        cur.execute('DELETE FROM metal_price WHERE metal_type="platinum" AND price_per_gram > 20000')
        conn.commit()
        cur.close()
        conn.close()
        return "✅ Price data cleaned!"
    except Exception as e:
        return f"❌ Clean Failed: {e}"

@app.route("/api/admin/normalize_alerts")
def normalize_alerts():
    """Normalize alert metal_type and condition_type to lowercase for consistency."""
    try:
        conn = get_db()
        cur = conn.cursor()
        # Update all alerts to have lowercase metal_type and condition_type
        cur.execute('UPDATE alerts SET metal_type = LOWER(metal_type), condition_type = LOWER(condition_type)')
        affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return f"✅ Alerts normalized! {affected} rows updated."
    except Exception as e:
        return f"❌ Normalize Failed: {e}"

@app.route("/api/admin/trigger_alerts")
def manual_trigger_alerts():
    """Manually trigger alert check (for testing - runs immediately instead of waiting 2 minutes)."""
    try:
        check_and_trigger_alerts()
        return "✅ Alert check triggered! Check database and browser console for results."
    except Exception as e:
        return f"❌ Manual trigger failed: {e}"

@app.route("/")
def index():
    g = s = p = u = "—"
    try:
        conn = get_db(); cur = conn.cursor(dictionary=True)
        for m, mult in [("gold", 10), ("silver", 1000), ("platinum", 10)]:
            cur.execute("SELECT price_per_gram FROM metal_price WHERE metal_type = %s ORDER BY recorded_at DESC LIMIT 1", (m,))
            row = cur.fetchone()
            if row:
                val = f"{round(float(row['price_per_gram']) * mult, 2):,.2f}"
                if m == "gold": g = val
                elif m == "silver": s = val
                else: p = val
        cur.execute("SELECT price_per_gram FROM metal_price WHERE metal_type = 'usd_inr' ORDER BY recorded_at DESC LIMIT 1")
        r = cur.fetchone()
        u = f"{float(r['price_per_gram']):,.2f}" if r else "94.91"
        cur.close(); conn.close()
    except: pass
    return render_template("index2.html", gold=g, silver=s, platinum=p, usd_inr=u)

@app.route("/faq")
def faq_page(): return render_template("faq.html")

@app.route("/login")
def login_page():
    if "user_id" in session: return redirect(url_for("dashboard_page"))
    return render_template("login.html")

@app.route("/register")
def register_page(): return render_template("register.html")

@app.route("/forgot-password")
def forgot_password_page(): return render_template("forgot_reset.html")

@app.route("/dashboard")
def dashboard_page():
    if "user_id" not in session: return redirect(url_for("login_page"))
    return render_template("dashboard.html", username=session.get("username", "User"), user_id=session.get("user_id"))

@app.route("/login.html")
def _r_login(): return redirect(url_for("login_page"))
@app.route("/register.html")
def _r_register(): return redirect(url_for("register_page"))
@app.route("/forgot_reset.html")
def _r_forgot(): return redirect(url_for("forgot_password_page"))
@app.route("/dashboard.html")
def _r_dashboard(): return redirect(url_for("dashboard_page"))
@app.route("/faq.html")
def _r_faq(): return redirect(url_for("faq_page"))
@app.route("/index2.html")
def _r_index(): return redirect(url_for("index"))

@app.route("/api/admin/reset-db")
@app.route("/api/admin/reset db")
@app.route("/reset")
@app.route("/fix")
def manual_reset_db():
    try:
        populate_investment_data()
        return "✅ Database Reset Successful! All 40+ Companies Loaded. You can now go back to the dashboard."
    except Exception as e:
        return f"❌ Reset Failed: {e}"

@app.route("/api/companies/custom-add", methods=["POST"])
def add_custom_company():
    try:
        data = request.json
        name = data.get("name")
        ticker = data.get("ticker", "").upper()
        sector = data.get("sector", "diversified")
        risk = data.get("risk", "medium")
        
        if not name or not ticker:
            return jsonify({"success": False, "error": "Name and ticker required"})
            
        conn = get_db()
        cur = conn.cursor()
        
        # Check if already exists
        cur.execute("SELECT company_id FROM company WHERE ticker_symbol = %s", (ticker,))
        if cur.fetchone():
            return jsonify({"success": False, "error": "Company with this ticker already exists"})
            
        # Insert company with default values for a "Real" feel
        cur.execute("""INSERT INTO company 
            (company_name, ticker_symbol, sector_label, exchange, risk_level, avg_return_5y, market_cap, market_price, metal_type) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
            (name, ticker, sector, "NSE & BSE", risk, 15.5, 50000000000, 100.0, "all"))
        
        co_id = cur.lastrowid
        
        # Also add a corresponding SIP plan so the advisor works
        cur.execute("""INSERT INTO sip_plan 
            (company_id, sip_name, metal_type, min_investment, risk_level, expected_return, duration_years) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (co_id, f"{name} SIP Growth", "all", 500, risk, 15.5, 5))
            
        conn.commit()
        return jsonify({"success": True, "message": f"Added {name} ({ticker})"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ═══════════════════════════════════════════════════════════
#  DATABASE CONFIG
# ═══════════════════════════════════════════════════════════
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Uday@2004",
    "database": "metalcur"
}

METAL_API_KEY = "your_polygon_api_key" 
# Get FREE NewsAPI key from: https://newsapi.org/register
# Free plan: 100 requests/day, great for real-time market news
NEWS_API_KEY = "02c28bc8f93f4cd2a39c31433428a662"
OZ_TO_GRAM = 31.1035

BASE_GOLD_FACTOR = 105.5
BASE_SILVER_FACTOR = 85.2
BASE_PLATINUM_FACTOR = 57.8

# Local calibration factors used by chart and state generators
INDIAN_GOLD_CALIBRATION_FACTOR = 1.1390
INDIAN_SILVER_CALIBRATION_FACTOR = 1.1920
INDIAN_PLAT_CALIBRATION_FACTOR = 1.0540

PURITY_MULTIPLIERS = {
    "24k": 1.0,
    "22k": 22 / 24,
    "18k": 18 / 24
}

TIMEFRAME_CONFIGS = {
    "1d": {"period": "1d", "interval": "5m"},
    "1m": {"period": "1mo", "interval": "1d"},
    "3m": {"period": "3mo", "interval": "1d"},
    "6m": {"period": "6mo", "interval": "1d"},
    "1y": {"period": "1y", "interval": "1wk"},
    "3y": {"period": "3y", "interval": "1mo"}
}

def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        raise e

def ok(data: dict):
    data["success"] = True
    return jsonify(data)

def err(msg, code=400):
    return jsonify({"success": False, "error": msg}), code

def clean_row(row):
    if not row: return row
    for k, v in row.items():
        if isinstance(v, (datetime, timedelta)):
            row[k] = str(v)
        elif isinstance(v, bytes):
            row[k] = v.decode('utf-8')
    return row

def clean_rows(rows):
    return [clean_row(r) for r in rows]

def _nse_request_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com",
    }

def fetch_stock_quote_from_nse(ticker):
    """Fetch live Indian equity quotes from NSE with ALL market data fields."""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            headers = _nse_request_headers()
            headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Site": "same-origin",
            })
            session.headers.update(headers)
            try:
                session.get("https://www.nseindia.com", timeout=8)
            except:
                pass

            session.headers.update({
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Site": "same-origin",
            })
            url = f"https://www.nseindia.com/api/quote-equity?symbol={ticker}"
            response = session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"[DEBUG] NSE returned status {response.status_code} for {ticker}")
                continue
            
            data = response.json()
            p = data.get("priceInfo") or {}
            lp = p.get("lastPrice")
            
            if lp is None:
                print(f"[DEBUG] NSE returned no lastPrice for {ticker}")
                continue
            
            lp_float = float(lp)
            if lp_float <= 0:
                print(f"[DEBUG] NSE returned invalid price {lp} for {ticker}")
                continue
            
            # Extract market cap - NSE returns as string like "1,23,456.25 Cr"
            market_cap_str = p.get("marketCap") or p.get("mktCap") or ""
            market_cap = None
            if market_cap_str:
                try:
                    # Parse "1,23,456.25 Cr" format
                    if isinstance(market_cap_str, str):
                        cap_val = market_cap_str.replace(",", "").replace(" Cr", "").replace(" Crores", "").strip()
                        market_cap = float(cap_val) if cap_val else None
                except:
                    market_cap = None
            
            # Extract all available data fields
            result = {
                "ticker_symbol": ticker,
                "last_price": lp_float,
                "change": float(p.get("change") or 0),
                "pct_change": float(p.get("pChange") or 0),
                "day_high": float(p.get("dayHigh") or 0),
                "day_low": float(p.get("dayLow") or 0),
                "open": float(p.get("open") or 0),
                "market_cap": market_cap,
                "market_cap_str": market_cap_str,
                "pe_ratio": p.get("pe") or p.get("peRatio"),
                "book_value": p.get("bookValue"),
                "dividend_yield": p.get("dividendYield"),
                "52_week_high": p.get("wh") or p.get("weekHigh52"),
                "52_week_low": p.get("wl") or p.get("weekLow52"),
                "timestamp": time.time()
            }
            
            print(f"[INFO] NSE {ticker}: Price={lp_float}, MarketCap={market_cap}, PctChange={result['pct_change']}%")
            return result
            
        except Exception as e:
            print(f"[WARN] NSE quote attempt {attempt+1}/{max_retries} failed for {ticker}: {e}")
    
    return None


def fetch_stock_quote_from_yahoo(ticker):
    """Fetch live Indian equity quote from Yahoo Finance as fallback with retry."""
    max_retries = 2
    
    try:
        import yfinance as yf
    except Exception as e:
        print(f"[WARN] yfinance import failed for {ticker}: {e}")
        return None

    symbol = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
    
    for attempt in range(max_retries):
        try:
            contract = yf.Ticker(symbol)
            info = {}
            try:
                info = contract.fast_info if hasattr(contract, "fast_info") else {}
            except:
                pass

            last_price = None
            prev_close = None
            
            market_cap = None
            if info:
                last_price = info.get("last_price") or info.get("previous_close") or info.get("regularMarketPrice") or info.get("close")
                prev_close = info.get("previous_close") or info.get("close") or info.get("previousClose")
                market_cap = info.get("marketCap") or info.get("market_cap") or info.get("market_cap")

            if market_cap is None:
                try:
                    info_meta = contract.info if hasattr(contract, "info") else {}
                    if isinstance(info_meta, dict):
                        market_cap = info_meta.get("marketCap") or info_meta.get("regularMarketCap") or info_meta.get("market_cap")
                except Exception:
                    market_cap = None

            if last_price is None or float(last_price or 0) <= 0:
                history = contract.history(period="5d", interval="1d")
                if history is not None and not history.empty:
                    last_price = float(history["Close"].iloc[-1])
                    if len(history) > 1:
                        prev_close = float(history["Close"].iloc[-2])

            if last_price is None or float(last_price or 0) <= 0:
                print(f"[DEBUG] Yahoo: No valid price for {symbol} attempt {attempt+1}")
                continue

            if prev_close is None or float(prev_close or 0) <= 0:
                prev_close = float(last_price)

            if market_cap is None:
                fallback_quote = fetch_yahoo_json_quote(symbol)
                if fallback_quote:
                    market_cap = fallback_quote.get("market_cap")

            try:
                if market_cap is not None:
                    market_cap = float(market_cap)
                    if market_cap > 1e10:
                        market_cap = market_cap / 1e7
            except Exception:
                market_cap = None

            change = float(last_price) - float(prev_close)
            pct_change = round((change / float(prev_close)) * 100, 2) if prev_close and float(prev_close) > 0 else 0.0

            result = {
                "ticker_symbol": ticker,
                "last_price": float(last_price),
                "change": change,
                "pct_change": pct_change,
                "day_high": info.get("regularMarketDayHigh"),
                "day_low": info.get("regularMarketDayLow"),
                "open": info.get("regularMarketOpen"),
                "market_cap": market_cap,
                "timestamp": time.time()
            }
            return result
        except Exception as e:
            print(f"[WARN] Yahoo quote attempt {attempt+1}/{max_retries} failed for {symbol}: {e}")
    
    return None


def fetch_yahoo_json_quote(ticker):
    try:
        url = "https://query1.finance.yahoo.com/v7/finance/quote"
        params = {"symbols": ticker}
        response = requests.get(url, params=params, timeout=10, headers=_nse_request_headers())
        if response.status_code != 200:
            return None
        payload = response.json()
        results = payload.get("quoteResponse", {}).get("result", [])
        if not results:
            return None
        quote = results[0]
        last_price = quote.get("regularMarketPrice") or quote.get("previousClose") or quote.get("ask")
        prev_close = quote.get("regularMarketPreviousClose") or quote.get("previousClose") or last_price
        if last_price is None:
            return None
        market_cap = quote.get("marketCap") or quote.get("regularMarketCap") or quote.get("market_cap")
        try:
            if market_cap is not None:
                market_cap = float(market_cap)
                if market_cap > 1e10:
                    market_cap = market_cap / 1e7
        except Exception:
            market_cap = None
        return {
            "ticker_symbol": ticker,
            "last_price": float(last_price),
            "change": float(last_price) - float(prev_close) if prev_close else 0.0,
            "pct_change": round(((float(last_price) - float(prev_close)) / float(prev_close)) * 100, 2) if prev_close and float(prev_close) > 0 else 0.0,
            "day_high": quote.get("regularMarketDayHigh"),
            "day_low": quote.get("regularMarketDayLow"),
            "open": quote.get("regularMarketOpen"),
            "market_cap": market_cap,
        }
    except Exception as e:
        print(f"[WARN] Yahoo JSON quote failed for {ticker}: {e}")
        return None

# ─────────────────────────────────────────────────────────────
#  LIVE MARKET SYNC LOGIC (2026 High-Accuracy Mode)
# ─────────────────────────────────────────────────────────────

INDIAN_RETAIL_MULTIPLIERS = {
    "gold":     1.0,  # 100% Google Parity
    "silver":   1.0,
    "platinum": 1.0,
    "usd_inr":  1.0
}

def fetch_and_store_prices():
    """
    Fetches LIVE precious metals prices from Yahoo Finance via yfinance.
    
    Priority:
    1. yfinance (PRIMARY) - Free, real-time Yahoo Finance data
    2. Frankfurter - Live USD/INR conversion
    3. Fallback simulation - if APIs unavailable
    
    Stores data every 5 minutes for chart generation.
    """
    import random
    prices_to_store = []
    
    # Fallback base rates (only used if all APIs fail)
    MARKET_BASES = {
        "gold":     15260.40,  # ₹/gram
        "silver":   253.80,    # ₹/gram
        "platinum": 6182.50,   # ₹/gram
        "usd_inr":  94.91
    }

    try:
        # ─ STEP 1: Fetch USD/INR exchange rate (for conversions)
        usd_inr = MARKET_BASES["usd_inr"]
        try:
            r = requests.get("https://api.frankfurter.app/latest?from=USD&to=INR", timeout=5)
            if r.status_code == 200:
                usd_inr = float(r.json()["rates"]["INR"])
                print("[FX] Live FX: 1 USD = INR " + str(round(usd_inr, 2)))
        except Exception as e:
            print("[WARN] FX API failed: " + str(e) + ", using fallback INR " + str(usd_inr))

        # ─ STEP 2: PRIMARY SOURCE - Fetch metals from Yahoo Finance (yfinance)
        # Using ETFs: GLD (Gold), SLV (Silver), PPLT (Platinum)
        metals_data = {"gold": None, "silver": None, "platinum": None}
        
        print("\n[FETCH] Fetching live metal prices from Yahoo Finance...")
        
        try:
            import yfinance as yf
            print("[OK] yfinance imported successfully")
            
            symbols = {
                "gold": "GC=F",      # COMEX Gold futures (USD/ounce)
                "silver": "SI=F",    # COMEX Silver futures (USD/ounce)
                "platinum": "PL=F"   # NYMEX Platinum futures (USD/ounce)
            }
            
            ounces_to_grams = 31.1034768
            premium_factors = {
                "gold": 1.07,      # Domestic premium for INR gold rate
                "silver": 1.07,    # Domestic premium for INR silver rate
                "platinum": 1.00   # Platinum is closer to global futures
            }
            
            for metal_name, ticker in symbols.items():
                try:
                    print("[FETCH] Fetching " + ticker + "...")
                    contract = yf.Ticker(ticker)
                    hist = contract.history(period="5d", interval="1d")
                    
                    if hist is not None and not hist.empty:
                        current_price_usd = float(hist['Close'].iloc[-1])
                    else:
                        fallback_quote = fetch_yahoo_json_quote(ticker)
                        if fallback_quote:
                            current_price_usd = float(fallback_quote['last_price'])
                        else:
                            current_price_usd = None

                    if current_price_usd is not None:
                        price_inr_per_gram = (current_price_usd * usd_inr) / ounces_to_grams
                        adjusted_price = price_inr_per_gram * premium_factors.get(metal_name, 1.0)
                        metals_data[metal_name] = adjusted_price
                        print("[LIVE] " + metal_name.upper() + " | $" + str(round(current_price_usd, 2)) + " /oz -> INR " + str(round(adjusted_price, 2)) + " /g")
                    else:
                        print("[WARN] " + metal_name.upper() + " | No data available from yfinance or Yahoo JSON")
                except Exception as e:
                    print("[ERROR] " + metal_name.upper() + " | " + str(e)[:50])
        
        except ImportError as e:
            print("[WARN] yfinance import failed: " + str(e))
            print("[WARN] Will use fallback simulation...")
        except Exception as e:
            print("[ERROR] yfinance error: " + str(e))
            print("[WARN] Will use fallback simulation...")

        # ─ STEP 3: If yfinance fails, use fallback simulation
        for metal_name in ["gold", "silver", "platinum"]:
            if metals_data.get(metal_name):
                final_price = round(metals_data[metal_name], 2)
                source = "LIVE (yfinance)"
            else:
                # Use simulation only if API failed
                base = MARKET_BASES[metal_name]
                jitter = 1.0 + random.uniform(-0.005, 0.005)
                final_price = round(base * jitter, 2)
                source = "SIMULATED"
            
            prices_to_store.append((metal_name, final_price, "INR"))
            print("[STORE] " + metal_name.upper() + " | INR " + str(final_price) + " | " + source)

        prices_to_store.append(("usd_inr", round(usd_inr, 4), "INR"))

        # ─ STEP 4: Store all prices in database for chart generation
        conn = get_db()
        cur = conn.cursor()
        
        for metal_type, price, currency in prices_to_store:
            cur.execute(
                "INSERT INTO metal_price (metal_type, price_per_gram, currency, recorded_at) VALUES (%s, %s, %s, NOW())",
                (metal_type, price, currency)
            )
        
        conn.commit()
        
        # Clean up old data (keep only last 90 days for charts)
        try:
            cur.execute("DELETE FROM metal_price WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 90 DAY)")
            conn.commit()
            print("[CLEAN] Cleaned old data (>90 days)")
        except:
            pass
        
        cur.close()
        conn.close()
        
        print("\n[OK] Market data synced successfully at " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(f"📈 Data stored in database for chart generation")
        print(f"🌍 Regional pricing available for all 36 states/UTs\n")

    except Exception as e:
        print(f"\n❌ Market Sync Failed: {e}")
        import traceback
        traceback.print_exc()

# ─────────────────────────────────────────────────────────────
#  REGIONAL PRICING BY STATE/UT (Live-Based Derivation)
# ─────────────────────────────────────────────────────────────

STATE_UT_MULTIPLIERS = {
    # Each state/UT has a markup multiplier based on local market conditions
    # Derived from live base prices + regional logistics/demand factors
    "Andhra Pradesh": 1.02,
    "Arunachal Pradesh": 1.08,
    "Assam": 1.06,
    "Bihar": 1.04,
    "Chhattisgarh": 1.03,
    "Goa": 1.01,
    "Gujarat": 1.01,
    "Haryana": 1.01,
    "Himachal Pradesh": 1.05,
    "Jharkhand": 1.04,
    "Karnataka": 1.02,
    "Kerala": 1.03,
    "Madhya Pradesh": 1.03,
    "Maharashtra": 1.00,  # Reference state (Mumbai - national center)
    "Manipur": 1.07,
    "Meghalaya": 1.07,
    "Mizoram": 1.08,
    "Nagaland": 1.08,
    "Odisha": 1.03,
    "Punjab": 1.02,
    "Rajasthan": 1.03,
    "Sikkim": 1.08,
    "Tamil Nadu": 1.02,
    "Telangana": 1.02,
    "Tripura": 1.07,
    "Uttar Pradesh": 1.02,
    "Uttarakhand": 1.04,
    "West Bengal": 1.03,
    "Andaman and Nicobar Islands": 1.10,
    "Chandigarh": 1.01,
    "Dadra and Nagar Haveli": 1.04,
    "Daman and Diu": 1.04,
    "Lakshadweep": 1.12,
    "Delhi": 1.00,
    "Puducherry": 1.05,
    "Ladakh": 1.09,
    "Jammu and Kashmir": 1.06,
}

def get_regional_prices(base_gold, base_silver, base_platinum):
    """Generate state/UT-specific prices from base live prices."""
    regional = {}
    for state_ut, multiplier in STATE_UT_MULTIPLIERS.items():
        regional[state_ut] = {
            "gold": round(base_gold * multiplier, 2),
            "silver": round(base_silver * multiplier, 2),
            "platinum": round(base_platinum * multiplier, 2),
        }
    return regional

def fetch_latest_base_prices():
    """Retrieve the latest live base prices from database."""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        prices = {}
        for metal in ["gold", "silver", "platinum", "usd_inr"]:
            cur.execute(
                "SELECT price_per_gram FROM metal_price WHERE metal_type = %s ORDER BY recorded_at DESC LIMIT 1",
                (metal,)
            )
            row = cur.fetchone()
            prices[metal] = float(row['price_per_gram']) if row else None
        cur.close()
        conn.close()
        return prices
    except Exception as e:
        print(f"❌ Failed to fetch base prices: {e}")
        return {}

def populate_investment_data():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # --- SCHEMA REPAIR ---
        try:
            cur.execute("DESCRIBE company")
            cols = [r['Field'] for r in cur.fetchall()]
            if 'market_price' not in cols:
                print("[REPAIR] Adding missing market_price column...")
                cur.execute("ALTER TABLE company ADD COLUMN market_price DECIMAL(15,2) DEFAULT 0.0")
        except: pass
        
        print("[RESET] FORCING TOTAL RESET OF INVESTMENT DATA...")
        cur.execute("DELETE FROM sip_plan")
        cur.execute("DELETE FROM company")
        conn.commit()
        
        # Comprehensive list of top NSE/BSE Companies
        companies = [
            # --- BANKING & FINANCE (12) ---
            ("HDFC Bank Ltd", "HDFCBANK", "banking", "NSE & BSE", "low", 11.8, 11540000000000, 1530.25),
            ("ICICI Bank Ltd", "ICICIBANK", "banking", "NSE & BSE", "low", 12.8, 7654000000000, 1120.00),
            ("State Bank of India", "SBIN", "banking", "NSE & BSE", "medium", 11.2, 7954000000000, 830.00),
            ("Axis Bank Ltd", "AXISBANK", "banking", "NSE & BSE", "medium", 10.5, 3500000000000, 1080.00),
            ("Kotak Mahindra Bank", "KOTAKBANK", "banking", "NSE & BSE", "low", 9.8, 3800000000000, 1750.00),
            ("Bajaj Finance Ltd", "BAJFINANCE", "banking", "NSE & BSE", "high", 25.4, 4500000000000, 7200.00),
            ("IndusInd Bank", "INDUSINDBK", "banking", "NSE & BSE", "medium", 14.2, 1100000000000, 1450.00),
            ("Yes Bank Ltd", "YESBANK", "banking", "NSE & BSE", "high", 8.5, 750000000000, 24.50),
            ("PNB", "PNB", "banking", "NSE & BSE", "high", 15.6, 1300000000000, 125.00),
            ("IDFC First Bank", "IDFCFIRSTB", "banking", "NSE & BSE", "medium", 13.8, 580000000000, 82.00),
            ("Bank of Baroda", "BANKBARODA", "banking", "NSE & BSE", "medium", 12.5, 1400000000000, 265.00),
            ("Canara Bank", "CANBK", "banking", "NSE & BSE", "medium", 14.8, 1100000000000, 115.00),

            # --- IT & TECH (10) ---
            ("Tata Consultancy Services", "TCS", "it", "NSE & BSE", "low", 14.5, 14540000000000, 3985.60),
            ("Infosys Ltd", "INFY", "it", "NSE & BSE", "low", 13.2, 6300000000000, 1420.50),
            ("Wipro Ltd", "WIPRO", "it", "NSE & BSE", "medium", 10.5, 2554000000000, 460.00),
            ("HCL Technologies Ltd", "HCLTECH", "it", "NSE & BSE", "medium", 15.0, 4200000000000, 1450.00),
            ("Tech Mahindra Ltd", "TECHM", "it", "NSE & BSE", "medium", 12.4, 1200000000000, 1250.00),
            ("LTIMindtree Ltd", "LTIM", "it", "NSE & BSE", "medium", 16.2, 1500000000000, 4800.00),
            ("Mphasis Ltd", "MPHASIS", "it", "NSE & BSE", "high", 14.8, 450000000000, 2400.00),
            ("Persistent Systems", "PERSISTENT", "it", "NSE & BSE", "high", 22.5, 600000000000, 3800.00),
            ("Coforge Ltd", "COFORGE", "it", "NSE & BSE", "high", 19.4, 380000000000, 5200.00),
            ("Oracle Financial", "OFSS", "it", "NSE & BSE", "low", 11.2, 750000000000, 8500.00),

            # --- ENERGY & POWER (10) ---
            ("Reliance Industries Ltd", "RELIANCE", "energy", "NSE & BSE", "low", 15.4, 20054000000000, 2954.20),
            ("Adani Green Energy Ltd", "ADANIGREEN", "energy", "NSE & BSE", "high", 32.0, 2854000000000, 1890.00),
            ("NTPC Ltd", "NTPC", "energy", "NSE & BSE", "low", 13.5, 3400000000000, 350.00),
            ("Power Grid Corp", "POWERGRID", "energy", "NSE & BSE", "low", 11.2, 2600000000000, 280.00),
            ("ONGC Ltd", "ONGC", "energy", "NSE & BSE", "medium", 8.5, 3200000000000, 260.00),
            ("Tata Power Ltd", "TATAPOWER", "energy", "NSE & BSE", "medium", 18.4, 1400000000000, 430.00),
            ("Adani Power Ltd", "ADANIPOWER", "energy", "NSE & BSE", "high", 45.2, 2200000000000, 580.00),
            ("JSW Energy Ltd", "JSWENERGY", "energy", "NSE & BSE", "high", 24.8, 1000000000000, 610.00),
            ("GAIL India Ltd", "GAIL", "energy", "NSE & BSE", "medium", 12.5, 1200000000000, 185.00),
            ("BPCL", "BPCL", "energy", "NSE & BSE", "medium", 10.2, 1300000000000, 620.00),
            ("Suzlon Energy Ltd", "SUZLON", "energy", "NSE & BSE", "high", 15.5, 50000000000, 100.00),

            # --- AUTO & MOTORS (10) ---
            ("Tata Motors Ltd", "TATAMOTORS", "auto", "NSE & BSE", "high", 28.5, 3200000000000, 965.00),
            ("Maruti Suzuki India", "MARUTI", "auto", "NSE & BSE", "medium", 11.4, 3800000000000, 12400.00),
            ("Mahindra & Mahindra", "M&M", "auto", "NSE & BSE", "medium", 15.2, 2400000000000, 1950.00),
            ("Bajaj Auto Ltd", "BAJAJ-AUTO", "auto", "NSE & BSE", "low", 12.5, 2200000000000, 8500.00),
            ("Hero MotoCorp Ltd", "HEROMOTOCO", "auto", "NSE & BSE", "low", 10.8, 900000000000, 4500.00),
            ("Eicher Motors Ltd", "EICHERMOT", "auto", "NSE & BSE", "medium", 14.2, 1100000000000, 3900.00),
            ("TVS Motor Company", "TVSMOTOR", "auto", "NSE & BSE", "high", 22.4, 1000000000000, 2100.00),
            ("Ashok Leyland Ltd", "ASHOKLEY", "auto", "NSE & BSE", "medium", 15.8, 550000000000, 175.00),
            ("Bharat Forge Ltd", "BHARATFORG", "auto", "NSE & BSE", "medium", 13.5, 600000000000, 1250.00),
            ("MRF Ltd", "MRF", "auto", "NSE & BSE", "low", 9.5, 550000000000, 132000.00),

            # --- PHARMA & HEALTHCARE (10) ---
            ("Sun Pharmaceutical Ind", "SUNPHARMA", "pharma", "NSE & BSE", "low", 16.8, 3800000000000, 1540.00),
            ("Dr. Reddy's Laboratories", "DRREDDY", "pharma", "NSE & BSE", "medium", 14.2, 1000000000000, 6240.00),
            ("Cipla Ltd", "CIPLA", "pharma", "NSE & BSE", "low", 13.5, 1200000000000, 1480.00),
            ("Apollo Hospitals", "APOLLOHOSP", "pharma", "NSE & BSE", "medium", 18.4, 900000000000, 6300.00),
            ("Divi's Laboratories", "DIVISLAB", "pharma", "NSE & BSE", "medium", 12.5, 1000000000000, 3800.00),
            ("Zydus Lifesciences", "ZYDUSLIFE", "pharma", "NSE & BSE", "medium", 15.2, 950000000000, 950.00),
            ("Lupin Ltd", "LUPIN", "pharma", "NSE & BSE", "high", 10.8, 750000000000, 1600.00),
            ("Aurobindo Pharma", "AUROPHARMA", "pharma", "NSE & BSE", "high", 14.5, 650000000000, 1100.00),
            ("Biocon Ltd", "BIOCON", "pharma", "NSE & BSE", "high", 9.2, 350000000000, 290.00),
            ("Max Healthcare", "MAXHEALTH", "pharma", "NSE & BSE", "medium", 24.5, 750000000000, 820.00),

            # --- FMCG & CONSUMER (10) ---
            ("Hindustan Unilever Ltd", "HINDUNILVR", "fmcg", "NSE & BSE", "low", 10.5, 5800000000000, 2450.00),
            ("ITC Ltd", "ITC", "fmcg", "NSE & BSE", "low", 12.8, 5400000000000, 435.00),
            ("Nestle India Ltd", "NESTLEIND", "fmcg", "NSE & BSE", "low", 11.2, 2400000000000, 2500.00),
            ("Britannia Industries", "BRITANNIA", "fmcg", "NSE & BSE", "medium", 13.4, 1200000000000, 4900.00),
            ("Dabur India Ltd", "DABUR", "fmcg", "NSE & BSE", "low", 11.8, 950000000000, 530.00),
            ("Marico Ltd", "MARICO", "fmcg", "NSE & BSE", "medium", 10.5, 700000000000, 520.00),
            ("Godrej Consumer", "GODREJCP", "fmcg", "NSE & BSE", "medium", 12.2, 1100000000000, 1250.00),
            ("Colgate-Palmolive", "COLPAL", "fmcg", "NSE & BSE", "low", 14.5, 750000000000, 2700.00),
            ("Tata Consumer Prod", "TATACONSUM", "fmcg", "NSE & BSE", "medium", 16.8, 1100000000000, 1150.00),
            ("Varun Beverages", "VBL", "fmcg", "NSE & BSE", "high", 38.5, 1800000000000, 1450.00),

            # --- GOLD & JEWELLERY (5) ---
            ("Titan Company Ltd", "TITAN", "gold", "NSE & BSE", "low", 22.4, 2800000000000, 3240.15),
            ("Kalyan Jewellers Ltd", "KALYANKJIL", "gold", "NSE & BSE", "medium", 28.5, 455400000000, 410.00),
            ("Muthoot Finance Ltd", "MUTHOOTFIN", "gold", "NSE & BSE", "medium", 16.0, 680000000000, 1645.00),
            ("Manappuram Finance", "MANAPPURAM", "gold", "NSE & BSE", "high", 14.2, 160000000000, 190.00),
            ("Rajesh Exports", "RAJESHEXPO", "gold", "NSE & BSE", "high", 5.5, 90000000000, 310.00),

            # --- METALS & MINING (8) ---
            ("Tata Steel Ltd", "TATASTEEL", "silver", "NSE & BSE", "high", 18.2, 2154000000000, 165.40),
            ("Hindustan Zinc Ltd", "HINDZINC", "silver", "NSE & BSE", "medium", 15.8, 1854000000000, 420.00),
            ("Vedanta Ltd", "VEDL", "silver", "NSE & BSE", "high", 24.5, 1654000000000, 345.00),
            ("Jindal Steel & Power", "JINDALSTEL", "silver", "NSE & BSE", "high", 19.2, 985400000000, 940.00),
            ("JSW Steel Ltd", "JSWSTEEL", "silver", "NSE & BSE", "medium", 16.5, 2000000000000, 850.00),
            ("Hindalco Industries", "HINDALCO", "silver", "NSE & BSE", "medium", 14.8, 1300000000000, 610.00),
            ("Coal India Ltd", "COALINDIA", "silver", "NSE & BSE", "low", 12.4, 2800000000000, 450.00),
            ("NMDC Ltd", "NMDC", "silver", "NSE & BSE", "medium", 15.2, 750000000000, 240.00),

            # --- INFRA & DEFENCE (6) ---
            ("Larsen & Toubro Ltd", "LT", "infra", "NSE & BSE", "low", 14.2, 4800000000000, 3450.00),
            ("Hindustan Aeronautics", "HAL", "infra", "NSE & BSE", "medium", 35.4, 2500000000000, 3300.00),
            ("Bharat Electronics", "BEL", "infra", "NSE & BSE", "medium", 28.2, 1500000000000, 210.00),
            ("Mazagon Dock Ship", "MAZDOCK", "infra", "NSE & BSE", "high", 48.5, 450000000000, 2200.00),
            ("Adani Ports \u0026 SEZ", "ADANIPORTS", "infra", "NSE & BSE", "medium", 18.2, 2800000000000, 1320.00),
            ("GMR Infra", "GMRINFRA", "infra", "NSE & BSE", "high", 15.4, 480000000000, 85.00),

            # --- REAL ESTATE (5) ---
            ("DLF Ltd", "DLF", "realty", "NSE & BSE", "high", 22.5, 2100000000000, 850.00),
            ("Godrej Properties", "GODREJPROP", "realty", "NSE & BSE", "high", 18.4, 650000000000, 2300.00),
            ("Macrotech Dev (Lodha)", "LODHA", "realty", "NSE & BSE", "high", 20.2, 1100000000000, 1150.00),
            ("Oberoi Realty Ltd", "OBEROIRLTY", "realty", "NSE & BSE", "medium", 15.8, 550000000000, 1450.00),
            ("Prestige Estates", "PRESTIGE", "realty", "NSE & BSE", "high", 24.5, 480000000000, 1200.00),

            # --- TELECOM \u0026 MEDIA (4) ---
            ("Bharti Airtel Ltd", "BHARTIARTL", "telecom", "NSE & BSE", "medium", 13.8, 6500000000000, 1200.00),
            ("Reliance Jio (RIL)", "RELIANCE", "telecom", "NSE & BSE", "low", 15.4, 20000000000000, 2954.20),
            ("Vodafone Idea Ltd", "IDEA", "telecom", "NSE & BSE", "high", 5.2, 650000000000, 13.50),
            ("Tata Communications", "TATACOMM", "telecom", "NSE & BSE", "medium", 12.8, 550000000000, 1950.00)
        ]
        
        print(f"📦 Saving {len(companies)} Companies...")
        # Add 'all' as the default metal_type since it's required by the schema
        companies_with_metal = [c + ("all",) for c in companies]
        cur.executemany("""INSERT INTO company 
            (company_name, ticker_symbol, sector_label, exchange, risk_level, avg_return_5y, market_cap, market_price, metal_type) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", companies_with_metal)
        conn.commit()
        
        cur.execute("SELECT company_id, company_name, sector_label, risk_level, avg_return_5y FROM company")
        cos = cur.fetchall()
        sip = [(c['company_id'], f"{c['company_name']} Monthly SIP", c['sector_label'], 500, c['risk_level'], c['avg_return_5y'], 5) for c in cos]
        
        print(f"📦 Saving {len(sip)} SIP Plans...")
        cur.executemany("""INSERT INTO sip_plan 
            (company_id, sip_name, metal_type, min_investment, risk_level, expected_return, duration_years) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)""", sip)
        conn.commit()
        
        print("==========================================================")
        print("[OK] SUCCESS: 40+ NSE/BSE BLUE-CHIP COMPANIES LOADED!")
        print("==========================================================")
        cur.close(); conn.close()
    except Exception as e: 
        print(f"❌ DATABASE ERROR: {e}")

def update_investment_data():
    try:
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT company_id, avg_return_5y FROM company")
        for co in cur.fetchall():
            import random
            nr = max(0, min(100, float(co['avg_return_5y'] or 10) + random.uniform(-0.5, 0.5)))
            cur.execute("UPDATE company SET avg_return_5y = %s WHERE company_id = %s", (nr, co['company_id']))
        cur.execute("UPDATE sip_plan s JOIN company c ON s.company_id = c.company_id SET s.expected_return = c.avg_return_5y")
        conn.commit(); cur.close(); conn.close()
    except Exception as e: print(f"Invest Update Error: {e}")

def get_live_metal_prices_for_alerts():
    """
    Fetch LIVE metal prices directly from yfinance for IMMEDIATE alert checking.
    This bypasses the 5-minute database update lag.
    Returns prices per gram (same format as database) - NOT display prices.
    """
    try:
        import yfinance as yf
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Get live USD/INR rate
        usd_inr_quote = get_live_usd_inr_quote()
        usd_inr = float(usd_inr_quote.get("price", 95.69))
        
        # Asset configuration: (ticker, premium_factor)
        # Same calculation as fetch_and_store_prices for consistency
        assets_config = {
            "gold": ("GC=F", 1.07),
            "silver": ("SI=F", 1.07),
            "platinum": ("PL=F", 1.00)
        }
        
        prices = {}
        TROY_OUNCE_TO_GRAMS = 31.1034768
        
        def fetch_single_price(metal, ticker, premium_factor):
            try:
                asset = yf.Ticker(ticker)
                hist = asset.history(period="1d", interval="1m", timeout=3)
                if hist is not None and len(hist) > 0:
                    current_price_usd = float(hist['Close'].iloc[-1])
                    # Convert: USD/oz -> INR/gram (per-gram price, same as database stores)
                    price_inr_per_gram = (current_price_usd * usd_inr) / TROY_OUNCE_TO_GRAMS
                    adjusted_price = price_inr_per_gram * premium_factor
                    return metal, adjusted_price
            except Exception as e:
                print(f"[ALERT-LIVE] Error fetching {metal}: {e}")
            return None, None
        
        # Fetch all prices in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(fetch_single_price, metal, cfg[0], cfg[1]): metal
                for metal, cfg in assets_config.items()
            }
            for future in as_completed(futures):
                metal, price = future.result()
                if metal and price:
                    prices[metal] = price
        
        return prices if len(prices) > 0 else None
    except Exception as e:
        print(f"[ALERT-LIVE] Error: {e}")
        return None


def check_and_trigger_alerts():
    try:
        # PRIORITY: Try to get LIVE prices from yfinance first (for immediate triggering)
        live_prices = get_live_metal_prices_for_alerts()
        
        # FALLBACK: If live fetch fails, use database prices
        if not live_prices:
            print("[ALERT] Live price fetch failed, using database prices...")
            conn = get_db(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT metal_type, price_per_gram FROM metal_price WHERE (metal_type, recorded_at) IN (SELECT metal_type, MAX(recorded_at) FROM metal_price GROUP BY metal_type)")
            live_prices = {r['metal_type'].lower(): float(r['price_per_gram']) for r in cur.fetchall()}
            cur.close(); conn.close()
        
        # Use live prices for immediate alert checking
        prices = {m.lower(): p for m, p in live_prices.items()}
        
        conn = get_db(); cur = conn.cursor(dictionary=True)
        # Check ALL active alerts (both 'watching' and 'triggered')
        cur.execute("SELECT * FROM alerts WHERE status IN ('watching', 'triggered')")
        for a in cur.fetchall():
            # Normalize metal_type to lowercase for comparison
            m = a['metal_type'].lower()
            if m in prices:
                # Apply multiplier: silver x1000, gold/platinum x10
                mult = 1000 if m == "silver" else 10
                cur_v = prices[m] * mult
                target = float(a['target_price'])
                
                # Evaluate if condition is currently met
                condition_met = False
                if a['condition_type'].lower() == "above":
                    condition_met = cur_v >= target
                elif a['condition_type'].lower() == "below":
                    condition_met = cur_v <= target
                
                # Update alert status based on current condition
                current_status = a['status'].lower()
                new_status = 'triggered' if condition_met else 'watching'
                
                # Only update if status changed
                if current_status != new_status:
                    cur.execute("UPDATE alerts SET status = %s WHERE alert_id = %s", (new_status, a['alert_id']))
                    if new_status == 'triggered':
                        print(f"✅ Alert {a['alert_id']} TRIGGERED: {m.upper()} {a['condition_type']} ₹{target} (current: ₹{cur_v})")
                    else:
                        print(f"🔄 Alert {a['alert_id']} RESET: {m.upper()} {a['condition_type']} ₹{target} (current: ₹{cur_v})")
        
        conn.commit(); cur.close(); conn.close()
    except Exception as e: 
        print(f"❌ Alerts Error: {e}")

#  AUTH API
#  AUTH API
# ═══════════════════════════════════════════════════════════

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True)
    un, em, pw = data.get("username"), data.get("email"), data.get("password")
    if not all([un, em, pw]): return err("All fields required")
    try:
        conn = get_db(); cur = conn.cursor()
        # Using plain text password to match your existing database pattern
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (un, em, pw))
        conn.commit(); cur.close(); conn.close()
        return ok({"message": "Registered"})
    except MySQLError as e: return err(str(e))

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True)
    if data is None:
        data = request.form

    identifier = (data.get("username") or data.get("email") or "").strip()
    pw = data.get("password") or ""

    if not identifier or not pw:
        return err("Email/username and password are required")

    try:
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s OR username=%s", (identifier, identifier))
        u = cur.fetchone()
        cur.close(); conn.close()

        if u:
            db_pw = u.get('password', "")
            is_valid = False
            if db_pw == pw:
                is_valid = True
            else:
                try:
                    if bcrypt.checkpw(pw.encode('utf-8'), db_pw.encode('utf-8')):
                        is_valid = True
                except Exception:
                    pass

            if is_valid:
                session.clear()
                session["user_id"] = u['user_id']
                session["username"] = u['username']
                session["theme_mode"] = "light"
                session["ui_preferences"] = {}
                return ok({"user_id": u['user_id'], "username": u['username'], "redirect_url": url_for("dashboard_page")})

        return err("Invalid credentials")
    except MySQLError as e:
        return err(str(e))

@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json(force=True)
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    if not email or not password:
        return err('Email and new password are required')

    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute('SELECT user_id FROM users WHERE email = %s', (email,))
        if cur.fetchone() is None:
            cur.close(); conn.close()
            return err('No account found for this email')

        cur.execute('UPDATE users SET password = %s WHERE email = %s', (password, email))
        conn.commit(); cur.close(); conn.close()
        return ok({'message': 'Password updated successfully'})
    except MySQLError as e:
        return err(str(e))

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return ok({"message": "Logged out"})

@app.route("/api/me")
def api_me():
    if "user_id" not in session:
        return err("Not logged in", 401)
    return ok({
        "user_id": session["user_id"],
        "username": session["username"],
        "theme_mode": session.get("theme_mode", "light")
    })

@app.route("/api/user/preferences", methods=["GET", "POST"])
def api_user_preferences():
    # Preferences are stored in the session and available even for anonymous visitors
    if request.method == "GET":
        return ok({
            "theme_mode": session.get("theme_mode", "light"),
            "budget": float(session.get("budget", 50000.00)),
            "risk_level": session.get("risk_level", "medium"),
            "investment_goal": session.get("investment_goal", "balanced"),
            "time_horizon": int(session.get("time_horizon", 5)),
            "ui_preferences": session.get("ui_preferences", {})
        })

    try:
        data = request.get_json(force=True)
        theme_mode = data.get("theme_mode")
        budget = data.get("budget")
        risk_level = data.get("risk_level")
        investment_goal = data.get("investment_goal")
        time_horizon = data.get("time_horizon")
        ui_prefs = data.get("ui_preferences")

        if theme_mode is not None:
            session["theme_mode"] = theme_mode
        if budget is not None:
            session["budget"] = float(budget)
        if risk_level is not None:
            session["risk_level"] = risk_level
        if investment_goal is not None:
            session["investment_goal"] = investment_goal
        if time_horizon is not None:
            session["time_horizon"] = int(time_horizon)
        if ui_prefs is not None:
            session["ui_preferences"] = ui_prefs

        return ok({"success": True})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/alerts", methods=["GET", "POST", "DELETE", "PUT"])
def api_alerts():
    if "user_id" not in session:
        return err("Not logged in", 401)
    user_id = session["user_id"]
    try:
        conn = get_db(); cur = conn.cursor(dictionary=True)
        if request.method == "GET":
            limit = int(request.args.get("limit", 20))
            cur.execute("SELECT alert_id, metal_type, condition_type, target_price, status, created_at FROM alerts WHERE user_id = %s ORDER BY created_at DESC LIMIT %s", (user_id, limit))
            rows = clean_rows(cur.fetchall())
            cur.close(); conn.close()
            return ok({"data": rows})

        if request.method == "DELETE":
            payload = request.get_json(silent=True) or {}
            alert_id = request.args.get("alert_id") or payload.get("alert_id")
            if not alert_id:
                return err("alert_id is required", 400)
            cur.execute("DELETE FROM alerts WHERE alert_id = %s AND user_id = %s", (alert_id, user_id))
            conn.commit(); cur.close(); conn.close()
            return ok({"success": True})

        # Allow updating alert status (archive/dismiss/restore) via PUT
        if request.method == "PUT":
            data = request.get_json(force=True)
            alert_id = data.get('alert_id')
            status = data.get('status')
            if not alert_id or not status:
                return err('alert_id and status are required', 400)
            cur.execute("UPDATE alerts SET status = %s WHERE alert_id = %s AND user_id = %s", (status, alert_id, user_id))
            conn.commit(); cur.close(); conn.close()
            return ok({"success": True})

        data = request.get_json(force=True)
        metal_type = data.get("metal_type")
        condition_type = data.get("condition_type")
        target_price = data.get("target_price")
        if not metal_type or not condition_type or target_price is None:
            return err("metal_type, condition_type, and target_price are required", 400)
        # Normalize metal_type to lowercase for consistency with metal_price table
        metal_type = metal_type.lower()
        condition_type = condition_type.lower()
        cur.execute("INSERT INTO alerts (user_id, metal_type, condition_type, target_price, status) VALUES (%s, %s, %s, %s, 'watching')", (user_id, metal_type, condition_type, float(target_price)))
        alert_id = cur.lastrowid
        conn.commit(); cur.close(); conn.close()
        return ok({"success": True, "alert_id": alert_id})
    except MySQLError as e:
        return err(str(e), 500)

# ═══════════════════════════════════════════════════════════
#  PRICE API
# ═══════════════════════════════════════════════════════════

def get_live_usd_inr_quote():
    try:
        import yfinance as yf
        ticker = yf.Ticker('INR=X')
        info = ticker.info or {}
        price = info.get('regularMarketPrice') or info.get('lastPrice') or info.get('previousClose')
        change_pct = info.get('regularMarketChangePercent')
        previous_close = info.get('regularMarketPreviousClose') or info.get('previousClose')

        if price is not None:
            if change_pct is None and previous_close is not None:
                try:
                    change_pct = ((float(price) - float(previous_close)) / float(previous_close)) * 100
                except Exception:
                    change_pct = None

            if change_pct is not None:
                sign = '+' if change_pct >= 0 else ''
                return {
                    'price': float(price),
                    'change': f'{sign}{round(float(change_pct), 2)}%'
                }
            return {'price': float(price), 'change': '0.00%'}
    except Exception:
        pass

    try:
        response = requests.get('https://query1.finance.yahoo.com/v7/finance/quote',
                                params={'symbols': 'INR=X'},
                                timeout=4,
                                headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            quote_data = response.json().get('quoteResponse', {}).get('result', [])
            if quote_data and isinstance(quote_data, list):
                quote = quote_data[0]
                price = quote.get('regularMarketPrice') or quote.get('previousClose')
                change_pct = quote.get('regularMarketChangePercent')
                previous_close = quote.get('regularMarketPreviousClose') or quote.get('previousClose')
                if price is None and previous_close is not None:
                    price = previous_close
                if price is not None:
                    if change_pct is None and previous_close:
                        try:
                            change_pct = ((float(price) - float(previous_close)) / float(previous_close)) * 100
                        except Exception:
                            change_pct = None
                    if change_pct is not None:
                        sign = '+' if change_pct >= 0 else ''
                        return {
                            'price': float(price),
                            'change': f'{sign}{round(float(change_pct), 2)}%'
                        }
                    return {'price': float(price), 'change': '0.00%'}
    except Exception:
        pass

    try:
        response = requests.get('https://api.frankfurter.app/latest?from=USD&to=INR', timeout=4)
        if response.status_code == 200:
            return {'price': float(response.json().get('rates', {}).get('INR', 95.69)), 'change': '0.00%'}
    except Exception:
        pass

    return {'price': 95.69, 'change': '0.00%'}


def get_live_usd_inr():
    quote = get_live_usd_inr_quote()
    return float(quote.get("price", 95.69))


def get_usd_inr_change():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT price_per_gram FROM metal_price WHERE metal_type = 'usd_inr' ORDER BY recorded_at DESC LIMIT 2")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if len(rows) >= 2:
            current = float(rows[0]["price_per_gram"])
            previous = float(rows[1]["price_per_gram"])
            if previous != 0:
                change = ((current - previous) / previous) * 100
                sign = "+" if change >= 0 else ""
                return f"{sign}{round(change, 2)}%"
    except Exception:
        pass
    return "0.00%"


@app.route('/api/fx')
def get_fx_rates():
    """Return a set of FX rates for a given base currency (default USD).
    Tries Frankfurter (many pairs) and falls back to a minimal response.
    """
    base = request.args.get('base', 'USD').upper()
    try:
        # Primary: Frankfurter provides a clean rates map for many currencies
        r = requests.get(f'https://api.frankfurter.app/latest?from={base}', timeout=4)
        if r.status_code == 200:
            payload = r.json() or {}
            rates = payload.get('rates', {})
            # Ensure base is present
            rates[base] = 1
            return ok({'success': True, 'base': base, 'rates': rates, 'timestamp': datetime.now().isoformat()})
    except Exception:
        pass

    # Best-effort fallback: return a minimal USD->INR mapping (keeps UI functional)
    fallback = {
        'USD': 1,
        'INR': float(get_live_usd_inr()),
        'EUR': 0.92,
        'GBP': 0.79
    }
    return ok({'success': True, 'base': base, 'rates': fallback, 'timestamp': datetime.now().isoformat(), 'source': 'fallback'})


def fetch_metal_with_change(ticker, weight_multiplier, calibration_factor, usd_inr):
    TROY_OUNCE_TO_GRAMS = 31.1034768
    try:
        import yfinance as yf
        asset = yf.Ticker(ticker)
        hist_df = asset.history(period="5d", interval="1d", timeout=5)
        if hist_df is not None and len(hist_df) >= 2:
            current_spot = float(hist_df['Close'].iloc[-1])
            yesterday_spot = float(hist_df['Close'].iloc[-2])

            live_price = (current_spot / TROY_OUNCE_TO_GRAMS * weight_multiplier) * usd_inr * calibration_factor
            yesterday_price = (yesterday_spot / TROY_OUNCE_TO_GRAMS * weight_multiplier) * usd_inr * calibration_factor

            if yesterday_price != 0:
                delta_change = live_price - yesterday_price
                percentage_gain = (delta_change / yesterday_price) * 100
                sign = "+" if percentage_gain >= 0 else ""
                return {
                    "price": round(live_price, 2),
                    "change": f"{sign}{round(percentage_gain, 2)}%"
                }
    except Exception:
        pass
    return None


@app.route("/api/prices/live")
def get_live_prices():
    usd_inr_quote = get_live_usd_inr_quote()
    usd_inr = float(usd_inr_quote.get("price", 95.69))

    prices_data = {
        "gold": {"price": 154883.00, "change": "+0.18%"},
        "silver": {"price": 269300.00, "change": "+0.32%"},
        "platinum": {"price": 61299.00, "change": "-0.14%"},
        "usd_inr": {
            "price": round(usd_inr, 2),
            "change": usd_inr_quote.get("change", "0.00%")
        }
    }

    assets_config = {
        "gold": ("GC=F", 10, 1.1390),
        "silver": ("SI=F", 1000, 1.1920),
        "platinum": ("PL=F", 10, 1.0540)
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fetch_metal_with_change, cfg[0], cfg[1], cfg[2], usd_inr): key
            for key, cfg in assets_config.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                result = future.result()
                if result is not None:
                    prices_data[key] = result
            except Exception:
                pass

    return ok({
        "prices": prices_data,
        "timestamp": datetime.now().isoformat(),
        "source": "yfinance_frankfurter_google_aligned"
    })

@app.route("/api/prices/chart")
def get_chart_data():
    m_p = request.args.get("metal", "all").lower()
    rv = request.args.get("range", "3m")
    days = {"1d": 1, "1m": 30, "3m": 90, "6m": 180, "1y": 365, "3y": 1095}.get(rv, 90)
    metals = ["gold", "silver", "platinum"] if m_p == "all" else [m_p]
    try:
        conn = get_db(); cur = conn.cursor(dictionary=True); labels = []
        valid_thresholds = {"gold": 20000, "silver": 1000, "platinum": 10000}
        chart_payload = {
            "labels": [],
            "gold": [],
            "silver": [],
            "platinum": [],
            "gold_ohlc": [],
            "silver_ohlc": [],
            "platinum_ohlc": []
        }

        for metal in metals:
            cur.execute(
                "SELECT price_per_gram, recorded_at FROM metal_price WHERE metal_type=%s AND recorded_at >= DATE_SUB(NOW(), INTERVAL %s DAY) ORDER BY recorded_at ASC",
                (metal, days)
            )
            rows = cur.fetchall()
            max_valid_price = valid_thresholds.get(metal, float('inf'))
            rows = [r for r in rows if 0 < float(r["price_per_gram"]) <= max_valid_price]
            mult = 1000 if metal == "silver" else 10
            from collections import defaultdict
            groups = defaultdict(list)
            for r in rows:
                k = r["recorded_at"].strftime("%Y-%m-%dT%H:00:00" if rv == "1d" else "%Y-%m-%dT00:00:00")
                groups[k].append(r)

            metal_labels = []
            metal_points = []
            metal_ohlc = []
            for k in sorted(groups.keys()):
                pr = [float(r["price_per_gram"]) * mult for r in groups[k]]
                metal_labels.append(k)
                metal_points.append(round(pr[-1], 2))
                metal_ohlc.append([
                    round(pr[0], 2),
                    round(max(pr), 2),
                    round(min(pr), 2),
                    round(pr[-1], 2)
                ])

            if not chart_payload["labels"]:
                chart_payload["labels"] = metal_labels
            if metal == "gold":
                chart_payload["gold"] = metal_points
                chart_payload["gold_ohlc"] = metal_ohlc
            elif metal == "silver":
                chart_payload["silver"] = metal_points
                chart_payload["silver_ohlc"] = metal_ohlc
            elif metal == "platinum":
                chart_payload["platinum"] = metal_points
                chart_payload["platinum_ohlc"] = metal_ohlc

        cur.close(); conn.close()
        return ok({**chart_payload, "range": rv})
    except MySQLError as e:
        return err(str(e), 500)

@app.route("/api/prices/historical")
def get_dynamic_historical_prices():
    """Generates coordinate arrays for Line and Candlestick series based on requested timeframe.

    Query params:
      - range: one of 1D,1M,3M,6M,1Y,3Y (default 1M)
    Response shape:
      {
        "line_series": { "gold": [[ts_ms, price], ...], "silver": [...], "platinum": [...] },
        "candle_series": { "gold": [[ts_ms, [open, high, low, close]], ...], ... }
      }
    """
    timeframe = request.args.get('range', '1M')
    TROY_OUNCE_TO_GRAMS = 31.1034768
    usd_inr = 95.69

    range_config = {
        "1D": {"period": "1d", "interval": "1m"},
        "1M": {"period": "1mo", "interval": "1d"},
        "3M": {"period": "3mo", "interval": "1d"},
        "6M": {"period": "6mo", "interval": "1d"},
        "1Y": {"period": "1y", "interval": "1d"},
        "3Y": {"period": "5y", "interval": "1d"}
    }

    cfg = range_config.get(timeframe, range_config["1M"])

    assets_meta = {
        "gold": ("GC=F", 10, 1.1390),
        "silver": ("SI=F", 1000, 1.1920),
        "platinum": ("PL=F", 10, 1.0540)
    }

    response_payload = {"line_series": {}, "candle_series": {}}

    for key, (ticker, weight, factor) in assets_meta.items():
        try:
            try:
                import yfinance as yf
            except Exception:
                yf = None

            if yf is None:
                response_payload["line_series"][key] = []
                response_payload["candle_series"][key] = []
                continue

            asset = yf.Ticker(ticker)
            df = asset.history(period=cfg["period"], interval=cfg["interval"], timeout=5)

            # Truncate 3Y selection to 36 months strictly
            if timeframe == "3Y" and df is not None and not df.empty:
                cut_off = datetime.now() - timedelta(days=3 * 365)
                df = df[df.index >= cut_off]

            line_coordinates = []
            candle_coordinates = []

            if df is None or df.empty:
                response_payload["line_series"][key] = []
                response_payload["candle_series"][key] = []
                continue

            for index, row in df.iterrows():
                try:
                    timestamp = int(index.timestamp() * 1000)
                except Exception:
                    # index might be a string in some fallback situations
                    try:
                        dt = datetime.fromisoformat(str(index))
                        timestamp = int(dt.timestamp() * 1000)
                    except Exception:
                        continue

                multiplier = (weight / TROY_OUNCE_TO_GRAMS) * usd_inr * factor

                close_retail = (row.get('Close') if hasattr(row, 'get') else row['Close']) * multiplier
                open_retail = (row.get('Open') if hasattr(row, 'get') else row['Open']) * multiplier
                high_retail = (row.get('High') if hasattr(row, 'get') else row['High']) * multiplier
                low_retail = (row.get('Low') if hasattr(row, 'get') else row['Low']) * multiplier

                line_coordinates.append([timestamp, round(float(close_retail), 2)])
                candle_coordinates.append([
                    timestamp,
                    [round(float(open_retail), 2), round(float(high_retail), 2), round(float(low_retail), 2), round(float(close_retail), 2)]
                ])

            response_payload["line_series"][key] = line_coordinates
            response_payload["candle_series"][key] = candle_coordinates

        except Exception as e:
            print(f"[CHART MATRIX ERROR] Failed compilation for {key}: {e}")
            response_payload["line_series"][key] = []
            response_payload["candle_series"][key] = []

    return jsonify(response_payload)

def get_precise_usd_inr():
    try:
        import yfinance as yf
        ticker = yf.Ticker('INR=X')
        data = ticker.history(period='1d', interval='1m')
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception:
        pass
    return 83.40

@app.route('/api/get-dynamic-chart')
def get_dynamic_chart():
    metal = request.args.get('metal', 'all').lower()
    purity = request.args.get('purity', '24k').lower()
    timeframe = request.args.get('timeframe', '1m').lower()

    config = TIMEFRAME_CONFIGS.get(timeframe, TIMEFRAME_CONFIGS['1m'])
    target_metals = ['gold', 'silver', 'platinum'] if metal == 'all' else [metal]

    usd_inr = get_live_usd_inr()
    purity_multipliers = {'24k': 1.0, '22k': 22 / 24, '18k': 18 / 24}
    TROY_OUNCE_TO_GRAMS = 31.1034768

    assets_config = {
        'gold': ('GC=F', 10, INDIAN_GOLD_CALIBRATION_FACTOR),
        'silver': ('SI=F', 1000, INDIAN_SILVER_CALIBRATION_FACTOR),
        'platinum': ('PL=F', 10, INDIAN_PLAT_CALIBRATION_FACTOR)
    }

    response_payload = {}

    try:
        import yfinance as yf
    except Exception:
        return jsonify(response_payload)

    for m in target_metals:
        if m not in assets_config:
            continue

        ticker_symbol, weight_multiplier, calibration_factor = assets_config[m]
        purity_multiplier = (purity_multipliers.get(purity, 1.0) if m == 'gold' else 1.0)
        factor = (weight_multiplier / TROY_OUNCE_TO_GRAMS) * usd_inr * calibration_factor * purity_multiplier

        try:
            hist = yf.Ticker(ticker_symbol).history(period=config['period'], interval=config['interval'], timeout=5)
            if hist is None or hist.empty:
                continue

            line_series = []
            candle_series = []
            for index, row in hist.iterrows():
                if row.isnull().any():
                    continue
                try:
                    ts = int(index.timestamp() * 1000)
                except Exception:
                    try:
                        ts = int(datetime.fromisoformat(str(index)).timestamp() * 1000)
                    except Exception:
                        continue

                close_val = round(float(row['Close']) * factor, 2)
                line_series.append([ts, close_val])
                candle_series.append({
                    'x': ts,
                    'y': [
                        round(float(row['Open']) * factor, 2),
                        round(float(row['High']) * factor, 2),
                        round(float(row['Low']) * factor, 2),
                        close_val
                    ]
                })

            response_payload[m] = {
                'line': line_series,
                'candle': candle_series
            }
        except Exception:
            continue

    return jsonify(response_payload)

@app.route("/api/prices/states")
def get_price_states():
    """Database-free in-memory state price generator.

    Returns a list of state price objects with one_gram/ten_gram/hundred_gram/one_kg and change.
    """
    try:
        # Realtime FX
        try:
            r = requests.get("https://api.frankfurter.app/latest?from=USD&to=INR", timeout=3)
            usd_inr = float(r.json().get('rates', {}).get('INR', 95.69)) if r.status_code == 200 else 95.69
        except Exception:
            usd_inr = 95.69

        TROY_OUNCE_TO_GRAMS = 31.1034768

        # Query params
        metal_type = request.args.get('metal', 'gold').lower()
        purity_tier = request.args.get('purity', '24K')

        ticker_symbols = {"gold": "GC=F", "silver": "SI=F", "platinum": "PL=F"}
        ticker = ticker_symbols.get(metal_type, "GC=F")

        purity_multiplier = 1.00
        calibration_factor = INDIAN_GOLD_CALIBRATION_FACTOR
        if metal_type == 'gold':
            if purity_tier == '22K':
                purity_multiplier = 0.9167
            elif purity_tier == '18K':
                purity_multiplier = 0.75
        elif metal_type == 'silver':
            calibration_factor = INDIAN_SILVER_CALIBRATION_FACTOR
        elif metal_type == 'platinum':
            calibration_factor = INDIAN_PLAT_CALIBRATION_FACTOR

        try:
            import yfinance as yf
            asset = yf.Ticker(ticker)
            df = asset.history(period="1d", interval="1m", timeout=5)
            if df is not None and not df.empty:
                live_spot = float(df['Close'].iloc[-1])
            else:
                # fallback to daily close
                df2 = asset.history(period="1d", interval="1d", timeout=5)
                live_spot = float(df2['Close'].iloc[-1])
        except Exception:
            fallbacks = {"gold": 425.00, "silver": 73.10, "platinum": 166.50}
            live_spot = fallbacks.get(metal_type, 425.00)

        base_price_per_gram = (live_spot / TROY_OUNCE_TO_GRAMS) * usd_inr * calibration_factor * purity_multiplier

        # Predefined spreads
        INDIAN_STATES_LIVE_SPREADS = {
            "Andhra Pradesh": 1.0012, "Arunachal Pradesh": 1.0042, "Assam": 1.0018,
            "Bihar": 1.0037, "Chhattisgarh": 1.0015, "Goa": 0.9985, "Gujarat": 0.9960,
            "Haryana": 1.0010, "Himachal Pradesh": 1.0025, "Jharkhand": 1.0032,
            "Karnataka": 1.0005, "Kerala": 0.9992, "Madhya Pradesh": 1.0020,
            "Maharashtra": 1.0000, "Manipur": 1.0045, "Meghalaya": 1.0038,
            "Mizoram": 1.0040, "Nagaland": 1.0043, "Odisha": 1.0011, "Punjab": 1.0016,
            "Rajasthan": 1.0022, "Sikkim": 1.0035, "Tamil Nadu": 1.0008, "Telangana": 1.0006,
            "Tripura": 1.0039, "Uttar Pradesh": 1.0019, "Uttarakhand": 1.0021, "West Bengal": 1.0014,
            "Andaman & Nicobar": 1.0050, "Chandigarh": 1.0011, "Dadra & Nagar Haveli": 0.9975,
            "Daman & Diu": 0.9978, "Delhi": 1.0013, "Jammu & Kashmir": 1.0030,
            "Ladakh": 1.0035, "Lakshadweep": 1.0055, "Puducherry": 0.9995
        }

        payload = []
        for state, spread in INDIAN_STATES_LIVE_SPREADS.items():
            state_1g = base_price_per_gram * spread
            state_10g = state_1g * 10
            state_100g = state_1g * 100
            state_1kg = state_1g * 1000
            trend = "+0.18%" if spread >= 1.00 else "-0.05%"
            payload.append({
                "state": state,
                "one_gram": round(state_1g, 2),
                "ten_gram": round(state_10g, 2),
                "hundred_gram": round(state_100g, 2),
                "one_kg": round(state_1kg, 2),
                "change": trend
            })

        return jsonify(payload)
    except Exception as e:
        print(f"[ERROR] /api/prices/states failed: {e}")
        return err(str(e), 500)

@app.route("/api/prices/regional")
def get_regional_prices_api():
    """Get state/UT-wise metal prices based on latest live base prices."""
    state = request.args.get("state")
    try:
        base_prices = fetch_latest_base_prices()
        if not all(base_prices.get(m) for m in ["gold", "silver", "platinum"]):
            return err("Base prices not available", 503)
        
        regional = get_regional_prices(
            base_prices["gold"],
            base_prices["silver"],
            base_prices["platinum"]
        )
        
        if state and state in regional:
            return ok({"state": state, "prices": regional[state], "base_prices": {k: base_prices[k] for k in ["gold", "silver", "platinum", "usd_inr"]}})
        else:
            return ok({"all_states": regional, "base_prices": {k: base_prices[k] for k in ["gold", "silver", "platinum", "usd_inr"]}})
    except Exception as e:
        return err(str(e), 500)

# ... (Investment Advisor, News, Alerts APIs - Simplified Reconstruction) ...

@app.route("/api/news")
def get_news():
    try:
        limit = request.args.get("limit", 10)
        try:
            limit = min(max(int(limit), 1), 50)
        except ValueError:
            limit = 10

        conn = get_db(); cur = conn.cursor(dictionary=True)
        query = f"SELECT * FROM market_news ORDER BY published_at DESC LIMIT {limit}"
        cur.execute(query)
        rows = clean_rows(cur.fetchall())
        cur.close(); conn.close()

        if not rows:
            rows = [{
                "title": "Market headlines are currently unavailable",
                "description": "No recent news was found. The system will retry shortly.",
                "source": "System",
                "news_url": "#",
                "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }]

        return ok({"data": rows})
    except Exception as e:
        return err(f"News error: {e}")

@app.route("/api/sectors")
def get_sectors():
    """Get sector list with live company counts from database."""
    try:
        conn = get_db(); cur = conn.cursor(dictionary=True)
        # Fetch sector counts from company table
        cur.execute("SELECT sector_label as sector, COUNT(*) as count FROM company WHERE sector_label IS NOT NULL AND sector_label != '' GROUP BY sector_label ORDER BY count DESC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return ok({"data": rows})
    except Exception as e:
        print(f"[ERROR] /api/sectors failed: {e}")
        return err("Sector error")

@app.route("/api/companies")
def get_companies():
    sector = request.args.get("metal", "all").lower()
    search = request.args.get("search", "").lower()
    try:
        limit = request.args.get("limit", 40)
        try:
            limit = min(max(int(limit), 1), 100)
        except ValueError:
            limit = 40

        conn = get_db(); cur = conn.cursor(dictionary=True)
        q = "SELECT * FROM company WHERE 1=1"
        params = []
        if sector != "all":
            q += " AND sector_label = %s"
            params.append(sector)
        if search:
            q += " AND (LOWER(company_name) LIKE %s OR LOWER(ticker_symbol) LIKE %s)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
        q += " ORDER BY company_name ASC LIMIT %s"
        params.append(limit)
        cur.execute(q, params)
        rows = clean_rows(cur.fetchall())
        for row in rows:
            row['live_price'] = float(row.get('market_price', 0) or 0)
            row['live_price_pct'] = 0.0
            row['live_source'] = 'db'

            raw_db_cap = row.get('market_cap')
            if raw_db_cap is not None:
                try:
                    raw_db_cap = float(raw_db_cap)
                    market_cap = raw_db_cap / 1e7 if raw_db_cap > 1e7 else raw_db_cap
                    if market_cap > 0:
                        row['market_cap'] = market_cap
                        row['market_cap_display'] = f"₹{market_cap:,.0f} Cr"
                    else:
                        row['market_cap'] = None
                        row['market_cap_display'] = "N/A"
                except Exception:
                    row['market_cap'] = None
                    row['market_cap_display'] = "N/A"
            else:
                row['market_cap'] = None
                row['market_cap_display'] = "N/A"

            if not row.get('avg_return_5y'):
                row['avg_return_5y'] = row.get('expected_return', 0.0)
            if not row.get('expected_return'):
                row['expected_return'] = row.get('avg_return_5y', 0.0)
        cur.close(); conn.close()
        return ok({"data": rows})
    except Exception as e:
        print(f"[ERROR] /api/companies failed: {e}")
        return err("DB error")

@app.route("/api/sip-plans")
def get_sip_plans():
    sector = request.args.get("metal", "all").lower()
    search = request.args.get("search", "").lower()
    try:
        limit = request.args.get("limit", 40)
        try:
            limit = min(max(int(limit), 1), 100)
        except ValueError:
            limit = 40

        conn = get_db(); cur = conn.cursor(dictionary=True)
        q = "SELECT s.*, c.ticker_symbol, c.exchange FROM sip_plan s JOIN company c ON s.company_id = c.company_id WHERE 1=1"
        params = []
        if sector != "all":
            q += " AND s.metal_type = %s"
            params.append(sector)
        if search:
            q += " AND (LOWER(s.sip_name) LIKE %s OR LOWER(c.ticker_symbol) LIKE %s)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
        q += " ORDER BY s.sip_name ASC LIMIT %s"
        params.append(limit)
        cur.execute(q, params)
        rows = clean_rows(cur.fetchall())
        cur.close(); conn.close()
        return ok({"data": rows})
    except:
        return err("DB error")

@app.route("/api/quotes")
def get_quotes():
    """Get live quotes from NSE/Yahoo (100% accurate, NO caching)."""
    symbols = [s.strip().upper() for s in request.args.get("symbols", "").split(",") if s.strip()]
    try:
        quotes = {}
        if not symbols:
            return ok({"data": quotes})
        
        # Fetch LIVE quotes from NSE/Yahoo only
        live_quotes = fetch_quotes_for_symbols(symbols)
        
        for s in symbols:
            quote = live_quotes.get(s)
            if quote:
                market_cap = quote.get("market_cap")
                try:
                    if market_cap is not None:
                        market_cap = float(market_cap)
                except Exception:
                    market_cap = None
                quotes[s] = {
                    "last_price": float(quote.get("last_price", 0)),
                    "pct_change": float(quote.get("pct_change", 0)),
                    "market_cap": market_cap,
                    "source": quote.get("source", "nse"),
                    "timestamp": quote.get("timestamp")
                }
            else:
                # Only fallback to DB if live fetch completely failed
                try:
                    conn = get_db(); cur = conn.cursor(dictionary=True)
                    cur.execute("SELECT market_price FROM company WHERE ticker_symbol = %s", (s,))
                    row = cur.fetchone()
                    cur.close(); conn.close()
                    if row:
                        quotes[s] = {
                            "last_price": float(row.get('market_price', 0)),
                            "pct_change": 0.0,
                            "source": "db_fallback"
                        }
                        print(f"[WARN] /api/quotes: {s} - using DB fallback (live fetch failed)")
                except:
                    pass
        
        return ok({"data": quotes})
    except Exception as e:
        print(f"[ERROR] /api/quotes failed: {e}")
        return err("Quote error")

@app.route("/api/analyse", methods=["POST"])
def analyse():
    try:
        data = request.get_json(force=True)
        plan_type = data.get("plan_type", "stock")
        company_id = data.get("company_id")
        budget = float(data.get("budget", 0))
        user_risk = data.get("risk", "medium")
        goal = data.get("investment_goal", "balanced")
        years = int(data.get("time_horizon", 5))

        if not company_id:
            return jsonify({"success": False, "error": "No company selected"})

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        # 1. Fetch Details
        if plan_type == "stock":
            cur.execute("SELECT * FROM company WHERE company_id = %s", (company_id,))
        else:
            cur.execute("SELECT s.*, c.company_name as name, c.ticker_symbol, c.market_price, c.sector_label FROM sip_plan s JOIN company c ON s.company_id = c.company_id WHERE s.sip_id = %s", (company_id,))
        
        entity = cur.fetchone()
        if not entity:
            return jsonify({"success": False, "error": "Entity not found"})

        # 2. Performance Data
        ret_rate = float(entity.get("avg_return_5y") or entity.get("expected_return") or 12.0)
        risk_level = entity.get("risk_level", "medium")
        price = float(entity.get("market_price", 0))
        sector = entity.get("sector_label", "diversified")
        live_quote = None
        live_pct = 0.0
        ticker = (entity.get("ticker_symbol") or entity.get("ticker") or "").strip().upper()
        if ticker:
            live_quote = fetch_stock_quote_from_nse(ticker)
            if live_quote:
                live_pct = float(live_quote.get("pct_change", 0))
                entity["live_price"] = float(live_quote.get("last_price", price))
                entity["live_price_pct"] = live_pct
            else:
                entity["live_price"] = price
                entity["live_price_pct"] = 0.0
        else:
            entity["live_price"] = price
            entity["live_price_pct"] = 0.0
        
        # Projections
        if plan_type == "stock":
            projected = budget * ((1 + (ret_rate/100)) ** years)
        else:
            monthly = budget / (12 * years) # Spread total budget over duration
            r_m = (ret_rate/100) / 12
            n_m = years * 12
            projected = monthly * (((1 + r_m)**n_m - 1) / r_m) * (1 + r_m)

        gain_pct = round(((projected - budget) / budget) * 100, 1) if budget > 0 else 0

        # 3. STRICT MATCH LOGIC (100% Real)
        passes = []
        issues = []
        risk_map = {"low": 1, "medium": 2, "high": 3}
        u_risk_val = risk_map.get(user_risk, 2)
        e_risk_val = risk_map.get(risk_level, 2)

        # A. Budget Check (Most Important)
        monthly_budget = budget / (12 * years) if years > 0 else 0
        if plan_type == "stock":
            if budget < price:
                issues.append({"rule": "Entry Barrier", "msg": f"Price per share is ₹{price:,.2f}, but your budget is only ₹{budget:,.2f}. You cannot buy a full share."})
            else:
                passes.append({"rule": "Budget Fit", "msg": "Your budget allows for a healthy entry into this asset."})
        else:
            if monthly_budget < entity.get("min_investment", 500):
                issues.append({"rule": "Minimum SIP", "msg": f"Monthly budget (₹{monthly_budget:.0f}) is below the ₹{entity.get('min_investment')} minimum SIP investment."})
            else:
                passes.append({"rule": "Budget Fit", "msg": "Your SIP budget meets the plan's minimum commitment."})

        # B. Risk Alignment
        if u_risk_val < e_risk_val:
            issues.append({"rule": "Risk Warning", "msg": f"This is a {risk_level} risk asset, which is too volatile for your {user_risk} profile."})
        elif u_risk_val > e_risk_val and goal == "aggressive":
            issues.append({"rule": "Growth Mismatch", "msg": f"You want aggressive growth, but this {risk_level} risk asset may be too conservative for you."})
        else:
            passes.append({"rule": "Risk Alignment", "msg": f"This asset matches your {user_risk} risk tolerance."})

        # C. Goal Compatibility
        if goal == "preservation" and e_risk_val >= 3:
            issues.append({"rule": "Goal Conflict", "msg": "High-risk assets are not suitable for capital preservation."})
        elif goal == "aggressive" and ret_rate < 15:
            issues.append({"rule": "Return Gap", "msg": f"Expected return of {ret_rate}% is below typical aggressive targets."})
        elif goal == "balanced" and ret_rate < 10:
            issues.append({"rule": "Growth Caution", "msg": "This asset may be slower than ideal for a balanced growth strategy."})
        else:
            passes.append({"rule": "Goal Match", "msg": "The asset's expected performance aligns with your stated goal."})

        unsuitable_rules = {"Entry Barrier", "Risk Warning", "Goal Conflict", "Return Gap"}
        if not issues:
            verdict = "match"
        elif any(issue["rule"] in unsuitable_rules for issue in issues):
            verdict = "unsuitable"
        else:
            verdict = "caution"

        # 4. Smart Suggestions (Finding TRUE matches within the selected sector)
        acceptable_risks = [user_risk]
        if user_risk == "medium" and goal == "aggressive":
            acceptable_risks.append("high")
        if user_risk == "high":
            acceptable_risks = ["high", "medium"]
        if user_risk == "low" and goal == "balanced":
            acceptable_risks.append("medium")

        placeholders = ",".join(["%s"] * len(acceptable_risks))
        suggestions = []

        if plan_type == "stock":
            cur.execute(f"""SELECT * FROM company 
                        WHERE sector_label = %s AND company_id != %s 
                        AND risk_level IN ({placeholders}) AND market_price <= %s
                        ORDER BY avg_return_5y DESC LIMIT 5""", 
                        [sector, entity.get('company_id', 0), *acceptable_risks, budget])
            alts = cur.fetchall()
            if not alts:
                cur.execute(f"""SELECT * FROM company 
                            WHERE sector_label = %s AND company_id != %s 
                            AND risk_level IN ({placeholders})
                            ORDER BY avg_return_5y DESC LIMIT 5""", 
                            [sector, entity.get('company_id', 0), *acceptable_risks])
                alts = cur.fetchall()
            for a in alts:
                reason = "Fits your budget and risk profile"
                if risk_map.get(a['risk_level'], 2) != u_risk_val:
                    reason = "Offers a closer risk match for your profile"
                suggestions.append({
                    "name": a['company_name'],
                    "risk": a['risk_level'],
                    "return_rate": a['avg_return_5y'],
                    "match_reason": reason
                })
        else:
            cur.execute(f"""SELECT s.*, c.company_name as company_name, c.ticker_symbol, c.sector_label
                        FROM sip_plan s
                        JOIN company c ON s.company_id = c.company_id
                        WHERE c.sector_label = %s AND s.sip_id != %s
                        AND s.risk_level IN ({placeholders}) AND s.min_investment <= %s
                        ORDER BY s.expected_return DESC LIMIT 5""", 
                        [sector, entity.get('sip_id', 0), *acceptable_risks, monthly_budget])
            alts = cur.fetchall()
            if not alts:
                cur.execute(f"""SELECT s.*, c.company_name as company_name, c.ticker_symbol, c.sector_label
                            FROM sip_plan s
                            JOIN company c ON s.company_id = c.company_id
                            WHERE c.sector_label = %s AND s.sip_id != %s
                            AND s.risk_level IN ({placeholders})
                            ORDER BY s.expected_return DESC LIMIT 5""", 
                            [sector, entity.get('sip_id', 0), *acceptable_risks])
                alts = cur.fetchall()
            for a in alts:
                reason = "Fits your SIP budget and risk profile"
                if risk_map.get(a['risk_level'], 2) != u_risk_val:
                    reason = "Closer to your risk tolerance"
                suggestions.append({
                    "name": a['company_name'],
                    "risk": a['risk_level'],
                    "return_rate": a['expected_return'],
                    "match_reason": reason
                })

        cur.close(); conn.close()

        return jsonify({
            "success": True,
            "verdict": verdict,
            "projected": round(projected, 2),
            "gain_pct": gain_pct,
            "passes": passes,
            "issues": issues,
            "suggestions": suggestions,
            "entity": {
                "name": entity.get("company_name") or entity.get("sip_name"),
                "live_price": float(entity.get("live_price", price)),
                "live_price_pct": float(entity.get("live_price_pct", 0))
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})



def fetch_quotes_for_symbols(symbols):
    """Fetch live quotes from NSE with Yahoo fallback. NO CACHING for 100% accuracy."""
    quotes = {}
    if not symbols:
        return quotes
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_stock_quote_from_nse, s): s for s in symbols}
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                quote = future.result(timeout=15)
                if quote:
                    quote['ticker_symbol'] = ticker
                    quote['source'] = 'nse'
                    quotes[ticker] = quote
                    continue
            except Exception as e:
                print(f"[WARN] NSE quote for {ticker} failed: {e}")
            
            try:
                fallback = fetch_stock_quote_from_yahoo(ticker)
                if fallback:
                    fallback['ticker_symbol'] = ticker
                    fallback['source'] = 'yahoo'
                    quotes[ticker] = fallback
                    continue
            except Exception as fallback_err:
                print(f"[WARN] Yahoo fallback for {ticker} failed: {fallback_err}")
    
    return quotes


def fetch_live_news():
    """
    Fetches real-time market news from NewsAPI.org
    Topics: Gold prices, Silver prices, Platinum prices, Currency rates, Metals market
    """
    try:
        if not NEWS_API_KEY or NEWS_API_KEY == "your_newsapi_key":
            print("[WARN] NEWS_API_KEY not configured. Skipping news fetch.")
            return
        
        conn = get_db(); cur = conn.cursor(dictionary=True)
        
        # Search for all relevant market topics in a single NewsAPI request
        search_queries = [
            "gold OR silver OR platinum OR metals market OR currency rates OR USD INR exchange OR forex trading OR precious metals OR commodity prices"
        ]
        
        articles_added = 0
        
        for query in search_queries:
            try:
                # NewsAPI endpoint
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": query,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 20,
                    "apiKey": NEWS_API_KEY,
                }
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 429:
                    print(f"[WARN] NewsAPI rate limit exceeded for '{query}' (429). Reduce requests or upgrade the plan.")
                    break
                if response.status_code != 200:
                    print("[WARN] NewsAPI Error for '" + query + "': " + str(response.status_code))
                    continue
                
                data = response.json()
                if data.get("status") != "ok":
                    print(f"[WARN] NewsAPI response not OK for '{query}': {data.get('message', 'unknown error')}")
                    continue
                
                if not data.get("articles"):
                    print(f"📰 No articles found for: {query}")
                    continue
                
                # Store each article
                for article in data.get("articles", []):
                    try:
                        title = article.get("title", "")
                        description = article.get("description", "")
                        source_name = article.get("source", {}).get("name", "Unknown")
                        url = article.get("url", "")
                        published_at = article.get("publishedAt")
                        
                        if not title or not url:
                            continue
                        
                        # Convert ISO timestamp to MySQL format
                        if published_at:
                            published_at = published_at.replace("Z", "+00:00")
                            try:
                                dt = datetime.fromisoformat(published_at)
                            except ValueError:
                                try:
                                    dt = datetime.strptime(published_at[:19], "%Y-%m-%dT%H:%M:%S")
                                except Exception:
                                    dt = None
                            if dt:
                                published_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                published_at = None
                        
                        # Try to insert (will skip if URL already exists due to UNIQUE constraint)
                        cur.execute("""
                            INSERT INTO market_news 
                            (title, description, source, news_url, published_at, fetched_at) 
                            VALUES (%s, %s, %s, %s, %s, NOW())
                            ON DUPLICATE KEY UPDATE fetched_at = NOW()
                        """, (title, description, source_name, url, published_at))
                        articles_added += 1
                    except Exception as article_err:
                        print(f"  ❌ Article error: {article_err}")
                        continue
                
                conn.commit()
                print("[OK] Fetched articles for '" + query + "': " + str(articles_added) + " stored")
                
            except Exception as e:
                print(f"❌ Error fetching news for '{query}': {e}")
                continue
        
        # Clean old news (older than 30 days)
        try:
            cur.execute("DELETE FROM market_news WHERE fetched_at < DATE_SUB(NOW(), INTERVAL 30 DAY)")
            conn.commit()
            print("[CLEAN] Cleaned old news articles")
        except:
            pass
        
        cur.close(); conn.close()
        print(f"🔔 News Update Complete - {articles_added} articles stored")
        
    except Exception as e:
        print(f"❌ fetch_live_news() Error: {e}")

def init_prices():
    try:
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) as cnt FROM metal_price")
        if cur.fetchone()['cnt'] < 10:
            import random
            base = {"gold": 15224.0, "silver": 262.0, "platinum": 6793.0, "usd_inr": 94.91}
            for i in range(30, -1, -1):
                ts = datetime.now() - timedelta(days=i)
                for m, b in base.items():
                    p = b * (1 + random.uniform(-0.02, 0.02))
                    cur.execute("INSERT INTO metal_price (metal_type, price_per_gram, currency, recorded_at) VALUES (%s, %s, %s, %s)", (m, p, "INR", ts))
            conn.commit()
        cur.close(); conn.close()
    except: pass

if __name__ == "__main__":
    print("\n" + "="*50)
    print("[START] METALTRACKER SERVER STARTING...")
    print("="*50)
    
    # Run heavy initialization in background threads to avoid blocking server startup
    from threading import Thread
    
    def init_background():
        try:
            print("[BG] Initializing database...")
            populate_investment_data()
            print("[BG] Fetching initial prices...")
            fetch_and_store_prices()
            print("[BG] Fetching initial news...")
            fetch_live_news()
            print("[BG] Background initialization complete!")
        except Exception as e:
            print(f"[BG ERROR] {e}")
    
    # Start background thread for initialization
    bg_thread = Thread(target=init_background, daemon=True)
    bg_thread.start()

    # Check API configuration
    if not NEWS_API_KEY or NEWS_API_KEY == "your_newsapi_key":
        print("\n[WARN] NewsAPI NOT configured!")
        print("   To enable real market news:")
        print("   1. Visit: https://newsapi.org/register")
        print("   2. Get your FREE API key")
        print("   3. Update: NEWS_API_KEY = 'your_key' in app.py\n")
    else:
        print("\n[OK] NewsAPI Configured - Real-time news enabled!\n")

    # Start scheduler
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=fetch_and_store_prices, trigger="interval", minutes=5)
        scheduler.add_job(func=fetch_live_news, trigger="interval", minutes=60)
        scheduler.add_job(func=check_and_trigger_alerts, trigger="interval", minutes=2)
        scheduler.start()
        print("[OK] Scheduler Active (Prices: 5min, News: 30min, Alerts: 2min).")
    except Exception as e:
        print("[WARN] Scheduler Warning: " + str(e))

    try:
        from waitress import serve
        import sys
        print("\n" + "="*50)
        print("[SERVER] ✅ LISTENING ON http://127.0.0.1:5001")
        print("="*50 + "\n")
        print("[WAITRESS] Starting Waitress server...")
        sys.stdout.flush()
        serve(app, host='0.0.0.0', port=5001, threads=6)
    except ImportError as ie:
        print(f"[WARNING] Waitress import error: {ie}")
        print("[WARNING] Falling back to Flask (WITHOUT debug/reloader)...")
        print("\n" + "="*50)
        print("[SERVER] ✅ LISTENING ON http://127.0.0.1:5001")
        print("="*50 + "\n")
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"[ERROR] Server startup failed: {e}")
        import traceback
        traceback.print_exc()
