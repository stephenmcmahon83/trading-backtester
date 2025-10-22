from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(DATABASE_URL)

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
        
        # Get years parameter (default 1 year)
        years = int(data.get('years', 1))
        if years > 20:
            years = 20  # Cap at 20 years
        
        app.logger.info(f'Fetching {years} years of data for {symbol} from database')
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query data
        cursor.execute("""
            SELECT date, open, high, low, close, volume
            FROM stock_data
            WHERE symbol = %s
            ORDER BY date DESC
            LIMIT %s
        """, (symbol, years * 365))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            return jsonify({'error': f'No data found for {symbol}. Available symbols: AAPL, MSFT, GOOGL, TSLA, AMZN, META, NVDA, SPY, QQQ, DIA'}), 404
        
        # Format data
        formatted_data = []
        for row in rows:
            formatted_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
        
        app.logger.info(f'Successfully fetched {len(formatted_data)} days of data')
        
        return jsonify({
            'symbol': symbol,
            'data': formatted_data
        })
            
    except Exception as e:
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/available-symbols', methods=['GET'])
def get_available_symbols():
    """Return list of available symbols"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT symbol, name, last_updated, total_days
            FROM symbols
            ORDER BY symbol
        """)
        
        symbols = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'symbols': symbols})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)