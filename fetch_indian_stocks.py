"""
═══════════════════════════════════════════════════════════════════════════════
  Indian Stock Market Data Fetcher
  Technical + Fundamental Data from TradingView & Screener.in
═══════════════════════════════════════════════════════════════════════════════

Fetches comprehensive technical and fundamental data for ALL Indian stocks 
(NSE + BSE) and saves to CSV + JSON files.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
import traceback
import glob
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ── Add the tradingview-mcp src to path ────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "src"))

# ── TradingView imports ────────────────────────────────────────────────────────
try:
    import tradingview_ta
    from tradingview_ta import TA_Handler, Interval
    # Try importing the batched version from the mcp repo if possible
    try:
        from tradingview_mcp.core.services.screener_provider import resilient_get_multiple_analysis as get_multiple_analysis
    except ImportError:
        from tradingview_ta import get_multiple_analysis
    TV_TA_AVAILABLE = True
except ImportError:
    TV_TA_AVAILABLE = False
    print("WARNING: tradingview_ta not installed. Technical data will be limited.")

try:
    from tradingview_screener import Query
    from tradingview_screener.column import Column
    TV_SCREENER_AVAILABLE = True
except ImportError:
    TV_SCREENER_AVAILABLE = False
    print("WARNING: tradingview_screener not installed. Screener data will be limited.")


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All timeframes supported by TradingView (Skipped 5m, 15m, 1h, 4h as requested)
ALL_TIMEFRAMES = ["1D", "1W", "1M"]

# TradingView interval mapping
TV_INTERVAL_MAP = {
    "5m": Interval.INTERVAL_5_MINUTES if TV_TA_AVAILABLE else None,
    "15m": Interval.INTERVAL_15_MINUTES if TV_TA_AVAILABLE else None,
    "1h": Interval.INTERVAL_1_HOUR if TV_TA_AVAILABLE else None,
    "1D": Interval.INTERVAL_1_DAY if TV_TA_AVAILABLE else None,
    "1W": Interval.INTERVAL_1_WEEK if TV_TA_AVAILABLE else None,
    "1M": Interval.INTERVAL_1_MONTH if TV_TA_AVAILABLE else None,
}

# Rate limiting
REQUEST_DELAY = 3.0  # seconds between TradingView requests
BATCH_SIZE = 50      # symbols per batch for tradingview_ta
SCREENER_IN_DELAY = 0.5  # seconds between screener.in requests

# Headers for web scraping
WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# ══════════════════════════════════════════════════════════════════════════════
# SYMBOL LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_symbols(exchange: str) -> List[str]:
    """Load symbols from coinlist file."""
    coinlist_dir = os.path.join(SCRIPT_DIR, "src", "tradingview_mcp", "coinlist")
    filepath = os.path.join(coinlist_dir, f"{exchange.lower()}.txt")
    
    if not os.path.exists(filepath):
        print(f"ERROR: Symbol list not found: {filepath}")
        return []
    
    symbols = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                # Format is EXCHANGE:SYMBOL, we want just SYMBOL
                if ":" in line:
                    symbols.append(line.split(":", 1)[1])
                else:
                    symbols.append(line)
    
    return symbols


# ══════════════════════════════════════════════════════════════════════════════
# SCREENER.IN FUNDAMENTAL DATA FETCHER (PRIORITY SOURCE)
# ══════════════════════════════════════════════════════════════════════════════

class ScreenerInFetcher:
    """Fetch fundamental data from screener.in (Indian stock screener)."""
    
    BASE_URL = "https://www.screener.in"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(WEB_HEADERS)
    
    def fetch_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.BASE_URL}/company/{symbol}/consolidated/"
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 404:
                url = f"{self.BASE_URL}/company/{symbol}/"
                resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            return self._parse_company_page(resp.text, symbol)
        except Exception as e:
            return None
    
    def _parse_company_page(self, html: str, symbol: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        data = {"symbol": symbol, "source": "screener.in"}
        try:
            name_tag = soup.select_one("h1.margin-0")
            if name_tag:
                data["company_name"] = name_tag.get_text(strip=True)
            ratios_list = soup.select("#top-ratios li")
            for li in ratios_list:
                name_span = li.select_one(".name")
                value_span = li.select_one(".value, .number")
                if name_span and value_span:
                    name = name_span.get_text(strip=True).lower()
                    value = value_span.get_text(strip=True)
                    if "market cap" in name: data["market_cap_cr"] = self._parse_number(value)
                    elif "current price" in name: data["current_price"] = self._parse_number(value)
                    elif "stock p/e" in name or "p/e" in name: data["pe_ratio"] = self._parse_number(value)
                    elif "book value" in name: data["book_value"] = self._parse_number(value)
                    elif "dividend yield" in name: data["dividend_yield"] = self._parse_number(value)
                    elif "roce" in name: data["roce"] = self._parse_number(value)
                    elif "roe" in name: data["roe"] = self._parse_number(value)
                    elif "eps" in name: data["eps"] = self._parse_number(value)
        except Exception as e:
            data["parse_error"] = str(e)
        return data
    
    @staticmethod
    def _parse_number(text: str) -> Optional[float]:
        if not text: return None
        try:
            cleaned = text.replace("₹", "").replace(",", "").replace("%", "").strip()
            if cleaned in ("", "-", "N/A", "NA"): return None
            multiplier = 1
            if cleaned.upper().endswith("CR"): cleaned = cleaned[:-2].strip()
            return float(cleaned) * multiplier
        except (ValueError, TypeError):
            return None
    
    def fetch_bulk_screener_data(self, symbols: List[str], progress_callback=None) -> Dict[str, Dict]:
        results = {}
        total = len(symbols)
        for i, symbol in enumerate(symbols):
            if progress_callback: progress_callback(i + 1, total, symbol)
            data = self.fetch_stock_data(symbol)
            if data: results[symbol] = data
            if i < total - 1: time.sleep(SCREENER_IN_DELAY)
        return results


# ══════════════════════════════════════════════════════════════════════════════
# TRADINGVIEW FUNDAMENTAL DATA FETCHER
# ══════════════════════════════════════════════════════════════════════════════

class TradingViewFundamentalFetcher:
    FUNDAMENTAL_COLUMNS = [
        "name", "description", "type", "subtype",
        "market_cap_basic", "price_earnings_ttm", "earnings_per_share_basic_ttm",
        "price_book_fq", "price_sales_ratio", "dividend_yield_recent",
        "return_on_equity", "debt_to_equity", "total_revenue",
        "net_income", "gross_margin", "operating_margin",
        "sector", "industry",
    ]
    
    def fetch_india_stocks(self, exchange: str = "NSE") -> List[Dict[str, Any]]:
        if not TV_SCREENER_AVAILABLE: return []
        try:
            q = Query().select(*self.FUNDAMENTAL_COLUMNS).set_markets("india")
            count, df = q.get_scanner_data()
            if count > 0 and len(df) < count:
                q.limit(count)
                count, df = q.get_scanner_data()
            if df is not None and not df.empty:
                results = []
                for _, row in df.iterrows():
                    ticker = row.get("name", "")
                    if ticker and (f"{exchange}:" in str(ticker) or exchange.upper() in str(ticker).upper()):
                        record = row.to_dict()
                        record["exchange"] = exchange
                        record["source"] = "tradingview"
                        results.append(record)
                if not results:
                    for _, row in df.iterrows():
                        record = row.to_dict()
                        record["exchange"] = exchange
                        record["source"] = "tradingview"
                        results.append(record)
                return results
            return []
        except Exception as e:
            print(f"  TradingView screener error: {e}")
            return []


# ══════════════════════════════════════════════════════════════════════════════
# TRADINGVIEW TECHNICAL DATA FETCHER
# ══════════════════════════════════════════════════════════════════════════════

class TradingViewTechnicalFetcher:
    INDICATOR_KEYS = [
        "SMA10", "SMA20", "SMA50", "SMA100", "SMA200",
        "EMA10", "EMA20", "EMA50", "EMA100", "EMA200",
        "RSI", "MACD.macd", "MACD.signal", "Stoch.K", "Stoch.D",
        "ADX", "CCI20", "W.R", "BB.upper", "BB.lower",
        "open", "close", "high", "low", "volume",
        "change", "ATR", "P.SAR"
    ]
    
    def fetch_batch_technical(self, symbols: List[str], exchange: str, timeframe: str,
                               progress_callback=None) -> List[Dict[str, Any]]:
        if not TV_TA_AVAILABLE or not symbols:
            return []
            
        interval = timeframe
        if timeframe == '1D': interval = '1d'
        elif timeframe == '1W': interval = '1W'
        elif timeframe == '1M': interval = '1M'
            
        results = []
        total = len(symbols)
        tv_symbols = [f"{exchange.upper()}:{sym}" for sym in symbols]
        
        for i in range(0, total, BATCH_SIZE):
            batch = tv_symbols[i:i+BATCH_SIZE]
            if progress_callback:
                progress_callback(min(i + BATCH_SIZE, total), total, f"Batch {i//BATCH_SIZE + 1}", timeframe)
            
            success = False
            attempts = 0
            while not success and attempts < 10:
                try:
                    analysis_dict = get_multiple_analysis(screener="india", interval=interval, symbols=batch)
                    for key, analysis in analysis_dict.items():
                        if analysis is None: continue
                        raw_sym = key.split(":")[1] if ":" in key else key
                        result = {
                            "symbol": raw_sym,
                            "exchange": exchange,
                            "timeframe": timeframe,
                            "timestamp": datetime.now().isoformat(),
                        }
                        if analysis.indicators:
                            for ind_key in self.INDICATOR_KEYS:
                                result[f"ind_{ind_key}"] = analysis.indicators.get(ind_key)
                        if analysis.summary:
                            result["recommendation"] = analysis.summary.get("RECOMMENDATION", "")
                            result["buy_signals"] = analysis.summary.get("BUY", 0)
                            result["sell_signals"] = analysis.summary.get("SELL", 0)
                            result["neutral_signals"] = analysis.summary.get("NEUTRAL", 0)
                        results.append(result)
                    success = True
                except Exception as e:
                    attempts += 1
                    print(f"\\n  ⚠️ Batch error for {exchange} {timeframe} (Attempt {attempts}/10): {e}")
                    print("  💤 Sleeping 60s to let TradingView API recover...")
                    time.sleep(60)
            time.sleep(REQUEST_DELAY)
        return results


# ══════════════════════════════════════════════════════════════════════════════
# MAIN DATA FETCHER - ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def print_progress(current, total, symbol, extra=""):
    pct = current / total * 100
    bar_len = 30
    filled = int(bar_len * current / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  [{bar}] {pct:5.1f}% ({current}/{total}) {symbol:20s} {extra}", end="", flush=True)


def fetch_all_indian_stocks(limit=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 70)
    print("  INDIAN STOCK MARKET DATA FETCHER")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print("\n📋 Loading symbol lists...")
    nse_symbols = load_symbols("nse")
    bse_symbols = load_symbols("bse")
    all_nse_symbols = sorted(set(nse_symbols))
    bse_only_symbols = sorted(set(bse_symbols) - set(nse_symbols))
    
    if limit:
        all_nse_symbols = all_nse_symbols[:limit]
        bse_only_symbols = bse_only_symbols[:limit]
    
    print(f"  NSE stocks: {len(all_nse_symbols)}")
    print(f"  BSE-only stocks: {len(bse_only_symbols)}")
    print(f"  Total unique stocks: {len(all_nse_symbols) + len(bse_only_symbols)}")
    
    # ══════════════════════════════════════════════════════════════════════
    # CHECK FOR EXISTING FUNDAMENTAL DATA TO RESUME
    # ══════════════════════════════════════════════════════════════════════
    merged_fundamental = {}
    existing_fund_files = glob.glob(os.path.join(OUTPUT_DIR, "indian_stocks_fundamental_*.json"))
    if existing_fund_files:
        latest_file = max(existing_fund_files, key=os.path.getctime)
        print(f"\n✅ Found existing fundamental data: {latest_file}")
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                merged_fundamental = json.load(f)
            print(f"  Loaded fundamental data for {len(merged_fundamental)} stocks. Skipping Phase 1-3.")
        except Exception as e:
            print(f"  Failed to load existing data: {e}")
            merged_fundamental = {}
            
    if not merged_fundamental:
        print("\n" + "=" * 70)
        print("  PHASE 1: Fundamental Data from screener.in")
        print("=" * 70)
        screener = ScreenerInFetcher()
        fundamental_data = {}
        test_symbols = all_nse_symbols[:5]
        print(f"\n🧪 Testing screener.in with {len(test_symbols)} stocks...")
        for sym in test_symbols:
            data = screener.fetch_stock_data(sym)
            if data and len(data) > 2:
                fundamental_data[sym] = data
                print(f"  ✅ {sym}: Got {len(data)} fields")
            else:
                print(f"  ⚠️  {sym}: No data or blocked")
            time.sleep(SCREENER_IN_DELAY)
        
        if len(fundamental_data) == 0:
            print("\n⚠️  screener.in appears to be blocking requests or unavailable.")
        else:
            print(f"\n✅ screener.in working! Fetching remaining {len(all_nse_symbols) - 5} stocks...")
            remaining = [s for s in all_nse_symbols[5:]]
            def screener_progress(current, total, symbol):
                print_progress(current + 5, len(all_nse_symbols), symbol, "screener.in")
            remaining_data = screener.fetch_bulk_screener_data(remaining, screener_progress)
            fundamental_data.update(remaining_data)
        
        print("\n" + "=" * 70)
        print("  PHASE 2: Fundamental Data from TradingView Screener")
        print("=" * 70)
        tv_fundamental = TradingViewFundamentalFetcher()
        tv_nse_data = tv_fundamental.fetch_india_stocks("NSE")
        tv_bse_data = tv_fundamental.fetch_india_stocks("BSE")
        tv_fundamental_data = {}
        for record in tv_nse_data + tv_bse_data:
            ticker = record.get("name", "")
            sym = str(ticker).split(":")[-1] if ":" in str(ticker) else str(ticker)
            tv_fundamental_data[sym] = record
        
        print("\n" + "=" * 70)
        print("  PHASE 3: Merging Fundamental Data")
        print("=" * 70)
        all_symbols = sorted(set(all_nse_symbols + bse_only_symbols))
        for sym in all_symbols:
            record = {"symbol": sym}
            if sym in fundamental_data:
                record.update(fundamental_data[sym])
                record["fundamental_source"] = "screener.in"
            if sym in tv_fundamental_data:
                tv_data = tv_fundamental_data[sym]
                for key, value in tv_data.items():
                    if key not in record or record[key] is None:
                        record[key] = value
            record["exchange"] = "NSE" if sym in nse_symbols else "BSE"
            merged_fundamental[sym] = record
        
        save_fundamental_data(merged_fundamental, timestamp)
    
    # ══════════════════════════════════════════════════════════════════════
    # PHASE 4: TECHNICAL DATA FROM TRADINGVIEW (ALL TIMEFRAMES)
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  PHASE 4: Technical Data from TradingView (All Timeframes)")
    print("=" * 70)
    
    tech_fetcher = TradingViewTechnicalFetcher()
    for tf in ALL_TIMEFRAMES:
        print(f"\n⏱️  Fetching {tf} timeframe data...")
        def tech_progress(current, total, symbol, timeframe):
            print_progress(current, total, symbol, f"[{timeframe}]")
        
        nse_tech = tech_fetcher.fetch_batch_technical(all_nse_symbols, "NSE", tf, tech_progress)
        bse_tech = tech_fetcher.fetch_batch_technical(bse_only_symbols, "BSE", tf, tech_progress)
        all_tech = nse_tech + bse_tech
        save_technical_data(all_tech, tf, timestamp)
    
    print("\n" + "=" * 70)
    print("  PHASE 5: Creating Combined Master Dataset")
    print("=" * 70)
    create_combined_dataset(merged_fundamental, timestamp)
    
    print("\n" + "=" * 70)
    print("  ✅ ALL DONE!")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("=" * 70)


def save_fundamental_data(data: Dict[str, Dict], timestamp: str):
    if not data: return
    json_path = os.path.join(OUTPUT_DIR, f"indian_stocks_fundamental_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    csv_path = os.path.join(OUTPUT_DIR, f"indian_stocks_fundamental_{timestamp}.csv")
    df = pd.DataFrame.from_dict(data, orient="index")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

def save_technical_data(data: List[Dict], timeframe: str, timestamp: str):
    if not data: return
    json_path = os.path.join(OUTPUT_DIR, f"indian_stocks_technical_{timeframe}_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    csv_path = os.path.join(OUTPUT_DIR, f"indian_stocks_technical_{timeframe}_{timestamp}.csv")
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

def create_combined_dataset(fundamental: Dict[str, Dict], timestamp: str):
    daily_tech_path = os.path.join(OUTPUT_DIR, f"indian_stocks_technical_1D_{timestamp}.json")
    daily_tech = {}
    if os.path.exists(daily_tech_path):
        with open(daily_tech_path, "r") as f:
            for record in json.load(f):
                if record.get("symbol"): daily_tech[record["symbol"]] = record
                
    combined = {}
    all_symbols = sorted(set(list(fundamental.keys()) + list(daily_tech.keys())))
    for sym in all_symbols:
        record = {"symbol": sym}
        if sym in fundamental:
            for k, v in fundamental[sym].items(): record[f"fund_{k}"] = v
        if sym in daily_tech:
            for k, v in daily_tech[sym].items():
                if k not in ("symbol", "exchange"): record[f"tech_{k}"] = v
        combined[sym] = record
        
    json_path = os.path.join(OUTPUT_DIR, f"indian_stocks_COMBINED_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, default=str, ensure_ascii=False)
    csv_path = os.path.join(OUTPUT_DIR, f"indian_stocks_COMBINED_{timestamp}.csv")
    df = pd.DataFrame.from_dict(combined, orient="index")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Indian Stock Market Data")
    parser.add_argument("--test", action="store_true", help="Run with only 10 stocks for testing")
    args = parser.parse_args()
    
    if args.test:
        BATCH_SIZE = 5
        fetch_all_indian_stocks(limit=10)
    else:
        fetch_all_indian_stocks()
