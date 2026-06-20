"""
Fetch the complete symbol list directly from TradingView's screener.
This gets all ~8000+ stocks in the Indian market as seen on:
https://in.tradingview.com/markets/stocks-india/market-movers-all-stocks/
"""
import os
import sys
from tradingview_screener import Query

# ── Add the tradingview-mcp src to path ────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COINLIST_DIR = os.path.join(SCRIPT_DIR, "src", "tradingview_mcp", "coinlist")
os.makedirs(COINLIST_DIR, exist_ok=True)

def fetch_and_save_all_symbols():
    print("Fetching all India market symbols from TradingView...")
    
    # Query all symbols from the 'india' market
    # No limit, we want all of them
    q = Query().select('name', 'exchange').set_markets('india')
    
    # By default limit might be 50. We need to fetch all rows.
    # The get_scanner_data() returns count and dataframe.
    count, df = q.get_scanner_data()
    
    if count > 0 and len(df) < count:
        print(f"Paginating to fetch all {count} symbols...")
        # Since get_scanner_data limit is 50, we set limit to count
        q.limit(count)
        count, df = q.get_scanner_data()
        
    print(f"Fetched {len(df)} total stocks from TradingView India market.")
    
    nse_symbols = []
    bse_symbols = []
    other_exchanges = set()
    
    for _, row in df.iterrows():
        ticker = row.get("name", "")
        # Format usually is EXCHANGE:SYMBOL or just SYMBOL depending on the screener
        # If the 'exchange' field is present, we can use it, otherwise we check the name
        
        exchange = str(row.get("exchange", "")).upper()
        if not exchange and ":" in ticker:
            exchange = ticker.split(":")[0].upper()
            sym = ticker.split(":")[1]
        elif ":" in ticker:
            sym = ticker.split(":")[1]
        else:
            sym = ticker
            
        if exchange == "NSE":
            nse_symbols.append(sym)
        elif exchange == "BSE":
            bse_symbols.append(sym)
        else:
            other_exchanges.add(exchange)
            
    print(f"Found {len(nse_symbols)} NSE stocks and {len(bse_symbols)} BSE stocks.")
    if other_exchanges:
        print(f"Other exchanges found (ignored): {other_exchanges}")
        
    # Write NSE symbols
    nse_path = os.path.join(COINLIST_DIR, "nse.txt")
    with open(nse_path, "w", newline="\r\n") as f:
        for sym in sorted(set(nse_symbols)):
            f.write(f"NSE:{sym}\r\n")
            
    # Write BSE symbols
    bse_path = os.path.join(COINLIST_DIR, "bse.txt")
    with open(bse_path, "w", newline="\r\n") as f:
        for sym in sorted(set(bse_symbols)):
            f.write(f"BSE:{sym}\r\n")
            
    print(f"Successfully saved to {nse_path} and {bse_path}")

if __name__ == "__main__":
    fetch_and_save_all_symbols()
