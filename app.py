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
    """Fetch stock data from DATABASE ONLY - NO Yahoo Finance!"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        print(f'[API] Fetching {symbol} from DATABASE')
        
        # Connect to Supabase database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query data from database
        cursor.execute("""
            SELECT date, open, high, low, close, volume
            FROM stock_data
            WHERE symbol = %s
            ORDER BY date DESC
        """, (symbol,))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            print(f'[API] No data found for {symbol}')
            return jsonify({
                'error': f'No data found for {symbol}. Available: AAPL, MSFT, GOOGL, TSLA, SPY, TQQQ'
            }), 404
        
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
        
        print(f'[API] Returning {len(formatted_data)} records for {symbol}')
        
        return jsonify({
            'symbol': symbol,
            'data': formatted_data
        })
            
    except Exception as e:
        print(f'[API] Error: {str(e)}')
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/available-symbols', methods=['GET'])
def get_available_symbols():
    """Return list of available symbols"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT DISTINCT symbol,
                   COUNT(*) as total_days,
                   MIN(date) as first_date,
                   MAX(date) as last_date
            FROM stock_data
            GROUP BY symbol
            ORDER BY symbol
        """)
        
        symbols = cursor.fetchall()
        cursor.close()
        conn.close()
        
        formatted_symbols = []
        for sym in symbols:
            formatted_symbols.append({
                'symbol': sym['symbol'],
                'total_days': sym['total_days'],
                'first_date': sym['first_date'].strftime('%Y-%m-%d') if sym['first_date'] else None,
                'last_date': sym['last_date'].strftime('%Y-%m-%d') if sym['last_date'] else None
            })
        
        return jsonify({'symbols': formatted_symbols})
    except Exception as e:
        print(f'[API] Error fetching symbols: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM stock_data')
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'total_records': count
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)