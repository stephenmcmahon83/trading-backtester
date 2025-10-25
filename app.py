from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(DATABASE_URL)

def calculate_and_merge_analytics(data_list):
    """
    Calculates daily indicators with new rounding and threshold highlighting.
    """
    if len(data_list) < 2:
        return data_list 

    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date', ascending=True)

    # --- Calculate RSI(2) using Wilder's Smoothing (EMA) ---
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    period = 2
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['rsi_2'] = 100 - (100 / (1 + rs))

    # --- Calculate Simple Moving Averages of the RSI(2) ---
    df['rsi_2_avg_5'] = df['rsi_2'].rolling(window=5).mean()
    df['rsi_2_avg_10'] = df['rsi_2'].rolling(window=10).mean()

    # --- NEW: Round all RSI values to the nearest whole number ---
    for col in ['rsi_2', 'rsi_2_avg_5', 'rsi_2_avg_10']:
        df[col] = df[col].round(0)

    # --- NEW: Apply threshold-based highlighting for every day ---
    # 5-Day Average Highlighting
    conditions_5 = [df['rsi_2_avg_5'] >= 90, df['rsi_2_avg_5'] <= 10]
    choices_5 = ['red', 'green']
    df['highlight_5_day'] = np.select(conditions_5, choices_5, default='none')

    # 10-Day Average Highlighting
    conditions_10 = [df['rsi_2_avg_10'] >= 85, df['rsi_2_avg_10'] <= 15]
    choices_10 = ['red', 'green']
    df['highlight_10_day'] = np.select(conditions_10, choices_10, default='none')

    # --- Format Data for JSON response ---
    # Use pandas' nullable integer type to handle potential NaNs after rounding
    for col in ['rsi_2', 'rsi_2_avg_5', 'rsi_2_avg_10']:
         df[col] = df[col].astype('Int64')
    
    df.replace({pd.NA: None, np.nan: None}, inplace=True)
    df = df.sort_values(by='date', ascending=False)
    
    return df.to_dict('records')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stock-data', methods=['POST'])
def get_stock_data():
    """Fetch all stock data, calculate daily analytics, and return merged data"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT date, open, high, low, close, volume FROM stock_data WHERE symbol = %s ORDER BY date DESC", (symbol,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            return jsonify({'error': f'No data found for {symbol}.'}), 404
        
        formatted_data = [{'date': r['date'].strftime('%Y-%m-%d'), 'open': float(r['open']), 'high': float(r['high']), 'low': float(r['low']), 'close': float(r['close']), 'volume': int(r['volume'])} for r in rows]
        
        # Calculate and merge the analytics into the data list
        data_with_analytics = calculate_and_merge_analytics(formatted_data)
        
        return jsonify({
            'symbol': symbol,
            'data': data_with_analytics # The 'data' key now contains everything
        })
            
    except Exception as e:
        print(f'[API] Error: {str(e)}')
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# The rest of your file (get_available_symbols, health, __main__) remains the same...
@app.route('/api/available-symbols', methods=['GET'])
def get_available_symbols():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT DISTINCT symbol, COUNT(*) as total_days, MIN(date) as first_date, MAX(date) as last_date FROM stock_data GROUP BY symbol ORDER BY symbol")
        symbols = cursor.fetchall()
        cursor.close()
        conn.close()
        formatted_symbols = [{'symbol': sym['symbol'], 'total_days': sym['total_days'], 'first_date': sym['first_date'].strftime('%Y-%m-%d') if sym['first_date'] else None, 'last_date': sym['last_date'].strftime('%Y-%m-%d') if sym['last_date'] else None} for sym in symbols]
        return jsonify({'symbols': formatted_symbols})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM stock_data')
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected', 'total_records': count}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)