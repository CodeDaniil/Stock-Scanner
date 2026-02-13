from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import os
from database import get_all_alerts, get_ticker_alerts, get_unique_tickers, init_db

app = Flask(__name__)
MARKET_TZ = pytz.timezone('US/Eastern')

# Initialize database on startup
init_db()

def format_timestamp(ts_string):
    """Format timestamp for display"""
    if not ts_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts_string)
        return dt.strftime('%m/%d/%Y %I:%M %p')
    except:
        return ts_string

@app.route('/')
def dashboard():
    """Main dashboard - list all alerts"""
    alerts = get_all_alerts()
    
    # Format data for display
    for alert in alerts:
        alert['timestamp_formatted'] = format_timestamp(alert['timestamp'])
    
    return render_template('dashboard.html', alerts=alerts)

@app.route('/ticker/<ticker>')
def ticker_detail(ticker):
    """Ticker detail page - show history for one ticker"""
    alerts = get_ticker_alerts(ticker)
    
    # Format data
    for alert in alerts:
        alert['timestamp_formatted'] = format_timestamp(alert['timestamp'])
    
    return render_template('ticker_detail.html', ticker=ticker, alerts=alerts)

@app.route('/api/latest')
def api_latest():
    """API endpoint for real-time updates"""
    alerts = get_all_alerts()[:10]  # Last 10 alerts
    
    for alert in alerts:
        alert['timestamp_formatted'] = format_timestamp(alert['timestamp'])
    
    return jsonify(alerts)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
