# NewsAPI Integration Setup Guide

## Overview
Your MetaTracker application now includes **real-time market news** fetching from [NewsAPI.org](https://newsapi.org). This provides up-to-date articles about metals prices, currency rates, forex trading, and precious metals markets.

---

## ⚡ Quick Start (2 Minutes)

### Step 1: Get Your Free NewsAPI Key
1. Visit: **https://newsapi.org/register**
2. Sign up with your email (FREE account)
3. Verify your email
4. Copy your **API Key**

### Step 2: Update Your Backend
Open `Backend/app.py` and find this line (around line 140):
```python
NEWS_API_KEY = "your_newsapi_key"
```

Replace it with:
```python
NEWS_API_KEY = "YOUR_ACTUAL_API_KEY_HERE"
```

### Step 3: Restart Server
```bash
cd Backend
python app.py
```

You should see:
```
✅ NewsAPI Configured - Real-time news enabled!
```

---

## 🔄 How It Works

### Automatic News Fetching
Once configured, the system:
- ✅ Fetches news **every 30 minutes** (scheduled job)
- ✅ Searches for articles about:
  - Gold prices
  - Silver prices
  - Platinum prices
  - Metals market
  - Currency rates
  - USD/INR exchange rates
  - Forex trading
  - Precious metals
  - Commodity prices

- ✅ Stores articles in MySQL database (`market_news` table)
- ✅ Automatically cleans articles older than 30 days
- ✅ Prevents duplicates (same article won't be stored twice)

### API Endpoints

#### Get Latest News
```
GET /api/news
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "news_id": 1,
      "title": "Gold prices surge to record highs",
      "description": "Precious metals market sees...",
      "source": "Reuters",
      "news_url": "https://...",
      "published_at": "2026-05-09 14:30:00",
      "fetched_at": "2026-05-09 15:00:00"
    },
    ...
  ]
}
```

---

## 📊 NewsAPI Pricing

| Plan | Requests/Day | Cost | Best For |
|------|-------------|------|----------|
| **Developer (Free)** | 100 | FREE | Testing & Development |
| **Professional** | 50,000 | $45/month | Production |
| **Business** | Unlimited | Custom | Enterprise |

**Current Setup:** Using Developer plan (100 requests/day)
- Fetches 9 different search queries every 30 minutes
- Average: ~18 requests/hour = ~432 requests/day
- **⚠️ May need upgrade** to Professional plan for production

---

## ✅ Features Included

### 1. **Real-Time Market News**
- Latest articles about metals and currency markets
- From 50,000+ news sources globally
- Updated every 30 minutes

### 2. **Smart Deduplication**
- Database UNIQUE constraint on `news_url`
- Prevents storing same article multiple times

### 3. **Automatic Cleanup**
- Articles older than 30 days auto-deleted
- Database stays optimized and fast

### 4. **Error Handling**
- Graceful failures if API is down
- Detailed logging of issues
- Continues operation if one query fails

### 5. **Multiple Search Topics**
- Gold, Silver, Platinum specific searches
- General metals market queries
- Currency and forex specific searches
- Commodity price searches

---

## 🔧 Troubleshooting

### Issue: "NewsAPI NOT configured"
**Solution:** 
- Add your API key to `Backend/app.py`
- Restart the server

### Issue: "NewsAPI Error: 401"
**Solution:**
- Your API key is invalid
- Regenerate it from https://newsapi.org/account

### Issue: "NewsAPI Error: 429"
**Solution:**
- You've exceeded your daily request quota (100 for free plan)
- Wait until next day, or upgrade to Professional plan

### Issue: News articles not showing up
**Solution:**
1. Check the database:
```sql
SELECT COUNT(*) FROM market_news;
SELECT * FROM market_news ORDER BY fetched_at DESC LIMIT 5;
```

2. Check if scheduled job is running:
```
Look for "✅ Fetched articles..." messages in server logs
```

---

## 📈 Production Recommendations

For production deployment:

1. **Upgrade to Professional Plan**
   - Cost: $45/month for 50,000 requests/day
   - Necessary if fetching news every 10-15 minutes

2. **Optimize Search Frequency**
   ```python
   # In app.py, change:
   scheduler.add_job(func=fetch_live_news, trigger="interval", minutes=30)
   # To:
   scheduler.add_job(func=fetch_live_news, trigger="interval", minutes=60)  # Less frequent
   ```

3. **Use Environment Variables**
   ```python
   import os
   NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "your_newsapi_key")
   ```

4. **Monitor API Usage**
   - Check your usage at: https://newsapi.org/account

---

## 🎯 Testing the Integration

### Manual Test in Python
```python
import requests

# Test endpoint
response = requests.get("http://localhost:5000/api/news")
print(response.json())
```

### Expected Output
```json
{
  "success": true,
  "data": [
    {
      "news_id": 1,
      "title": "...",
      "source": "...",
      ...
    },
    ...
  ]
}
```

---

## 📚 Additional Resources

- **NewsAPI Documentation**: https://newsapi.org/docs
- **API Status**: https://newsapi.org/docs/get-started
- **Query Language**: https://newsapi.org/docs/endpoints/everything

---

## ✨ Your News Is Now Live!

The `/api/news` endpoint will automatically display:
- ✅ Latest market news
- ✅ Metals price movements
- ✅ Currency rate updates
- ✅ Global forex news
- ✅ Commodity market insights

**All updated every 30 minutes automatically!** 🚀
