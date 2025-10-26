from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import pandas_market_calendars as mcal

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

DATABASE_URL = os.getenv('DATABASE_URL')

# === HELPER FUNCTIONS ===

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(DATABASE_URL)

def calculate_and_merge_analytics(data_list):
    """
    Calculates RSI(2) and moving averages for the historical data page.
    """
    if len(data_list) < 2:
        return data_list 

    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date', ascending=True)

    # Calculate RSI(2) using Wilder's Smoothing (EMA)
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    period = 2
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['rsi_2'] = 100 - (100 / (1 + rs))

    # Calculate Simple Moving Averages of the RSI(2)
    df['rsi_2_avg_5'] = df['rsi_2'].rolling(window=5).mean()
    df['rsi_2_avg_10'] = df['rsi_2'].rolling(window=10).mean()

    # Round all RSI values to the nearest whole number
    for col in ['rsi_2', 'rsi_2_avg_5', 'rsi_2_avg_10']:
        df[col] = df[col].round(0)

    # Apply threshold-based highlighting for every day
    conditions_5 = [df['rsi_2_avg_5'] >= 90, df['rsi_2_avg_5'] <= 10]
    choices_5 = ['red', 'green']
    df['highlight_5_day'] = np.select(conditions_5, choices_5, default='none')

    conditions_10 = [df['rsi_2_avg_10'] >= 85, df['rsi_2_avg_10'] <= 15]
    choices_10 = ['red', 'green']
    df['highlight_10_day'] = np.select(conditions_10, choices_10, default='none')
    
    for col in ['rsi_2', 'rsi_2_avg_5', 'rsi_2_avg_10']:
         df[col] = df[col].astype('Int64')
    
    df.replace({pd.NA: None, np.nan: None}, inplace=True)
    df = df.sort_values(by='date', ascending=False)
    
    return df.to_dict('records')
# --- CORRECTED Helper function for Seasonal Tendencies ---
def calculate_seasonal_tendencies(data_list):
    """
    Performs a seasonal backtest on historical data.
    (Corrected version to ensure all 251 days are shown)
    """
    if not data_list:
        return []

    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date', ascending=True).reset_index(drop=True)

    df['trading_day_num'] = df.groupby(df['date'].dt.year).cumcount() + 1

    hold_periods = range(1, 16)
    for n in hold_periods:
        df[f'fwd_ret_{n}d'] = (df['open'].shift(-n) - df['open']) / df['open']

    agg_dict = {}
    for n in hold_periods:
        col_name = f'fwd_ret_{n}d'
        agg_dict[f'avg_ret_{n}d'] = pd.NamedAgg(column=col_name, aggfunc='mean')
        agg_dict[f'win_rate_{n}d'] = pd.NamedAgg(column=col_name, aggfunc=lambda x: (x > 0).mean())
    agg_dict['trade_count'] = pd.NamedAgg(column='date', aggfunc='count')

    seasonal_stats = df.groupby('trading_day_num').agg(**agg_dict)
    
    # --- THIS IS THE CORRECTED LOGIC BLOCK ---
    
    # 1. Convert stats to a dictionary for fast lookups
    stats_dict = seasonal_stats.to_dict('index')

    # 2. Generate the full, correct 2025 trading calendar
    target_year = 2025
    nyse = mcal.get_calendar('NYSE')
    schedule = nyse.schedule(start_date=f'{target_year}-01-01', end_date=f'{target_year}-12-31')
    
    results = []
    # 3. Loop through the correct 2025 calendar (all 251 days)
    for i, date in enumerate(schedule.index):
        day_num = i + 1
        date_str = date.strftime('%b %d, %Y')
        
        # 4. Look up the stats for this day number. If it exists, use it.
        if day_num in stats_dict:
            row = stats_dict[day_num]
            results.append({
                'date': date_str,
                'tradingDayNum': day_num,
                'tradeCount': int(row['trade_count']),
                'avgReturns': [row[f'avg_ret_{n}d'] for n in hold_periods],
                'winRates': [row[f'win_rate_{n}d'] for n in hold_periods]
            })
        else:
            # 5. If no historical stats exist, create a placeholder row
            results.append({
                'date': date_str,
                'tradingDayNum': day_num,
                'tradeCount': 0,
                'avgReturns': [0] * len(hold_periods), # Fill with zeros
                'winRates': [0] * len(hold_periods)    # Fill with zeros
            })
            
    return results

# === PAGE ROUTES ===
@app.route('/')
def index():
    """Serves the home page."""
    return render_template('index.html')

@app.route('/historical-data')
def historical_data():
    """Serves the data analysis tool page."""
    return render_template('historical_data.html')

# --- NEW: Route for the Seasonal Tendencies page ---
@app.route('/seasonal-tendencies')
def seasonal_tendencies_page():
    """Serves the seasonal tendencies analysis page."""
    return render_template('seasonal-tendencies.html')


# === API ROUTES ===

# --- NEW: API route for Seasonal Data calculation ---
@app.route('/api/seasonal-data', methods=['GET'])
def get_seasonal_data():
    """
    API endpoint to fetch data and calculate seasonal tendencies.
    """
    try:
        symbol = request.args.get('symbol', 'SPY').upper()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT date, open FROM stock_data WHERE symbol = %s ORDER BY date ASC", (symbol,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            return jsonify({'error': f'No data found for {symbol}.'}), 404
            
        formatted_data = [{'date': r['date'], 'open': float(r['open'])} for r in rows]
        seasonal_results = calculate_seasonal_tendencies(formatted_data)
        
        return jsonify(seasonal_results)
            
    except Exception as e:
        print(f'[API Seasonal] Error: {str(e)}')
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/stock-data', methods=['POST'])
def get_stock_data():
    """API endpoint to fetch all stock data and calculate RSI analytics."""
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
        
        data_with_analytics = calculate_and_merge_analytics(formatted_data)
        
        return jsonify({
            'symbol': symbol,
            'data': data_with_analytics
        })
            
    except Exception as e:
        print(f'[API Stock Data] Error: {str(e)}')
        return jsonify({'error': f'Server error: {str(e)}'}), 500

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