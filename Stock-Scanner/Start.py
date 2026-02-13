import yfinance as yf
import pandas as pd
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import schedule
from datetime import datetime, timedelta
import pytz
from config import (
    FINNHUB_API_KEY,
    GMAIL_EMAIL,
    GMAIL_PASSWORD,
    SCAN_INTERVAL,
    MIN_GAIN_PERCENT,
    MIN_FREE_FLOAT,
    MIN_VOLUME_MULTIPLIER
)

# Market timezone
MARKET_TZ = pytz.timezone('US/Eastern')

class StockScanner:
    def __init__(self):
        self.scanned_tickers = set()  # Track already notified stocks
        
    def get_top_gainers(self):
        """Fetch top gainers from Finnhub API"""
        try:
            url = f"https://finnhub.io/api/v1/stock/market-movers?exchange=US&token={FINNHUB_API_KEY}"
            response = requests.get(url)
            data = response.json()
            
            if 'topGainers' in data:
                # Extract ticker symbols from top gainers
                gainers = [item['symbol'] for item in data['topGainers'][:20]]  # Top 20 gainers
                print(f"📈 Found top gainers: {', '.join(gainers)}")
                return gainers
            else:
                print("⚠️ Could not fetch top gainers")
                return []
        except Exception as e:
            print(f"❌ Error fetching gainers: {e}")
            return []
    
    def get_intraday_data(self, ticker, interval='5m'):
        """Fetch 5-min and 10-min candle data"""
        try:
            # Get last 2 days of 5-min data
            data = yf.download(ticker, interval=interval, period='2d', progress=False)
            return data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def calculate_ema(self, data, period):
        """Calculate EMA"""
        return data['Close'].ewm(span=period, adjust=False).mean()
    
    def calculate_vwap(self, data):
        """Calculate VWAP (Volume Weighted Average Price)"""
        data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
        data['CumVP'] = data['TP'] * data['Volume']
        data['CumV'] = data['Volume'].cumsum()
        data['VWAP'] = data['CumVP'].cumsum() / data['CumV']
        return data['VWAP']
    
    def get_free_float(self, ticker):
        """Get free float from Finnhub API"""
        try:
            url = f"https://finnhub.io/api/v1/company-basic-financials?symbol={ticker}&token={FINNHUB_API_KEY}"
            response = requests.get(url)
            data = response.json()
            
            # Free float shares
            if 'metric' in data and 'sharesOutstanding' in data['metric']:
                return data['metric']['sharesOutstanding']
            return None
        except Exception as e:
            print(f"Error fetching free float for {ticker}: {e}")
            return None
    
    def get_relative_volume(self, ticker):
        """Get 20-day average volume"""
        try:
            data = yf.download(ticker, period='20d', progress=False)
            return data['Volume'].mean()
        except Exception as e:
            print(f"Error fetching volume for {ticker}: {e}")
            return None
    
    def get_sec_news(self, ticker):
        """Get recent SEC news"""
        try:
            url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&limit=3&token={FINNHUB_API_KEY}"
            response = requests.get(url)
            news = response.json()
            return news[:1] if news else []  # Return most recent
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return []
    
    def check_criteria(self, ticker):
        """Check if ticker meets all criteria"""
        try:
            # Get current price and gain %
            stock = yf.Ticker(ticker)
            info = stock.info
            
            current_price = info.get('currentPrice')
            prev_close = info.get('previousClose')
            
            if not current_price or not prev_close:
                return False, None
            
            gain_percent = ((current_price - prev_close) / prev_close) * 100
            
            if gain_percent < MIN_GAIN_PERCENT:
                return False, None
            
            # Get intraday data
            data_5m = self.get_intraday_data(ticker, '5m')
            if data_5m is None or len(data_5m) < 20:
                return False, None
            
            # Calculate indicators
            ema5 = self.calculate_ema(data_5m, 5)
            ema9 = self.calculate_ema(data_5m, 9)
            vwap = self.calculate_vwap(data_5m)
            
            latest_price = data_5m['Close'].iloc[-1]
            latest_ema5 = ema5.iloc[-1]
            latest_ema9 = ema9.iloc[-1]
            latest_vwap = vwap.iloc[-1]
            latest_volume = data_5m['Volume'].iloc[-1]
            
            # Check EMA crossover (EMA5 above EMA9)
            ema_crossover = latest_ema5 > latest_ema9
            
            # Check volume
            rel_volume = self.get_relative_volume(ticker)
            volume_check = rel_volume and latest_volume >= (rel_volume * MIN_VOLUME_MULTIPLIER)
            
            # Check free float
            free_float = self.get_free_float(ticker)
            free_float_check = free_float and free_float < MIN_FREE_FLOAT
            
            if ema_crossover and volume_check and free_float_check:
                return True, {
                    'ticker': ticker,
                    'price': latest_price,
                    'gain': gain_percent,
                    'ema5': latest_ema5,
                    'ema9': latest_ema9,
                    'vwap': latest_vwap,
                    'volume': latest_volume,
                    'rel_volume': rel_volume,
                    'free_float': free_float
                }
            
            return False, None
            
        except Exception as e:
            print(f"Error checking criteria for {ticker}: {e}")
            return False, None
    
    def send_email(self, ticker, data):
        """Send email notification"""
        try:
            subject = f"🔔 ALERT: {ticker} - EMA Cross + Volume Spike!"
            
            news = self.get_sec_news(ticker)
            news_link = f"<a href='{news[0]['url']}'>{news[0]['headline']}</a>" if news else "No recent news"
            
            body = f"""
            <html>
            <body>
            <h2>Stock Alert: {ticker}</h2>
            <p><b>Price:</b> ${data['price']:.2f}</p>
            <p><b>Gain:</b> {data['gain']:.2f}%</p>
            <hr>
            <h3>Technical Indicators:</h3>
            <ul>
                <li><b>EMA5:</b> ${data['ema5']:.2f}</li>
                <li><b>EMA9:</b> ${data['ema9']:.2f}</li>
                <li><b>VWAP:</b> ${data['vwap']:.2f}</li>
            </ul>
            <hr>
            <h3>Volume:</h3>
            <ul>
                <li><b>Current:</b> {int(data['volume']):,}</li>
                <li><b>Relative (20d avg):</b> {int(data['rel_volume']):,}</li>
                <li><b>Multiplier:</b> {data['volume']/data['rel_volume']:.2f}x</li>
            </ul>
            <hr>
            <h3>Fundamentals:</h3>
            <ul>
                <li><b>Free Float:</b> {int(data['free_float']):,} shares</li>
            </ul>
            <hr>
            <h3>Latest News:</h3>
            <p>{news_link}</p>
            <p><small>Scanned at {datetime.now(MARKET_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}</small></p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = GMAIL_EMAIL
            msg['To'] = GMAIL_EMAIL
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Email sent for {ticker}")
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
    
    def scan(self):
        """Main scan function"""
        now = datetime.now(MARKET_TZ)
        
        # Check if market is open (9:30 AM - 4:00 PM ET, Mon-Fri)
        if now.weekday() >= 5:  # Weekend
            print(f"Market closed (Weekend) - {now.strftime('%H:%M:%S')}")
            return
        
        if now.time() < pd.Timestamp("09:30").time() or now.time() > pd.Timestamp("16:00").time():
            print(f"Market closed - {now.strftime('%H:%M:%S')}")
            return
        
        print(f"\n📊 Scan started at {now.strftime('%H:%M:%S')}")
        
        # Get top gainers automatically
        tickers = self.get_top_gainers()
        
        if not tickers:
            print("⚠️ No tickers to scan")
            return
        
        for ticker in tickers:
            try:
                meets_criteria, data = self.check_criteria(ticker)
                
                if meets_criteria and ticker not in self.scanned_tickers:
                    print(f"🎯 {ticker} meets criteria!")
                    self.send_email(ticker, data)
                    self.scanned_tickers.add(ticker)
                elif meets_criteria:
                    print(f"✓ {ticker} still active (already notified)")
                    
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
        
        # Reset scanned tickers every 4 hours (allow re-notification)
        if len(self.scanned_tickers) > 0 and now.hour % 4 == 0:
            self.scanned_tickers.clear()
            print("🔄 Resetting alert cache")

def main():
    scanner = StockScanner()
    
    print("🚀 Stock Scanner Started!")
    print(f"Scanning every {SCAN_INTERVAL} minutes")
    print(f"Criteria: >{MIN_GAIN_PERCENT}% gain, EMA5>EMA9, Vol>{MIN_VOLUME_MULTIPLIER}x rel vol, Free Float<{MIN_FREE_FLOAT/1_000_000}M")
    print("-" * 50)
    
    # Schedule scan
    schedule.every(SCAN_INTERVAL).minutes.do(scanner.scan)
    
    # Run scanner
    try:
        while True:
            schedule.run_pending()
            time.sleep(10)  # Check every 10 seconds if scan is due
    except KeyboardInterrupt:
        print("\n⛔ Scanner stopped by user")

if __name__ == "__main__":
    main()
