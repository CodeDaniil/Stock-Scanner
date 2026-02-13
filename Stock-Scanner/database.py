import sqlite3
from datetime import datetime
import pytz

MARKET_TZ = pytz.timezone('US/Eastern')

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ticker TEXT NOT NULL,
                  price REAL NOT NULL,
                  gain REAL NOT NULL,
                  ema5 REAL NOT NULL,
                  ema9 REAL NOT NULL,
                  vwap REAL NOT NULL,
                  volume INTEGER NOT NULL,
                  rel_volume INTEGER NOT NULL,
                  free_float INTEGER NOT NULL,
                  news_headline TEXT,
                  news_url TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def add_alert(ticker, price, gain, ema5, ema9, vwap, volume, rel_volume, free_float, news_headline=None, news_url=None):
    """Add alert to database"""
    try:
        conn = sqlite3.connect('alerts.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO alerts 
                     (ticker, price, gain, ema5, ema9, vwap, volume, rel_volume, free_float, news_headline, news_url)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (ticker, price, gain, ema5, ema9, vwap, volume, rel_volume, free_float, news_headline, news_url))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding alert to database: {e}")
        return False

def get_all_alerts():
    """Get all alerts ordered by most recent"""
    try:
        conn = sqlite3.connect('alerts.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''SELECT * FROM alerts ORDER BY timestamp DESC''')
        alerts = c.fetchall()
        conn.close()
        
        return [dict(alert) for alert in alerts]
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []

def get_ticker_alerts(ticker):
    """Get all alerts for a specific ticker"""
    try:
        conn = sqlite3.connect('alerts.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''SELECT * FROM alerts WHERE ticker = ? ORDER BY timestamp DESC''', (ticker,))
        alerts = c.fetchall()
        conn.close()
        
        return [dict(alert) for alert in alerts]
    except Exception as e:
        print(f"Error fetching ticker alerts: {e}")
        return []

def get_unique_tickers():
    """Get list of all unique tickers that have alerts"""
    try:
        conn = sqlite3.connect('alerts.db')
        c = conn.cursor()
        
        c.execute('''SELECT DISTINCT ticker FROM alerts ORDER BY ticker''')
        tickers = [row[0] for row in c.fetchall()]
        conn.close()
        
        return tickers
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return []
