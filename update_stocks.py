"""
Daily stock data updater for Supabase
Updates last 7 days for all symbols with detailed logging
"""
import yfinance as yf
import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

SYMBOLS = [
    # Tech Giants
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AMD', 'INTC', 'CRM', 'ORCL', 'CSCO',
    
    # Finance
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA', 'PYPL', 'AXP',
    
    # Leveraged/ETF
    'TQQQ', 'SPXL', 'SOXL', 'SOXX', 'IBB', 'LABU', 'XLE', 'GUSH', 'GLD', 'GDX','NUGT','JNUG', 'FXI','XPP','KWEB','CWEB','EWG','EWU','EWZ','TLT','FANG',
    
    # Consumer
    'WMT', 'HD', 'DIS', 'NKE', 'MCD', 'SBUX', 'KO', 'PEP', 'COST', 'TGT',
    
    # Energy
    'XOM', 'CVX', 'COP', 'SLB', 'EOG',
    
    # ETFs (Most Popular)
    'SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'VTI', 'EEM', 'AGG',
    
    # Add your own here!
]

def check_latest_date_in_db(symbol, conn):
    """Check what's the latest date we have for this symbol"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(date) 
        FROM stock_data 
        WHERE symbol = %s
    """, (symbol,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result and result[0] else None

def update_symbol(symbol, conn):
    """Update last 7 days of data for a symbol"""
    try:
        # Check latest date in database
        latest_db_date = check_latest_date_in_db(symbol, conn)
        
        # Fetch recent data from Yahoo
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)  # Get 10 days to be safe
        
        print(f"\n{symbol}:")
        print(f"  📅 Latest in DB: {latest_db_date}")
        print(f"  📥 Fetching: {start_date.date()} to {end_date.date()}")
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            print(f"  ⚠️  No data from Yahoo Finance")
            return 0, f"{symbol}: No data available"
        
        print(f"  📊 Yahoo returned {len(hist)} days")
        
        # Show what dates we got
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
        print(f"  📆 Dates: {', '.join(dates[-5:])}")  # Show last 5 dates
        
        cursor = conn.cursor()
        inserted = 0
        updated = 0
        
        for date, row in hist.iterrows():
            date_str = date.strftime('%Y-%m-%d')
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
                    date_str,
                    round(float(row['Open']), 2),
                    round(float(row['High']), 2),
                    round(float(row['Low']), 2),
                    round(float(row['Close']), 2),
                    int(row['Volume'])
                ))
                
                result = cursor.fetchone()
                if result and result[0]:
                    inserted += 1
                    print(f"  ✅ Inserted: {date_str}")
                else:
                    updated += 1
                    print(f"  🔄 Updated: {date_str}")
                    
            except Exception as e:
                print(f"  ❌ Error on {date_str}: {e}")
                continue
        
        # Update symbols table
        cursor.execute("""
            UPDATE symbols 
            SET last_updated = %s
            WHERE symbol = %s
        """, (datetime.now(), symbol))
        
        conn.commit()
        cursor.close()
        
        return inserted + updated, f"{symbol}: {inserted} new, {updated} updated"
        
    except Exception as e:
        return 0, f"{symbol}: ERROR - {str(e)}"

def main():
    print(f"\n{'='*70}")
    print(f"📊 Stock Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not set!")
        return
    
    print(f"\n🔗 Connecting to database...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connected to Supabase\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    print(f"{'='*70}")
    
    total_updated = 0
    
    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"\n[{i}/5] Processing {symbol}...")
        count, message = update_symbol(symbol, conn)
        total_updated += count
    
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"✅ Total records processed: {total_updated}")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()