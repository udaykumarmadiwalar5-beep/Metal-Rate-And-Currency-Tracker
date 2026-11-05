# 🎯 LIVE METAL PRICE API - INTEGRATION GUIDE

## Quick Start

### Server Status
Backend is running on: **http://127.0.0.1:5000**

All endpoints return JSON responses with `{ "success": true, "data": {...} }` format

---

## 📡 API Examples

### 1. Get Live Base Prices + All Regional Prices

```javascript
// Frontend JavaScript
async function getLivePrices() {
  const response = await fetch('http://localhost:5000/api/prices/live');
  const data = await response.json();
  
  if (data.success) {
    const prices = data.prices;
    
    // Base prices
    console.log('Gold (per 10g):', prices.gold);        // ₹15,328.46
    console.log('Silver (per g):', prices.silver);      // ₹253.82
    console.log('Platinum (per g):', prices.platinum);  // ₹6,155.48
    console.log('USD/INR:', prices.usd_inr);            // ₹94.49
    
    // Regional prices (36 states/UTs)
    const regional = data.regional_prices;
    console.log('Maharashtra:', regional.Maharashtra.gold);  // ₹15,328.46
    console.log('Tamil Nadu:', regional['Tamil Nadu'].gold); // ₹15,465.47
    console.log('Assam:', regional.Assam.gold);              // ₹15,902.20
    
    // All states
    Object.keys(regional).forEach(state => {
      console.log(`${state}: ₹${regional[state].gold}`);
    });
  }
}
```

### 2. Get Historical Chart Data

```javascript
// Get 1-day chart for gold
async function getGoldChart() {
  const response = await fetch(
    'http://localhost:5000/api/prices/chart?metal=gold&range=1d'
  );
  const data = await response.json();
  
  if (data.success) {
    const goldData = data.data.gold;
    
    // Line chart data (9 points for 1 day)
    console.log('Line points:', goldData.line);
    // [
    //   { t: "2026-05-09T08:00:00", y: 152850.5 },
    //   { t: "2026-05-09T09:00:00", y: 153150.2 },
    //   ...
    // ]
    
    // Candlestick OHLC data
    console.log('OHLC candles:', goldData.ohlc);
    // [
    //   { 
    //     t: "2026-05-09T08:00:00",
    //     o: 152850,  // Open
    //     h: 153500,  // High
    //     l: 152400,  // Low
    //     c: 153200   // Close
    //   },
    //   ...
    // ]
  }
}

// Other time ranges available:
// ?range=1d  (1 day, 9 points)
// ?range=1m  (1 month, ~30 points)
// ?range=3m  (3 months, ~90 points)
// ?range=6m  (6 months, ~180 points)
// ?range=1y  (1 year, ~365 points)
// ?range=3y  (3 years, ~1095 points)
```

### 3. Get Market News

```javascript
async function getNews() {
  const response = await fetch('http://localhost:5000/api/news');
  const data = await response.json();
  
  if (data.success) {
    const articles = data.data;  // 89 articles
    
    articles.forEach(article => {
      console.log('Title:', article.title);
      console.log('Source:', article.source);
      console.log('Published:', article.published);
      console.log('URL:', article.url);
      console.log('---');
    });
  }
}
```

---

## 🎨 UI Implementation Examples

### Dashboard Widget - Live Prices

```html
<div class="price-widget">
  <h2>Live Metal Prices</h2>
  
  <div class="price-item">
    <span class="label">Gold (per 10g)</span>
    <span class="price gold-price">₹--</span>
    <span class="change"></span>
  </div>
  
  <div class="price-item">
    <span class="label">Silver (per g)</span>
    <span class="price silver-price">₹--</span>
    <span class="change"></span>
  </div>
  
  <div class="price-item">
    <span class="label">Platinum (per g)</span>
    <span class="price platinum-price">₹--</span>
    <span class="change"></span>
  </div>
</div>

<script>
async function updatePrices() {
  const response = await fetch('/api/prices/live');
  const data = await response.json();
  
  if (data.success) {
    const prices = data.prices;
    
    document.querySelector('.gold-price').textContent = 
      '₹' + prices.gold.toLocaleString('en-IN', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
    
    document.querySelector('.silver-price').textContent = 
      '₹' + prices.silver.toLocaleString('en-IN', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
    
    document.querySelector('.platinum-price').textContent = 
      '₹' + prices.platinum.toLocaleString('en-IN', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
  }
}

// Update immediately and then every 5 minutes
updatePrices();
setInterval(updatePrices, 5 * 60 * 1000);
</script>
```

### Regional Price Selector

```html
<div class="regional-price-selector">
  <h3>Regional Prices</h3>
  
  <select id="state-selector">
    <option value="">Select State/UT</option>
    <!-- Options will be populated from API -->
  </select>
  
  <div id="regional-prices">
    <p>Gold: ₹<span id="regional-gold">--</span></p>
    <p>Silver: ₹<span id="regional-silver">--</span></p>
    <p>Platinum: ₹<span id="regional-platinum">--</span></p>
  </div>
</div>

<script>
let regionalData = {};

// Load live prices and populate selector
async function loadRegionalPrices() {
  const response = await fetch('/api/prices/live');
  const data = await response.json();
  
  if (data.success) {
    regionalData = data.regional_prices;
    
    // Populate state selector
    const selector = document.getElementById('state-selector');
    Object.keys(regionalData).sort().forEach(state => {
      const option = document.createElement('option');
      option.value = state;
      option.textContent = state;
      selector.appendChild(option);
    });
    
    // Default to first state
    selector.value = Object.keys(regionalData)[0];
    displayRegionalPrice(selector.value);
  }
}

// Display selected state's prices
function displayRegionalPrice(state) {
  if (state && regionalData[state]) {
    const prices = regionalData[state];
    document.getElementById('regional-gold').textContent = 
      prices.gold.toLocaleString('en-IN', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
    document.getElementById('regional-silver').textContent = 
      prices.silver.toLocaleString('en-IN', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
    document.getElementById('regional-platinum').textContent = 
      prices.platinum.toLocaleString('en-IN', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
  }
}

// Event listener
document.getElementById('state-selector').addEventListener('change', (e) => {
  displayRegionalPrice(e.target.value);
});

loadRegionalPrices();
</script>
```

### Chart Display (with Chart.js)

```html
<div class="chart-container">
  <h3>Gold Price Chart</h3>
  
  <div class="chart-controls">
    <button onclick="showChart('1d')">1 Day</button>
    <button onclick="showChart('1m')">1 Month</button>
    <button onclick="showChart('3m')">3 Months</button>
    <button onclick="showChart('1y')">1 Year</button>
  </div>
  
  <canvas id="price-chart"></canvas>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
let chart = null;

async function showChart(range) {
  const response = await fetch(
    `/api/prices/chart?metal=gold&range=${range}`
  );
  const data = await response.json();
  
  if (data.success) {
    const goldData = data.data.gold;
    const linePoints = goldData.line;
    
    const labels = linePoints.map(p => new Date(p.t).toLocaleString());
    const prices = linePoints.map(p => p.y);
    
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    if (chart) chart.destroy();
    
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Gold Price (per 10g)',
          data: prices,
          borderColor: '#D4AF37',
          backgroundColor: 'rgba(212, 175, 55, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: true,
            labels: { color: '#666' }
          }
        },
        scales: {
          y: {
            beginAtZero: false,
            title: { display: true, text: 'Price (₹)' }
          }
        }
      }
    });
  }
}

// Show 1 day chart by default
showChart('1d');
</script>
```

### News Ticker

```html
<div class="news-ticker">
  <h3>📰 Market News</h3>
  <div id="news-list" class="news-scroll">
    <!-- News will be populated here -->
  </div>
</div>

<script>
async function displayNews() {
  const response = await fetch('/api/news');
  const data = await response.json();
  
  if (data.success) {
    const articles = data.data;
    const newsList = document.getElementById('news-list');
    
    articles.slice(0, 10).forEach(article => {
      const newsItem = document.createElement('div');
      newsItem.className = 'news-item';
      newsItem.innerHTML = `
        <h4>${article.title}</h4>
        <p class="source">${article.source}</p>
        <p class="time">${new Date(article.published).toLocaleDateString()}</p>
        <a href="${article.url}" target="_blank">Read more →</a>
      `;
      newsList.appendChild(newsItem);
    });
  }
}

displayNews();
// Refresh every 30 minutes
setInterval(displayNews, 30 * 60 * 1000);
</script>
```

---

## 💾 Data Structure Reference

### Regional States/UTs (36 Total)

**North**: 
- Haryana, Punjab, Himachal Pradesh, Jammu & Kashmir, Ladakh, Uttarakhand, Uttar Pradesh

**South**: 
- Tamil Nadu, Karnataka, Telangana, Andhra Pradesh, Kerala

**East**: 
- West Bengal, Assam, Meghalaya, Tripura, Manipur, Mizoram, Nagaland, Sikkim, Jharkhand, Odisha, Bihar

**West**: 
- Gujarat, Maharashtra, Rajasthan

**Central**: 
- Madhya Pradesh, Chhattisgarh

**UTs**: 
- Delhi, Goa, Puducherry, Chandigarh, Daman & Diu, Dadra & Nagar Haveli, Andaman & Nicobar Islands, Lakshadweep

---

## 🔄 Update Frequency

- **Metal Prices**: Every 5 minutes
- **News Articles**: Every 30 minutes
- **Charts**: Calculated from stored data (90-day history)
- **USD/INR Rate**: Every 5 minutes (live)

---

## ⚠️ Error Handling

```javascript
async function safeGetPrices() {
  try {
    const response = await fetch('/api/prices/live', { 
      timeout: 5000 
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
      console.error('API Error:', data.error);
      return null;
    }
    
    return data;
    
  } catch (error) {
    console.error('Failed to fetch prices:', error);
    // Show cached prices or default values
    return getCachedPrices() || getDefaultPrices();
  }
}
```

---

## 🎯 Performance Tips

1. **Cache prices for 5 minutes** to reduce API calls
2. **Use line charts for short ranges** (1d, 1m) - faster rendering
3. **Use candlestick for long ranges** (6m+) - better pattern visibility
4. **Lazy load regional state selector** - only populate when needed
5. **Store news locally** - update every 30 minutes in background

---

## ✅ Testing Checklist

- [ ] Live prices endpoint returns 200
- [ ] All 36 states appear in regional_prices
- [ ] Chart data has correct OHLC values
- [ ] News articles display with titles and sources
- [ ] USD/INR rate updates every 5 minutes
- [ ] Regional multipliers between 1.00-1.12
- [ ] Prices update every 5 minutes (check timestamps)
- [ ] Frontend displays prices with ₹ symbol
- [ ] State selector filters regional prices correctly
- [ ] Charts render without errors

---

**Ready to integrate!** 🚀
