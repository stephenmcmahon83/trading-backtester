from flask import Flask, render_template, jsonify, request
import yfinance as yf
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stock-data', methods=['POST'])
def get_stock_data():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        app.logger.info(f'Requesting data for {symbol}')
        
        # Calculate date range (last 365 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Fetch data from Yahoo Finance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        # Check if data exists
        if hist.empty:
            app.logger.warning(f'No data found for {symbol}')
            return jsonify({'error': 'No data found for this symbol. Check if it\'s valid (e.g., AAPL, MSFT, GOOGL)'}), 404
        
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
        return jsonify({'error': f'Failed to fetch data. Please check the symbol and try again.'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)