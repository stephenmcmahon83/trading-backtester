import yfinance as yf
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

# EXPANDED SYMBOLS LIST - Add as many as you want!
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

def populate_stock_data(symbol, years=None):
    """
    Fetch and store historical data for a symbol
    If years=None, gets ALL available data
    """
    if years:
        print(f"\nFetching {years} years of data for {symbol}...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
    else:
        print(f"\nFetching ALL available data for {symbol}...")
        # Set start_date to far in the past to get all data
        start_date = datetime(1970, 1, 1)  # Gets everything Yahoo has
        end_date = datetime.now()
    
    try:
        # Fetch data from Yahoo Finance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            print(f"❌ No data found for {symbol}")
            return False
        
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Insert data
        inserted = 0
        skipped = 0
        for date, row in hist.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO stock_data (symbol, date, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, date) DO NOTHING
                """, (
                    symbol,
                    date.strftime('%Y-%m-%d'),
                    round(float(row['Open']), 2),
                    round(float(row['High']), 2),
                    round(float(row['Low']), 2),
                    round(float(row['Close']), 2),
                    int(row['Volume'])
                ))
                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"Error inserting data for {date}: {e}")
                continue
        
        # Update symbols table
        cursor.execute("""
            INSERT INTO symbols (symbol, name, last_updated, total_days)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE SET
                last_updated = EXCLUDED.last_updated,
                total_days = EXCLUDED.total_days
        """, (symbol, ticker.info.get('longName', symbol), datetime.now(), len(hist)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Inserted {inserted} new days, skipped {skipped} existing days for {symbol}")
        print(f"   Total data range: {hist.index[0].strftime('%Y-%m-%d')} to {hist.index[-1].strftime('%Y-%m-%d')}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {symbol}: {e}")
        return False

def main():
    print("=" * 60)
    print("Stock Data Population Script - MAXIMUM HISTORICAL DATA")
    print("=" * 60)
    print(f"Symbols to populate: {len(SYMBOLS)}")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"\n[{i}/{len(SYMBOLS)}] Processing {symbol}...")
        if populate_stock_data(symbol, years=None):  # None = ALL data
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully populated: {success_count} symbols")
    print(f"❌ Failed: {fail_count} symbols")
    print("=" * 60)

if __name__ == '__main__':
    main()