-- ============================================================
--  MetalTracker -- Complete NSE & BSE Stock Database
--  Database  : metalcur
--  Tables    : users, metal_price, company, sip_plan,
--              alerts, market_news
--
--  Companies : 111 real NSE/BSE listed stocks + ETFs
--  Sectors   : gold, silver, platinum, banking, it, pharma,
--              fmcg, auto, energy, infra, realty, telecom,
--              diversified, etf
--
--  HOW TO RUN:
--    Option 1 (MySQL CLI):
--      mysql -u root -p < setup_database.sql
--    Option 2 (MySQL Workbench):
--      Open this file -> Run All (Ctrl+Shift+Enter)
--    Option 3 (Python):
--      python setup_database.py
-- ============================================================

CREATE DATABASE IF NOT EXISTS metalcur
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE metalcur;

-- Drop in safe FK order
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS sip_plan;
DROP TABLE IF EXISTS company;
DROP TABLE IF EXISTS metal_price;
DROP TABLE IF EXISTS market_news;
DROP TABLE IF EXISTS users;

-- ============================================================
--  TABLE: users
-- ============================================================
CREATE TABLE users (
    user_id    INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(80)  NOT NULL UNIQUE,
    email      VARCHAR(120) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    theme_mode VARCHAR(10)  NOT NULL DEFAULT 'light',
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
--  TABLE: metal_price
-- ============================================================
CREATE TABLE metal_price (
    price_id       INT            NOT NULL AUTO_INCREMENT PRIMARY KEY,
    metal_type     VARCHAR(20)    NOT NULL,
    price_per_gram DECIMAL(18,6)  NOT NULL,
    currency       VARCHAR(10)    NOT NULL DEFAULT 'INR',
    recorded_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metal_recorded (metal_type, recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
--  TABLE: company
--  All NSE/BSE listed stocks across every major sector.
--  'metal_type' column acts as the sector/category filter
--   used by the investment API (backward-compatible).
--  market_cap stored in INR rupees (1 Cr = 10,000,000)
-- ============================================================
CREATE TABLE company (
    company_id    INT            NOT NULL AUTO_INCREMENT PRIMARY KEY,
    company_name  VARCHAR(150)   NOT NULL,
    ticker_symbol VARCHAR(20)    NOT NULL,
    exchange      VARCHAR(15)    NOT NULL DEFAULT 'NSE & BSE',
    metal_type    VARCHAR(20)    NOT NULL,   -- sector key used by API
    sector_label  VARCHAR(50)    NOT NULL,   -- human-readable sector name
    risk_level    VARCHAR(10)    NOT NULL DEFAULT 'medium',
    avg_return_5y DECIMAL(6,2)   NULL,
    market_cap    BIGINT         NULL,
    created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
--  TABLE: sip_plan
-- ============================================================
CREATE TABLE sip_plan (
    sip_id          INT           NOT NULL AUTO_INCREMENT PRIMARY KEY,
    company_id      INT           NOT NULL,
    sip_name        VARCHAR(200)  NOT NULL,
    metal_type      VARCHAR(20)   NOT NULL,
    min_investment  DECIMAL(12,2) NOT NULL DEFAULT 500.00,
    risk_level      VARCHAR(10)   NOT NULL DEFAULT 'medium',
    expected_return DECIMAL(6,2)  NULL,
    duration_years  INT           NOT NULL DEFAULT 5,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sip_company FOREIGN KEY (company_id)
        REFERENCES company (company_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
--  TABLE: alerts
-- ============================================================
CREATE TABLE alerts (
    alert_id       INT            NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id        INT            NOT NULL,
    metal_type     VARCHAR(20)    NOT NULL,
    condition_type VARCHAR(10)    NOT NULL,
    target_price   DECIMAL(12,2)  NOT NULL,
    status         VARCHAR(15)    NOT NULL DEFAULT 'watching',
    created_at     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alert_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
--  TABLE: market_news
-- ============================================================
CREATE TABLE market_news (
    news_id      INT           NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(400)  NOT NULL,
    description  TEXT          NULL,
    source       VARCHAR(100)  NULL,
    news_url     VARCHAR(600)  NOT NULL UNIQUE,
    published_at DATETIME      NULL,
    fetched_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ============================================================
--  SEED: metal_price  (April 2026 Indian retail rates)
-- ============================================================
INSERT INTO metal_price (metal_type, price_per_gram, currency) VALUES
    ('gold',     9400.00, 'INR'),
    ('silver',   108.00,  'INR'),
    ('platinum', 3250.00, 'INR'),
    ('usd_inr',  84.25,   'INR');


-- ============================================================
--  SEED: company  (111 NSE/BSE stocks across 14 sectors)
--
--  Columns: company_name, ticker_symbol, exchange,
--           metal_type (sector key), sector_label,
--           risk_level, avg_return_5y (%), market_cap (INR)
-- ============================================================
INSERT INTO company
    (company_name, ticker_symbol, exchange, metal_type, sector_label, risk_level, avg_return_5y, market_cap)
VALUES

-- ══════════════════════════════════════════════════════════════
--  GOLD  (10 stocks) — Jewellery, Gold Finance, Gold Refining
-- ══════════════════════════════════════════════════════════════
('Titan Company Ltd',           'TITAN',      'NSE & BSE', 'gold',    'Gold & Jewellery', 'low',    15.20,  2800000000000),
('Muthoot Finance Ltd',         'MUTHOOTFIN', 'NSE & BSE', 'gold',    'Gold & Jewellery', 'medium', 18.50,   650000000000),
('Manappuram Finance Ltd',      'MANAPPURAM', 'NSE & BSE', 'gold',    'Gold & Jewellery', 'medium', 12.30,   150000000000),
('Kalyan Jewellers India Ltd',  'KALYANKJIL', 'NSE & BSE', 'gold',    'Gold & Jewellery', 'medium', 22.10,   250000000000),
('Senco Gold Ltd',              'SENCO',      'NSE & BSE', 'gold',    'Gold & Jewellery', 'high',   28.40,    40000000000),
('PC Jeweller Ltd',             'PCJEWELLER', 'NSE & BSE', 'gold',    'Gold & Jewellery', 'high',    8.20,    25000000000),
('Rajesh Exports Ltd',          'RAJESHEXPO', 'NSE & BSE', 'gold',    'Gold & Jewellery', 'low',    10.50,    80000000000),
('Thangamayil Jewellery Ltd',   'THANGAMAYL', 'NSE & BSE', 'gold',    'Gold & Jewellery', 'high',   30.20,    30000000000),
('Tribhovandas Bhimji Zaveri',  'TBZ',        'BSE',       'gold',    'Gold & Jewellery', 'medium', 14.80,    15000000000),
('Vaibhav Global Ltd',          'VAIBHAVGBL', 'NSE & BSE', 'gold',    'Gold & Jewellery', 'medium', 16.50,    80000000000),

-- ══════════════════════════════════════════════════════════════
--  SILVER  (8 stocks) — Primary silver producers / base metals
-- ══════════════════════════════════════════════════════════════
('Hindustan Zinc Ltd',          'HINDZINC',   'NSE & BSE', 'silver',  'Silver & Base Metals', 'low',    11.80, 1250000000000),
('Vedanta Ltd',                 'VEDL',       'NSE & BSE', 'silver',  'Silver & Base Metals', 'high',   19.50, 1600000000000),
('NMDC Ltd',                    'NMDC',       'NSE & BSE', 'silver',  'Silver & Base Metals', 'low',     8.50,  450000000000),
('Shyam Metalics & Energy Ltd', 'SHYAMMETL',  'NSE & BSE', 'silver',  'Silver & Base Metals', 'medium', 15.30,  120000000000),
('Hindustan Copper Ltd',        'HINDCOPPER', 'NSE & BSE', 'silver',  'Silver & Base Metals', 'high',   22.50,  200000000000),
('MOIL Ltd',                    'MOIL',       'NSE & BSE', 'silver',  'Silver & Base Metals', 'low',     9.80,   80000000000),
('Gravita India Ltd',           'GRAVITA',    'NSE',       'silver',  'Silver & Base Metals', 'medium', 18.70,   50000000000),
('National Aluminium Co Ltd',   'NATIONALUM', 'NSE & BSE', 'silver',  'Silver & Base Metals', 'low',    12.10,  250000000000),

-- ══════════════════════════════════════════════════════════════
--  PLATINUM  (7 stocks) — Specialty & alloy metals
-- ══════════════════════════════════════════════════════════════
('MMTC Ltd',                    'MMTC',       'NSE & BSE', 'platinum','Platinum & Specialty', 'low',     5.20,   35000000000),
('Mishra Dhatu Nigam Ltd',      'MIDHANI',    'NSE & BSE', 'platinum','Platinum & Specialty', 'medium', 10.20,   45000000000),
('Tata Steel Ltd',              'TATASTEEL',  'NSE & BSE', 'platinum','Platinum & Specialty', 'medium', 13.50, 1700000000000),
('JSW Steel Ltd',               'JSWSTEEL',   'NSE & BSE', 'platinum','Platinum & Specialty', 'medium', 15.80, 2000000000000),
('Usha Martin Ltd',             'USHAMART',   'NSE & BSE', 'platinum','Platinum & Specialty', 'medium', 18.20,   60000000000),
('Ferro Alloys Corp Ltd',       'FACOR',      'NSE & BSE', 'platinum','Platinum & Specialty', 'high',   12.30,   15000000000),
('Steel Authority of India',    'SAIL',       'NSE & BSE', 'platinum','Platinum & Specialty', 'low',     9.10,  380000000000),

-- ══════════════════════════════════════════════════════════════
--  BANKING & FINANCE  (10 stocks)
-- ══════════════════════════════════════════════════════════════
('HDFC Bank Ltd',               'HDFCBANK',   'NSE & BSE', 'banking', 'Banking & Finance', 'low',    16.80, 12800000000000),
('ICICI Bank Ltd',              'ICICIBANK',  'NSE & BSE', 'banking', 'Banking & Finance', 'low',    22.50,  8500000000000),
('State Bank of India',         'SBIN',       'NSE & BSE', 'banking', 'Banking & Finance', 'medium', 18.20,  7200000000000),
('Axis Bank Ltd',               'AXISBANK',   'NSE & BSE', 'banking', 'Banking & Finance', 'medium', 14.50,  3600000000000),
('Kotak Mahindra Bank Ltd',     'KOTAKBANK',  'NSE & BSE', 'banking', 'Banking & Finance', 'low',    15.30,  3800000000000),
('IndusInd Bank Ltd',           'INDUSINDBK', 'NSE & BSE', 'banking', 'Banking & Finance', 'medium', 12.10,  1100000000000),
('Bank of Baroda',              'BANKBARODA', 'NSE & BSE', 'banking', 'Banking & Finance', 'medium', 19.50,  1300000000000),
('Punjab National Bank',        'PNB',        'NSE & BSE', 'banking', 'Banking & Finance', 'high',   15.80,  1200000000000),
('Federal Bank Ltd',            'FEDERALBNK', 'NSE & BSE', 'banking', 'Banking & Finance', 'medium', 14.20,   450000000000),
('Yes Bank Ltd',                'YESBANK',    'NSE & BSE', 'banking', 'Banking & Finance', 'high',    8.40,   450000000000),

-- ══════════════════════════════════════════════════════════════
--  INFORMATION TECHNOLOGY  (10 stocks)
-- ══════════════════════════════════════════════════════════════
('Tata Consultancy Services',   'TCS',        'NSE & BSE', 'it',      'Information Technology', 'low',    14.50, 14500000000000),
('Infosys Ltd',                 'INFY',       'NSE & BSE', 'it',      'Information Technology', 'low',    12.30,  7200000000000),
('Wipro Ltd',                   'WIPRO',      'NSE & BSE', 'it',      'Information Technology', 'medium', 10.80,  2800000000000),
('HCL Technologies Ltd',        'HCLTECH',    'NSE & BSE', 'it',      'Information Technology', 'low',    18.20,  4500000000000),
('Tech Mahindra Ltd',           'TECHM',      'NSE & BSE', 'it',      'Information Technology', 'medium', 13.50,  1500000000000),
('LTIMindtree Ltd',             'LTIM',       'NSE & BSE', 'it',      'Information Technology', 'medium', 22.40,  1700000000000),
('Mphasis Ltd',                 'MPHASIS',    'NSE & BSE', 'it',      'Information Technology', 'medium', 19.80,   550000000000),
('Persistent Systems Ltd',      'PERSISTENT', 'NSE & BSE', 'it',      'Information Technology', 'high',   35.20,   800000000000),
('Coforge Ltd',                 'COFORGE',    'NSE & BSE', 'it',      'Information Technology', 'high',   28.50,   450000000000),
('KPIT Technologies Ltd',       'KPITTECH',   'NSE & BSE', 'it',      'Information Technology', 'high',   42.30,   400000000000),

-- ══════════════════════════════════════════════════════════════
--  PHARMA & HEALTHCARE  (8 stocks)
-- ══════════════════════════════════════════════════════════════
('Sun Pharmaceutical Industries','SUNPHARMA', 'NSE & BSE', 'pharma',  'Pharma & Healthcare', 'low',    18.50,  4200000000000),
('Dr Reddys Laboratories Ltd',  'DRREDDY',    'NSE & BSE', 'pharma',  'Pharma & Healthcare', 'low',    15.20,  1000000000000),
('Cipla Ltd',                   'CIPLA',      'NSE & BSE', 'pharma',  'Pharma & Healthcare', 'low',    14.80,  1100000000000),
('Lupin Ltd',                   'LUPIN',      'NSE & BSE', 'pharma',  'Pharma & Healthcare', 'medium', 12.50,   800000000000),
('Divis Laboratories Ltd',      'DIVISLAB',   'NSE & BSE', 'pharma',  'Pharma & Healthcare', 'medium', 20.30,  1300000000000),
('Apollo Hospitals Enterprises','APOLLOHOSP', 'NSE & BSE', 'pharma',  'Pharma & Healthcare', 'medium', 28.50,   900000000000),
('Biocon Ltd',                  'BIOCON',     'NSE & BSE', 'pharma',  'Pharma & Healthcare', 'high',    8.20,   300000000000),
('Aurobindo Pharma Ltd',        'AUROPHARMA', 'NSE & BSE', 'pharma',  'Pharma & Healthcare', 'medium', 11.50,   450000000000),

-- ══════════════════════════════════════════════════════════════
--  FMCG / CONSUMER GOODS  (9 stocks)
-- ══════════════════════════════════════════════════════════════
('Hindustan Unilever Ltd',      'HINDUNILVR', 'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'low',    12.30,  5600000000000),
('ITC Ltd',                     'ITC',        'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'low',    18.90,  5500000000000),
('Nestle India Ltd',            'NESTLEIND',  'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'low',    16.50,  2100000000000),
('Britannia Industries Ltd',    'BRITANNIA',  'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'low',    14.20,  1000000000000),
('Dabur India Ltd',             'DABUR',      'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'low',    11.80,   900000000000),
('Marico Ltd',                  'MARICO',     'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'low',    13.50,   800000000000),
('Godrej Consumer Products Ltd','GODREJCP',   'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'medium', 15.80,  1300000000000),
('Colgate-Palmolive India Ltd', 'COLPAL',     'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'low',    14.20,   550000000000),
('Emami Ltd',                   'EMAMILTD',   'NSE & BSE', 'fmcg',    'FMCG & Consumer', 'medium', 12.50,   350000000000),

-- ══════════════════════════════════════════════════════════════
--  AUTOMOBILE  (9 stocks)
-- ══════════════════════════════════════════════════════════════
('Maruti Suzuki India Ltd',     'MARUTI',     'NSE & BSE', 'auto',    'Automobile', 'low',    14.50,  3600000000000),
('Tata Motors Ltd',             'TATAMOTORS', 'NSE & BSE', 'auto',    'Automobile', 'medium', 28.50,  3200000000000),
('Mahindra and Mahindra Ltd',   'M&M',        'NSE & BSE', 'auto',    'Automobile', 'medium', 32.10,  4000000000000),
('Hero MotoCorp Ltd',           'HEROMOTOCO', 'NSE & BSE', 'auto',    'Automobile', 'medium', 10.80,   900000000000),
('Bajaj Auto Ltd',              'BAJAJ-AUTO', 'NSE & BSE', 'auto',    'Automobile', 'low',    20.30,  2600000000000),
('Eicher Motors Ltd',           'EICHERMOT',  'NSE & BSE', 'auto',    'Automobile', 'medium', 22.50,  1200000000000),
('TVS Motor Company Ltd',       'TVSMOTOR',   'NSE & BSE', 'auto',    'Automobile', 'medium', 25.80,  1800000000000),
('Bharat Forge Ltd',            'BHARATFORG', 'NSE & BSE', 'auto',    'Automobile', 'high',   18.20,   350000000000),
('MRF Ltd',                     'MRF',        'NSE & BSE', 'auto',    'Automobile', 'low',    12.50,   950000000000),

-- ══════════════════════════════════════════════════════════════
--  ENERGY & POWER  (9 stocks)
-- ══════════════════════════════════════════════════════════════
('Reliance Industries Ltd',     'RELIANCE',   'NSE & BSE', 'energy',  'Energy & Power', 'low',    14.20, 19000000000000),
('Oil & Natural Gas Corp',      'ONGC',       'NSE & BSE', 'energy',  'Energy & Power', 'medium', 12.50,  3600000000000),
('Bharat Petroleum Corp Ltd',   'BPCL',       'NSE & BSE', 'energy',  'Energy & Power', 'medium', 18.50,  1600000000000),
('NTPC Ltd',                    'NTPC',       'NSE & BSE', 'energy',  'Energy & Power', 'low',    14.80,  3600000000000),
('Tata Power Company Ltd',      'TATAPOWER',  'NSE & BSE', 'energy',  'Energy & Power', 'medium', 28.50,  1400000000000),
('Coal India Ltd',              'COALINDIA',  'NSE & BSE', 'energy',  'Energy & Power', 'low',    20.30,  2600000000000),
('Power Grid Corp of India',    'POWERGRID',  'NSE & BSE', 'energy',  'Energy & Power', 'low',    12.80,  2800000000000),
('Adani Green Energy Ltd',      'ADANIGREEN', 'NSE & BSE', 'energy',  'Energy & Power', 'high',   35.20,  2000000000000),
('GAIL India Ltd',              'GAIL',       'NSE & BSE', 'energy',  'Energy & Power', 'medium', 10.50,  1300000000000),

-- ══════════════════════════════════════════════════════════════
--  INFRASTRUCTURE & DEFENCE  (6 stocks)
-- ══════════════════════════════════════════════════════════════
('Larsen and Toubro Ltd',       'LT',        'NSE & BSE', 'infra',   'Infrastructure & Defence', 'low',    18.50,  5500000000000),
('Adani Enterprises Ltd',       'ADANIENT',  'NSE & BSE', 'infra',   'Infrastructure & Defence', 'high',   45.20,  3000000000000),
('Adani Ports and SEZ Ltd',     'ADANIPORTS','NSE & BSE', 'infra',   'Infrastructure & Defence', 'medium', 22.50,  3000000000000),
('Bharat Electronics Ltd',      'BEL',       'NSE & BSE', 'infra',   'Infrastructure & Defence', 'medium', 28.50,  2200000000000),
('HAL Hindustan Aeronautics',   'HAL',       'NSE & BSE', 'infra',   'Infrastructure & Defence', 'medium', 32.10,  2500000000000),
('IRB Infrastructure Developers','IRB',      'NSE & BSE', 'infra',   'Infrastructure & Defence', 'high',   15.80,   250000000000),

-- ══════════════════════════════════════════════════════════════
--  REAL ESTATE  (5 stocks)
-- ══════════════════════════════════════════════════════════════
('DLF Ltd',                     'DLF',        'NSE & BSE', 'realty',  'Real Estate', 'medium', 22.50,  1800000000000),
('Godrej Properties Ltd',       'GODREJPROP', 'NSE & BSE', 'realty',  'Real Estate', 'medium', 28.50,   850000000000),
('Macrotech Developers Ltd',    'LODHA',      'NSE & BSE', 'realty',  'Real Estate', 'medium', 18.50,  1200000000000),
('Oberoi Realty Ltd',           'OBEROIRLTY', 'NSE & BSE', 'realty',  'Real Estate', 'medium', 20.30,   600000000000),
('Prestige Estates Projects',   'PRESTIGE',   'NSE & BSE', 'realty',  'Real Estate', 'high',   35.80,   600000000000),

-- ══════════════════════════════════════════════════════════════
--  TELECOM & MEDIA  (5 stocks)
-- ══════════════════════════════════════════════════════════════
('Bharti Airtel Ltd',           'BHARTIARTL', 'NSE & BSE', 'telecom', 'Telecom & Media', 'low',    22.50,  9000000000000),
('Vodafone Idea Ltd',           'IDEA',       'NSE & BSE', 'telecom', 'Telecom & Media', 'high',    5.20,   250000000000),
('Indus Towers Ltd',            'INDUSTOWER', 'NSE & BSE', 'telecom', 'Telecom & Media', 'medium', 12.50,   900000000000),
('Info Edge India Ltd',         'NAUKRI',     'NSE & BSE', 'telecom', 'Telecom & Media', 'medium', 18.80,   750000000000),
('Tata Communications Ltd',     'TATACOMM',   'NSE & BSE', 'telecom', 'Telecom & Media', 'medium', 15.50,   550000000000),

-- ══════════════════════════════════════════════════════════════
--  DIVERSIFIED / FINANCIAL SERVICES  (6 stocks)
-- ══════════════════════════════════════════════════════════════
('Bajaj Finance Ltd',           'BAJFINANCE', 'NSE & BSE', 'diversified','Diversified & Finance', 'low',    28.50,  5000000000000),
('Bajaj Finserv Ltd',           'BAJAJFINSV', 'NSE & BSE', 'diversified','Diversified & Finance', 'medium', 18.50,  2800000000000),
('Asian Paints Ltd',            'ASIANPAINT', 'NSE & BSE', 'diversified','Diversified & Finance', 'low',    14.50,  2100000000000),
('Havells India Ltd',           'HAVELLS',    'NSE & BSE', 'diversified','Diversified & Finance', 'medium', 18.20,   900000000000),
('Pidilite Industries Ltd',     'PIDILITIND', 'NSE & BSE', 'diversified','Diversified & Finance', 'low',    18.80,  1500000000000),
('Zomato Ltd',                  'ZOMATO',     'NSE & BSE', 'diversified','Diversified & Finance', 'high',   38.50,  2200000000000),

-- ══════════════════════════════════════════════════════════════
--  ETF / INDEX FUNDS  (10 entries)
--  Popular ETFs listed on NSE / BSE for SIP investors
-- ══════════════════════════════════════════════════════════════
('SBI Nifty 50 ETF',            'SETFNIF50',  'NSE',       'etf',     'ETF & Index Funds', 'low',    13.50,   NULL),
('Nippon India ETF Nifty BeES', 'NIFTYBEES',  'NSE',       'etf',     'ETF & Index Funds', 'low',    13.60,   NULL),
('Nippon India Gold ETF',       'GOLDBEES',   'NSE',       'etf',     'ETF & Index Funds', 'low',    10.20,   NULL),
('ICICI Prudential Silver ETF', 'SILVRETF',   'NSE',       'etf',     'ETF & Index Funds', 'medium', 14.50,   NULL),
('UTI Nifty 50 ETF',            'UTINIFTETF', 'NSE',       'etf',     'ETF & Index Funds', 'low',    13.40,   NULL),
('Kotak Nifty Bank ETF',        'KOTAKBKETF', 'NSE',       'etf',     'ETF & Index Funds', 'medium', 12.80,   NULL),
('HDFC Nifty 50 ETF',           'HDFCNIFETF', 'NSE',       'etf',     'ETF & Index Funds', 'low',    13.55,   NULL),
('Mirae Asset Nifty Midcap 150','MAFSETFMID', 'NSE',       'etf',     'ETF & Index Funds', 'medium', 18.90,   NULL),
('Nippon India Silver ETF',     'SILVERBEES', 'NSE',       'etf',     'ETF & Index Funds', 'medium', 14.20,   NULL),
('Motilal Oswal Nasdaq 100 ETF','MOM100',     'NSE',       'etf',     'ETF & Index Funds', 'high',   22.50,   NULL);


-- ============================================================
--  SEED: sip_plan  (one plan per company = 111 plans)
--  Duration logic:
--    low risk    -> 10 years  (wealth preservation)
--    medium risk -> 5 years   (balanced growth)
--    high risk   -> 3 years   (aggressive growth)
--  Min investment logic:
--    market_cap >= 1 Lakh Cr  -> Rs 1000/month
--    market_cap < 1 Lakh Cr   -> Rs 500/month
--    ETF (market_cap IS NULL) -> Rs 500/month
-- ============================================================
INSERT INTO sip_plan
    (company_id, sip_name, metal_type, min_investment, risk_level, expected_return, duration_years)
SELECT
    c.company_id,
    CONCAT(c.company_name, ' - Monthly SIP'),
    c.metal_type,
    CASE
        WHEN c.market_cap >= 1000000000000 THEN 1000.00
        ELSE 500.00
    END,
    c.risk_level,
    c.avg_return_5y,
    CASE
        WHEN c.risk_level = 'low'    THEN 10
        WHEN c.risk_level = 'medium' THEN  5
        ELSE                               3
    END
FROM company c;


-- ============================================================
--  SEED: market_news
-- ============================================================
INSERT INTO market_news (title, description, source, news_url, published_at) VALUES
('Gold prices surge on Fed rate cut expectations',
 'Gold crossed Rs 94,000 per 10g amid global uncertainty and dovish Fed outlook.',
 'Economic Times', 'https://economictimes.indiatimes.com/markets/commodities/news', NOW()),

('Hindustan Zinc Q4: Silver output up 8% YoY',
 'India largest zinc-silver miner reported record silver production of 760 tonnes in Q4 FY26.',
 'Mint', 'https://www.livemint.com/market/commodities', NOW()),

('Titan posts 22% revenue growth on jewellery demand',
 'Titan jewellery business grew 22% YoY in Q4 FY26, aided by strong gold demand in wedding season.',
 'Business Standard', 'https://www.business-standard.com/markets/commodities', NOW()),

('Nifty 50 hits all-time high of 27,500 in April 2026',
 'Broad-based rally driven by strong FII inflows, IT earnings beat and cooling inflation.',
 'NDTV Profit', 'https://www.ndtvprofit.com/markets', NOW()),

('TCS and Infosys report better-than-expected Q4 results',
 'India top two IT majors beat estimates thanks to deal wins in BFSI and healthcare verticals.',
 'Reuters', 'https://www.reuters.com/markets/commodities', NOW()),

('Platinum demand from EV hydrogen fuel cells to drive 2026 prices',
 'Analysts forecast 12% uptick in platinum demand as hydrogen fuel cell adoption accelerates.',
 'Financial Times', 'https://www.ft.com/commodities', NOW()),

('Silver ETFs see record inflows as industrial demand outpaces supply',
 'Silver ETF AUM crosses Rs 12,000 Cr in India as solar panel and EV battery demand keeps supply tight.',
 'Financial Express', 'https://www.financialexpress.com/market/commodities/', NOW()),

('HDFC Bank Q4 profit jumps 18% to Rs 17,600 Cr',
 'HDFC Bank reported net profit of Rs 17,616 Cr for Q4 FY26, beating analyst estimates by 4%.',
 'Bloomberg', 'https://www.bloomberg.com/markets/commodities', NOW()),

('Reliance Industries enters green hydrogen with Rs 75,000 Cr investment',
 'RIL announced its largest-ever green energy capex, targeting 5 GW of clean hydrogen capacity by 2028.',
 'Business Line', 'https://www.thehindubusinessline.com/markets/commodities/', NOW()),

('Bharti Airtel 5G subscriber base crosses 100 million in India',
 'Airtel reaches 100 million 5G subscribers milestone, expanding to 1,200 cities across India.',
 'Mint', 'https://www.livemint.com/industry/telecom', NOW());


-- ============================================================
--  VERIFY
-- ============================================================
SELECT 'users'       AS tbl, COUNT(*) AS row_count FROM users
UNION ALL SELECT 'metal_price',  COUNT(*) FROM metal_price
UNION ALL SELECT 'company',      COUNT(*) FROM company
UNION ALL SELECT 'sip_plan',     COUNT(*) FROM sip_plan
UNION ALL SELECT 'alerts',       COUNT(*) FROM alerts
UNION ALL SELECT 'market_news',  COUNT(*) FROM market_news;

-- Sector breakdown
SELECT metal_type AS sector, sector_label, COUNT(*) AS stocks
FROM company GROUP BY metal_type, sector_label ORDER BY metal_type;

-- ============================================================
--  DONE -- Run: python app.py
-- ============================================================
