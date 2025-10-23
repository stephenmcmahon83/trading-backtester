"""
Daily stock data updater for Supabase
Updates last 7 days for all symbols
"""
import yfinance as yf
import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# This will use the DATABASE_URL from Render environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC',
    'TQQQ', 'SPXL', 'SOXL', 'SPY', 'QQQ', 'DIA', 'JNUG', 'NUGT', 'GLD', 'GDX',
    'JPM', 'BAC', 'WFC', 'WMT', 'HD', 'DIS', 'XOM', 'CVX'
]

def update_symbol(symbol, conn):
    """Update last 7 days of data for a symbol"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            return 0, f"{symbol}: No new data"
        
        cursor = conn.cursor()
        inserted = 0
        updated = 0
        
        for date, row in hist.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO stock_data (symbol, date, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, date) 
                    DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                    RETURNING (xmax = 0) AS inserted
                """, (
                    symbol,
                    date.strftime('%Y-%m-%d'),
                    round(float(row['Open']), 2),
                    round(float(row['High']), 2),
                    round(float(row['Low']), 2),
                    round(float(row['Close']), 2),
                    int(row['Volume'])
                ))
                
                result = cursor.fetchone()
                if result and result[0]:
                    inserted += 1
                else:
                    updated += 1
                    
            except Exception as e:
                continue
        
        # Update symbols table
        cursor.execute("""
            UPDATE symbols 
            SET last_updated = %s
            WHERE symbol = %s
        """, (datetime.now(), symbol))
        
        conn.commit()
        cursor.close()
        
        return inserted + updated, f"✅ {symbol}: {inserted} new, {updated} updated"
        
    except Exception as e:
        return 0, f"❌ {symbol}: {str(e)}"

def main():
    print(f"\n{'='*60}")
    print(f"📊 Daily Stock Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not set!")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connected to Supabase\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    total_updated = 0
    
    for i, symbol in enumerate(SYMBOLS, 1):
        count, message = update_symbol(symbol, conn)
        total_updated += count
        print(f"[{i}/{len(SYMBOLS)}] {message}")
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Total records processed: {total_updated}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()