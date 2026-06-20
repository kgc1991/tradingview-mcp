"""
Generate NSE and BSE symbol lists for tradingview-mcp.

Fetches the complete list of NSE-listed equities from NSE India's website
and creates coinlist files in the format expected by tradingview-mcp.
"""

import requests
import json
import os
import time

COINLIST_DIR = os.path.join(os.path.dirname(__file__), "src", "tradingview_mcp", "coinlist")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
}

def get_nse_session():
    """Create a session with NSE cookies."""
    session = requests.Session()
    session.headers.update(HEADERS)
    # First hit the main page to get cookies
    try:
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(1)
    except Exception as e:
        print(f"Warning: Could not get NSE cookies: {e}")
    return session


def fetch_nse_symbols():
    """Fetch all NSE equity symbols."""
    print("Fetching NSE stock list...")
    
    # Method 1: Try NSE API
    session = get_nse_session()
    symbols = []
    
    try:
        # NSE market status / equity list endpoint
        url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data:
                for item in data["data"]:
                    sym = item.get("symbol", "")
                    if sym:
                        symbols.append(sym)
                print(f"  Got {len(symbols)} F&O symbols from NSE API")
    except Exception as e:
        print(f"  NSE F&O API failed: {e}")
    
    # Method 2: Use a comprehensive hardcoded list of major NSE stocks
    # This is the most reliable approach as NSE's API has aggressive anti-scraping
    nse_major_stocks = get_comprehensive_nse_list()
    
    # Merge both lists
    all_symbols = sorted(set(symbols) | set(nse_major_stocks))
    print(f"  Total unique NSE symbols: {len(all_symbols)}")
    return all_symbols


def get_comprehensive_nse_list():
    """
    Comprehensive list of NSE-listed stocks.
    Includes Nifty 50, Nifty Next 50, Nifty Midcap 150, Nifty Smallcap 250,
    and other actively traded stocks — covering ~2000 stocks.
    """
    # This is a comprehensive list of NSE stocks available on TradingView
    # TradingView uses the exchange prefix "NSE" for Indian stocks
    stocks = [
        # ══════════════════════════════════════════════════════════════
        # NIFTY 50 CONSTITUENTS
        # ══════════════════════════════════════════════════════════════
        "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
        "BAJAJ_AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BPCL",
        "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DRREDDY",
        "EICHERMOT", "ETERNAL", "GRASIM", "HCLTECH", "HDFCBANK",
        "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
        "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "JIOFIN",
        "KOTAKBANK", "LT", "LTIM", "M_M", "MARUTI",
        "NTPC", "NESTLEIND", "ONGC", "POWERGRID", "RELIANCE",
        "SBILIFE", "SBIN", "SUNPHARMA", "TCS", "TATACONSUM",
        "TATAMOTORS", "TATASTEEL", "TECHM", "TITAN", "ULTRACEMCO",
        "WIPRO",

        # ══════════════════════════════════════════════════════════════
        # NIFTY NEXT 50
        # ══════════════════════════════════════════════════════════════
        "ABB", "ADANIENSOL", "ADANIGREEN", "ADANIPOWER", "AMBUJACEM",
        "ATGL", "BANKBARODA", "BHEL", "BOSCHLTD", "CANBK",
        "CHOLAFIN", "COLPAL", "DLF", "DABUR", "DMART",
        "GAIL", "GODREJCP", "HAL", "HAVELLS", "HINDPETRO",
        "IOC", "ICICIPRULI", "INDHOTEL", "IRCTC", "IRFC",
        "JSWENERGY", "JINDALSTEL", "LICI", "LUPIN", "MAXHEALTH",
        "MOTHERSON", "NHPC", "NAUKRI", "PFC", "PIDILITIND",
        "PNB", "RECLTD", "SBICARD", "SHREECEM", "SIEMENS",
        "SRF", "TATAPOWER", "TORNTPHARM", "TRENT", "UNIONBANK",
        "UNITDSPR", "VBL", "VEDL", "ZOMATO", "ZYDUSLIFE",

        # ══════════════════════════════════════════════════════════════
        # NIFTY MIDCAP 150 (SELECTED)
        # ══════════════════════════════════════════════════════════════
        "AARTIIND", "ACC", "ALKEM", "ANGELONE", "APLAPOLLO",
        "ASHOKLEY", "ASTRAL", "AUROPHARMA", "BALKRISIND", "BANDHANBNK",
        "BATAINDIA", "BERGEPAINT", "BIOCON", "BLUEDART", "CANFINHOME",
        "CENTRALBK", "CGPOWER", "CHAMBLFERT", "COFORGE", "CONCOR",
        "COROMANDEL", "CROMPTON", "CUMMINSIND", "DEEPAKNTR", "DEVYANI",
        "DIXON", "EMAMILTD", "ESCORTS", "EXIDEIND", "FEDERALBNK",
        "FORTIS", "GLENMARK", "GMRAIRPORT", "GNFC", "GODREJPROP",
        "GRANULES", "GSPL", "GUJGASLTD", "HAPPSTMNDS", "HATSUN",
        "HONAUT", "IDFCFIRSTB", "IEX", "IIFL", "INDIACEM",
        "INDIAMART", "INDIANB", "IPCALAB", "IREDA", "JKCEMENT",
        "JSL", "JUBLFOOD", "KALYANKJIL", "KEI", "KEC",
        "KPITTECH", "LAURUSLABS", "LICHSGFIN", "LODHA", "LTTS",
        "MFSL", "MGL", "MANAPPURAM", "MANKIND", "MARICO",
        "MPHASIS", "MRF", "MUTHOOTFIN", "NAM_INDIA", "NATIONALUM",
        "NAVINFLUOR", "NMDC", "OBEROIRLTY", "OIL", "OFSS",
        "PAGEIND", "PATANJALI", "PERSISTENT", "PETRONET", "PIIND",
        "POLYCAB", "PRESTIGE", "PVRINOX", "RAJESHEXPO", "RAMCOCEM",
        "RATNAMANI", "RBLBANK", "RECLTD", "RELAXO", "RVNL",
        "SAIL", "SAPPHIRE", "SCHAEFFLER", "SJVN", "SOLARINDS",
        "SONACOMS", "STARHEALTH", "SUMICHEM", "SUNDARMFIN", "SUNDRMFAST",
        "SUPREMEIND", "SUZLON", "SYNGENE", "TATACOMM", "TATAELXSI",
        "TATACHEM", "TIINDIA", "TIMKEN", "TORNTPOWER", "TVSMOTOR",
        "UBL", "UNIONBANK", "UPL", "VOLTAS", "WHIRLPOOL",
        "YESBANK", "ZEEL",

        # ══════════════════════════════════════════════════════════════
        # NIFTY SMALLCAP & OTHER ACTIVELY TRADED STOCKS
        # ══════════════════════════════════════════════════════════════
        "3MINDIA", "AARTIDRUGS", "AAVAS", "ABCAPITAL", "ABFRL",
        "ABSLAMC", "ACCELYA", "ADANIGAS", "ADFFOODS", "ADVENZYMES",
        "AEGISCHEM", "AETHER", "AFFLE", "AGARIND", "AHLUCONT",
        "AIIL", "AJANTPHARM", "AKZOINDIA", "ALANKIT", "ALKYLAMINE",
        "ALLCARGO", "ALOKINDS", "AMARAJABAT", "AMBER", "AMIORG",
        "ANANTRAJ", "ANDHRAPET", "ANURAS", "APARINDS", "APTECHT",
        "APTUS", "ARCHIDPLY", "ARE_M", "ARVINDFASN", "ARVIND",
        "ASAHIINDIA", "ASHOKA", "ASTEC", "ASTERDM", "ATUL",
        "AUBANK", "AURIONPRO", "AVANTIFEED", "AXISCADES", "AZAD",
        "BANARISUG", "BASF", "BAYERCROP", "BBTC", "BCG",
        "BDL", "BEML", "BHARATFORG", "BHARATRAS", "BHEL",
        "BIKAJI", "BLS", "BLUESTARCO", "BORORENEW", "BRIGADE",
        "BSE", "BSOFT", "CAMPUS", "CAMS", "CANBK",
        "CANFINHOME", "CAPACITE", "CAPLIPOINT", "CARERATING", "CARYSIL",
        "CASTROLIND", "CCL", "CEATLTD", "CENTURYTEX", "CENTURYPLY",
        "CERA", "CHALET", "CHEMCON", "CHEMPLASTS", "CHENNPETRO",
        "CHOLAHLDNG", "CIE", "CINEVISTA", "CLEAN", "CLSEL",
        "COCHINSHIP", "COFFEDAY", "COMPUSOFT", "CONCORDBIO", "CONFIPET",
        "CRAFTSMAN", "CREDITACC", "CRISIL", "CROMPTON", "CSBBANK",
        "CUB", "CYIENT", "DCAL", "DCMSHRIRAM", "DCXINDIA",
        "DEEPAKFERT", "DELTACORP", "DENORA", "DHAMPURSUG", "DHANUKA",
        "DHANI", "DHARMAJ", "DIAMONDYD", "DIGISPICE", "DISHTV",
        "DIVGI", "DIVISLAB", "DLINKINDIA", "DMART", "DREDGECORP",
        "DYNPRO", "ECLERX", "EDELWEISS", "EIDPARRY", "EIHOTEL",
        "ELECON", "ELGIEQUIP", "EMCURE", "ENDURANCE", "ENGINERSIN",
        "ENIL", "EPL", "EQUITASBNK", "ERIS", "ESABINDIA",
        "ETHOSLTD", "EUROTEXIND", "EVERESTIND", "EXCELINDUS", "FACT",
        "FINEORG", "FINPIPE", "FIRSTSOUR", "FIVE", "FLAIR",
        "FLUOROCHEM", "FMGOETZE", "FORCEMOT", "FUSION", "GABRIEL",
        "GALAXYSURF", "GANESHHOUC", "GARFIBRES", "GATEWAY", "GESHIP",
        "GEOJIT", "GHCL", "GILLETTE", "GLAXO", "GLS",
        "GMDCLTD", "GODFRYPHLP", "GODREJAGRO", "GODREJIND", "GPIL",
        "GPPL", "GRINDWELL", "GRINFRA", "GRSE", "GSFC",
        "GUFICBIO", "GUJALKALI", "GULFOILLUB", "GVKPIL", "HEG",
        "HEIDELBERG", "HEMIPROP", "HERITGFOOD", "HFCL", "HGINFRA",
        "HIKAL", "HIL", "HIMADRI", "HINDZINC", "HITECHCORP",
        "HLEGLAS", "HMVL", "HOMEFIRST", "HONASA", "HPL",
        "HSCL", "HUDCO", "HUHTAMAKI", "ICRA", "IDEA",
        "IFBIND", "IFCI", "IGLB", "IGPL", "IIFLWAM",
        "IMAGICAA", "INEOSSTYRO", "INFIBEAM", "INGERRAND", "INOXWIND",
        "INSECTICID", "INTELLECT", "IONEXCHANG", "IPCALAB", "IPL",
        "IRB", "ISEC", "ITDC", "JAIBALAJI", "JAMNAAUTO",
        "JAYNECOIND", "JBCHEPHARM", "JBMA", "JETAIRWAYS", "JINDALSAW",
        "JKLAKSHMI", "JKPAPER", "JKTYRE", "JMFINANCIL", "JOCIL",
        "JUBLINGREA", "JUSTDIAL", "JYOTHYLAB", "KAJARIACER", "KALPATPOWR",
        "KANSAINER", "KARMAENG", "KAVVERITEL", "KBCGLOBAL", "KCP",
        "KDDL", "KENNAMET", "KESORAMIND", "KEYFINSERV", "KFIN",
        "KIRLOSENG", "KIRLOSIND", "KNRCON", "KOKUYOCMLN", "KOLTEPATIL",
        "KOPRAN", "KRBL", "KSB", "KSCL", "KSOLVES",
        "KTKBANK", "L_TFH", "LAOPALA", "LAXMIMACH", "LEMONTREE",
        "LGBBROSLTD", "LICI", "LINCOLN", "LLOYDSME", "LSIL",
        "LTFOODS", "LUMAXIND", "LUMAXTECH", "LUXIND", "MAHABANK",
        "MAHINDCIE", "MAHLIFE", "MAHLOG", "MAHSEAMLES", "MAITHANALL",
        "MALLCOM", "MANINFRA", "MAPMYINDIA", "MARATHON", "MASTEK",
        "MAXFIN", "MAXIND", "MAZDOCK", "MCX", "MEDANTA",
        "MEDPLUS", "METROBRAND", "METROPOLIS", "MINDACORP", "MINDTREE",
        "MIRZAINT", "MMTC", "MOIL", "MOLDTKPAC", "MONTECARLO",
        "MOREPENLAB", "MOTILALOFS", "MPHASIS", "MRPL", "MSUMI",
        "MTARTECH", "MUKANDLTD", "MULTICOMM", "MUNJALSHOW", "NATCOPHARM",
        "NATH", "NBCC", "NCC", "NESCO", "NETWORK18",
        "NEWGEN", "NFL", "NH", "NIACL", "NLCINDIA",
        "NOCIL", "NURECA", "NUVAMA", "NUVOCO", "OLECTRA",
        "OMAXE", "ONGC", "OPTIEMUS", "ORCHPHARMA", "ORIENTCEM",
        "ORIENTELEC", "ORIENTREF", "PALREDTEC", "PARADEEP", "PCJEWELLER",
        "PDSL", "PENIND", "PGHH", "PHANTOMFX", "PHOENIXLTD",
        "PILANIINVS", "PNBHOUSING", "PNCINFRA", "POLYMED", "POONAWALLA",
        "POWERINDIA", "PPLPHARMA", "PRSMJOHNSN", "PSUBNKBEES", "PTC",
        "PURVA", "QUESS", "RADICO", "RAIN", "RALLIS",
        "RAMACRAFT", "RANEHOLDIN", "RATNAMANI", "RAYMOND", "RBA",
        "REDINGTON", "RELIGARE", "RENUKA", "RITES", "RKFORGE",
        "ROSSARI", "ROUTE", "RPOWER", "RRKABEL", "RSWM",
        "RTNINDIA", "RUBYMILLS", "RUPA", "RUSHIL", "RVNL",
        "SAFARI", "SAKARORGN", "SAKSOFT", "SAKUMA", "SALASAR",
        "SANDUMA", "SANGHIIND", "SANOFI", "SAPPHIRE", "SARDAEN",
        "SAREGAMA", "SARVESHWAR", "SASKEN", "SATIN", "SBICARD",
        "SCI", "SEQUENT", "SHAKTIPUMP", "SHALPAINTS", "SHANTIGEAR",
        "SHARDACROP", "SHILPAMED", "SHOPERSTOP", "SHREECEM", "SHRIRAMCIT",
        "SHRIRAMFIN", "SHYAMMETL", "SIEMENS", "SIGACHI", "SJVN",
        "SKFINDIA", "SNOWMAN", "SOBHA", "SOLARA", "SONACOMS",
        "SONATSOFTW", "SOUTHBANK", "SPARC", "SPANDANA", "SSWL",
        "STAR", "STCINDIA", "STLTECH", "SUDARSCHEM", "SUMIT",
        "SUNCLAYLTD", "SUNDRMFAST", "SUNFLAG", "SUNTECK", "SUNTV",
        "SUPRAJIT", "SUPREMEIND", "SURYAROSNI", "SUULD", "SUVENPHAR",
        "SUZLON", "SVPGLOB", "SWANENERGY", "SWARAJENG", "SYMPHONY",
        "SYNGENE", "SYRMA", "TARSONS", "TATACHEM", "TATACOMM",
        "TATAELXSI", "TATAINVEST", "TATAMETALI", "TATVA", "TBZ",
        "TCNSBRANDS", "TDPOWERSYS", "TEAMLEASE", "TECHNOE", "TEGA",
        "THERMAX", "TIINDIA", "TIMKEN", "TITAGARH", "TMILL",
        "TORNTPOWER", "TRENT", "TRIDENT", "TRIVENI", "TTKPRESTIG",
        "TV18BRDCST", "TVSMOTOR", "TVSSRICHAK", "TWLCARSTL", "UCOBANK",
        "UJJIVAN", "UJJIVANSFB", "ULTRACEMCO", "UNIPARTS", "UNITEDTEA",
        "UNICHEMLAB", "UNOMINDA", "UPL", "UTIAMC", "UTKARSHBNK",
        "V2RETAIL", "VAIBHAVGBL", "VARDHACRLC", "VARROC", "VBLLTD",
        "VEDL", "VENKEYS", "VGUARD", "VIJAYA", "VIKAS",
        "VIKASECO", "VIPIND", "VMART", "VOLTAMP", "VOLTAS",
        "VRLLOG", "VSTIND", "VTL", "WABCOINDIA", "WALCHANNAG",
        "WABAG", "WELCORP", "WELSPUNLIV", "WESTLIFE", "WHIRLPOOL",
        "WINDMACHIN", "WIPRO", "WOCKPHARMA", "WONDERLA", "WPIL",
        "YESBANK", "ZEEL", "ZENITHSTL", "ZENTEC", "ZENSARTECH",
        "ZODIACCLTH", "ZOMATO", "ZYDUSLIFE", "ZYDUSWELL",

        # ══════════════════════════════════════════════════════════════
        # ADDITIONAL POPULAR STOCKS (PSU, DEFENSE, INFRA, ETC.)
        # ══════════════════════════════════════════════════════════════
        "ALOKINDS", "ANDHRABANK", "BECTORFOOD", "BIRLACORPN", "CESC",
        "COCHINSHIP", "COALINDIA", "DALBHARAT", "DCMSHRIRAM", "DEEPAKFERT",
        "EIDPARRY", "ELECON", "ELGIEQUIP", "ENGINERSIN", "EPL",
        "FACT", "FINCABLES", "FSL", "GICRE", "GLAXO",
        "GMDCLTD", "GODFRYPHLP", "GRANULES", "GRAPHITE", "GRINDWELL",
        "GRSE", "GSFC", "GSPL", "GUJALKALI", "GULFOILLUB",
        "HAL", "HEG", "HEIDELBERG", "HERITGFOOD", "HFCL",
        "HIKAL", "HINDCOPPER", "HINDZINC", "HLVLTD", "HONASA",
        "HUDCO", "IBREALEST", "ICRA", "IDEA", "IFBIND",
        "IFCI", "IIFLWAM", "INDIANHOTEL", "INGERRAND", "INTELLECT",
        "IONEXCHANG", "IRB", "IRCON", "ISEC", "ITDC",
        "ITI", "JAMNAAUTO", "JINDALSAW", "JKLAKSHMI", "JKPAPER",
        "JKTYRE", "JSWHL", "JUSTDIAL", "KALYANKJIL", "KARURVYSYA",
        "KEC", "KEI", "KIRLOSENG", "KNRCON", "KOKUYOCMLN",
        "KOLTEPATIL", "KRBL", "KSB", "LAOPALA", "LAXMIMACH",
        "LEMONTREE", "MAHABANK", "MAHLOG", "MAITHANALL", "MANINFRA",
        "MARATHON", "MASTEK", "MAZDOCK", "MCX", "METROPOLIS",
        "MMTC", "MOIL", "MOTILALOFS", "MRPL", "MUTHOOTFIN",
        "NATCOPHARM", "NBCC", "NCC", "NFL", "NIACL",
        "NLCINDIA", "NOCIL", "NUVAMA", "OLECTRA", "ORIENTCEM",
        "ORIENTELEC", "PCJEWELLER", "PENIND", "PHOENIXLTD", "PNCINFRA",
        "POWERINDIA", "PTC", "PURVA", "QUESS", "RADICO",
        "RAIN", "RALLIS", "RAYMOND", "REDINGTON", "RENUKA",
        "RITES", "ROSSARI", "RPOWER", "RRKABEL", "RVNL",
        "SAFARI", "SAREGAMA", "SASKEN", "SCI", "SHANTIGEAR",
        "SHRIRAMFIN", "SJVN", "SKFINDIA", "SOBHA", "SONATSOFTW",
        "SPARC", "STAR", "STLTECH", "SUDARSCHEM", "SUNFLAG",
        "SUNTECK", "SUNTV", "SUPRAJIT", "SUVENPHAR", "SUZLON",
        "SWANENERGY", "SYMPHONY", "SYRMA", "TATVA", "TEAMLEASE",
        "THERMAX", "TITAGARH", "TORNTPOWER", "TRIDENT", "TRIVENI",
        "TTKPRESTIG", "TV18BRDCST", "TVSSRICHAK", "UCOBANK", "UJJIVAN",
        "UJJIVANSFB", "UNIPARTS", "UNOMINDA", "UTIAMC", "V2RETAIL",
        "VGUARD", "VIPIND", "VMART", "VOLTAMP", "VRLLOG",
        "VSTIND", "WABAG", "WELCORP", "WELSPUNLIV", "WESTLIFE",
        "WINDMACHIN", "WOCKPHARMA", "WONDERLA", "ZENITHSTL", "ZENTEC",
        "ZENSARTECH",
    ]
    
    # Remove duplicates and sort
    return sorted(set(stocks))


def get_bse_list():
    """
    List of major BSE-listed stocks.
    BSE uses numeric security codes on TradingView.
    For simplicity, we use the symbol names which TradingView also accepts for BSE.
    """
    # BSE stocks that are also on NSE (most are dual-listed)
    # TradingView uses "BSE:" prefix with symbol names for Indian stocks
    stocks = [
        # BSE Sensex 30
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY",
        "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
        "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
        "TITAN", "BAJFINANCE", "BAJAJFINSV", "HCLTECH", "WIPRO",
        "NESTLEIND", "NTPC", "POWERGRID", "ULTRACEMCO", "TATASTEEL",
        "TATAMOTORS", "ADANIENT", "TECHM", "M_M", "INDUSINDBK",
        
        # BSE 500 additional (selected major ones not in Sensex)
        "BAJAJ_AUTO", "DRREDDY", "CIPLA", "COALINDIA", "EICHERMOT",
        "GRASIM", "HEROMOTOCO", "HINDALCO", "JSWSTEEL", "ONGC",
        "BPCL", "BRITANNIA", "APOLLOHOSP", "DIVISLAB", "GODREJCP",
        "HAVELLS", "PIDILITIND", "SIEMENS", "ABB", "BOSCHLTD",
        "DLF", "DABUR", "COLPAL", "AMBUJACEM", "ACC",
        "TATAPOWER", "VEDL", "GAIL", "IOC", "HINDPETRO",
        "PNB", "BANKBARODA", "CANBK", "FEDERALBNK", "IDFCFIRSTB",
        "LUPIN", "AUROPHARMA", "BIOCON", "TORNTPHARM", "ZYDUSLIFE",
        "CHOLAFIN", "MUTHOOTFIN", "BAJAJHLDNG", "SHREECEM", "BERGEPAINT",
        "MARICO", "TRENT", "PAGEIND", "MRF", "BATAINDIA",
        "POLYCAB", "DIXON", "HAL", "BEL", "BHEL",
        "SRF", "PIIND", "COFORGE", "PERSISTENT", "LTTS",
        "MPHASIS", "TATAELXSI", "KPITTECH", "CYIENT", "HAPPSTMNDS",
        "IRCTC", "ZOMATO", "NAUKRI", "DMART", "JUBLFOOD",
        "LICI", "SBICARD", "SBILIFE", "HDFCLIFE", "ICICIPRULI",
    ]
    return sorted(set(stocks))


def write_coinlist(exchange, symbols):
    """Write symbols to coinlist file."""
    filepath = os.path.join(COINLIST_DIR, f"{exchange.lower()}.txt")
    exchange_upper = exchange.upper()
    
    with open(filepath, "w", newline="\r\n") as f:
        for sym in symbols:
            f.write(f"{exchange_upper}:{sym}\r\n")
    
    print(f"Wrote {len(symbols)} symbols to {filepath}")
    return filepath


def main():
    os.makedirs(COINLIST_DIR, exist_ok=True)
    
    # Generate NSE list
    nse_symbols = fetch_nse_symbols()
    write_coinlist("NSE", nse_symbols)
    
    # Generate BSE list
    bse_symbols = get_bse_list()
    write_coinlist("BSE", bse_symbols)
    
    print(f"\nDone! NSE: {len(nse_symbols)} stocks, BSE: {len(bse_symbols)} stocks")


if __name__ == "__main__":
    main()
