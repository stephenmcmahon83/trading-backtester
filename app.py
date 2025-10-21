from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Get API key from environment variable
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')

# Configure for production
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

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
        
        # Calculate date range (last 365 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Convert to Unix timestamps
        end_timestamp = int(end_date.timestamp())
        start_timestamp = int(start_date.timestamp())
        
        # Finnhub API endpoint
        url = f'https://finnhub.io/api/v1/stock/candle'
        params = {
            'symbol': symbol,
            'resolution': 'D',
            'from': start_timestamp,
            'to': end_timestamp,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('s') == 'no_data':
                return jsonify({'error': 'No data found for this symbol'}), 404
            
            # Format the data
            formatted_data = []
            for i in range(len(result['t'])):
                formatted_data.append({
                    'date': datetime.fromtimestamp(result['t'][i]).strftime('%Y-%m-%d'),
                    'open': round(result['o'][i], 2),
                    'high': round(result['h'][i], 2),
                    'low': round(result['l'][i], 2),
                    'close': round(result['c'][i], 2),
                    'volume': result['v'][i]
                })
            
            return jsonify({
                'symbol': symbol,
                'data': formatted_data
            })
        else:
            return jsonify({'error': 'Failed to fetch data from Finnhub'}), 500
            
    except requests.Timeout:
        return jsonify({'error': 'Request timeout - please try again'}), 504
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': 'An error occurred'}), 500

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # Only for local development
    app.run(debug=True, port=5000)