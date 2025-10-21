from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError as e:
    YFINANCE_AVAILABLE = False
    print(f"WARNING: yfinance not available: {e}")

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stock-data', methods=['POST'])
def get_stock_data():
    try:
        if not YFINANCE_AVAILABLE:
            return jsonify({'error': 'Stock data service temporarily unavailable.'}), 503
        
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        app.logger.info(f'Requesting data for {symbol}')
        
        # Calculate date range (last 365 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Create ticker with custom session to add headers
        import requests
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Fetch data from Yahoo Finance with custom session
        ticker = yf.Ticker(symbol, session=session)
        hist = ticker.history(start=start_date, end=end_date)
        
        # Check if data exists
        if hist.empty:
            app.logger.warning(f'No data found for {symbol}')
            return jsonify({'error': f'No data found for {symbol}. Try: AAPL, MSFT, GOOGL, TSLA'}), 404
        
        # Format the data
        formatted_data = []
        for date, row in hist.iterrows():
            formatted_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume'])
            })
        
        # Sort by date descending (newest first)
        formatted_data.reverse()
        
        app.logger.info(f'Successfully fetched {len(formatted_data)} days of data for {symbol}')
        
        return jsonify({
            'symbol': symbol,
            'data': formatted_data
        })
            
    except Exception as e:
        app.logger.error(f'Error fetching data for {symbol}: {str(e)}')
        return jsonify({'error': f'Failed to fetch data. Please try again.'}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'yfinance_available': YFINANCE_AVAILABLE
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)