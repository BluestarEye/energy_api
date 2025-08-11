import re
import os
import glob
import threading
import time
import logging
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI, HTTPException, Request, Depends, Query
from dotenv import load_dotenv # type: ignore
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
from engie_format import load_engie, filter_engie_data
from atlantic_format import load_atlantic, filter_atlantic_data
from utils import normalize_start_month, normalize_utility, normalize_zone, resolve_utility_for_rep, zip_to_zone, load_zip_zone_map, zip_map_status, zip_map_peek
# Uncomment if Freepoint is needed
#from freepoint_format import load_freepoint, filter_freepoint_data

def clean_nans(obj):
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            # Convert key if it's NaN or float NaN
            if isinstance(k, float) and pd.isna(k):
                continue  # or: k = "null_key" to keep it
            elif isinstance(k, float):
                k = str(k)
            cleaned[k] = clean_nans(v)
        return cleaned
    elif isinstance(obj, list):
        return [clean_nans(i) for i in obj]
    elif isinstance(obj, float) and pd.isna(obj):
        return None
    return obj

# --- Load environment variables ---
load_dotenv()

# --- Set up rotating log file ---
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
log_handler = TimedRotatingFileHandler("logs/pricing_api.log", when="midnight", backupCount=7)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[log_handler, console_handler])

app = FastAPI(
    title="Energy Pricing API",
    description="API for retrieving and comparing energy pricing data from multiple sources",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory pricing sources ---
pricing_sources = {}
engie_df = None
xcon_df = None
last_refresh_status = {"timestamp": None, "success": False, "error": None}

# --- Utility: Get most recent file based on pattern ---
def get_latest_file(directory: str, pattern: str) -> str:
    files = glob.glob(os.path.join(directory, pattern))
    if not files:
        raise FileNotFoundError(f"No files matching pattern {pattern} in {directory}")
    return max(files, key=os.path.getmtime)

# --- Load pricing data from latest files ---
def refresh_pricing_data():
    global engie_df, xcon_df, pricing_sources, last_refresh_status
    try:
        pricing_dir = "pricing_data"
        engie_path = get_latest_file(pricing_dir, "TX_MATRIX_*.xlsx")
        atlantic_path = get_latest_file(pricing_dir, "* - AE TEXAS.xlsx")
        # Uncomment if Freepoint is needed
        #freepoint_path = get_latest_file(pricing_dir, "*_Freepoint_Matrix_Offer_ERCOT_Adj.xlsx")

        load_zip_zone_map()  # pre-load map; avoids first-request latency

        engie_df = load_engie(engie_path, sheet_name="All In Matrix")
        xcon_df = load_engie(engie_path, sheet_name="X-Con Matrix")
        atlantic_df = load_atlantic(atlantic_path, sheet_name="AE Texas Matrix")
        #freepoint_df = load_freepoint(freepoint_path, sheet_name=0)

        pricing_sources = {
            "Engie": engie_df,
            "X-Con": xcon_df,
            "Atlantic": atlantic_df,
            #"Freepoint": freepoint_df,
        }

        logging.info("Successfully refreshed pricing data from latest files.")
        last_refresh_status.update({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": True,
            "error": None
        })

    except Exception as e:
        logging.error(f"Failed to refresh pricing data: {e}")
        last_refresh_status.update({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "error": str(e)
        })

# --- Background thread for daily refresh ---
def schedule_daily_refresh():
    def refresh_loop():
        while True:
            refresh_pricing_data()
            time.sleep(86400)  # Sleep for 24 hours

    threading.Thread(target=refresh_loop, daemon=True).start()

# --- Trigger initial load and schedule ---
refresh_pricing_data()
schedule_daily_refresh()

class PriceRequest(BaseModel):
    start_month: str
    utility: str
    zipcode: str
    #congestion_zone: str
    load_factor: str  # 'HI' or 'LO'
    annual_volume: float
    #include_congestion: bool = True

class PriceResult(BaseModel):
    rep: str
    term: int
    price_cents_per_kwh: float

def _resolve_zone_from_request(req: PriceRequest) -> str:
    """Derive zone strictly from ZIP. Raise if unknown."""
    zone = zip_to_zone(req.zipcode)
    if not zone:
        raise HTTPException(status_code=422, detail="Unknown ZIP code. Please verify your 5-digit ZIP.")
    return normalize_zone(zone)

@app.post("/get-prices", response_model=List[PriceResult])
def get_prices(req: PriceRequest):
    results = []
    normalized_start = normalize_start_month(req.start_month)
    normalized_zone = _resolve_zone_from_request(req)
    normalized_lf = req.load_factor.strip().upper()
    for rep_name, df in pricing_sources.items():
        resolved_utility = resolve_utility_for_rep(req.utility, rep_name)
        df_filtered = df[
            (df["Start Month"].apply(normalize_start_month) == normalized_start) &
            (df["Utility"].apply(normalize_utility) == normalize_utility(resolved_utility)) &
            (df["Congestion Zone"].apply(normalize_zone) == normalized_zone) &
            (df["Load Factor"].str.strip().str.upper() == normalized_lf)
        ]

        if df_filtered.empty:
            logging.info(f"No matches found for {rep_name} with filters: {req}")
            continue

        if rep_name == "Engie":
            results.extend(filter_engie_data(df_filtered, req))
        elif rep_name == "Atlantic":
            results.extend(filter_atlantic_data(df_filtered, req))
        #elif rep_name == "Freepoint":
            #results.extend(filter_freepoint_data(df_filtered, req))
    
    return sorted(results, key=lambda r: (r["term"], r["rep"]))

@app.post("/debug-pricing-filters")
def debug_filters(request: PriceRequest):
    try:
        result = {}
        logging.info(f"Debug request: {request}")
        logging.info(f"Available pricing sources: {list(pricing_sources.keys())}")
        normalized_start = normalize_start_month(request.start_month)
        normalized_zone = _resolve_zone_from_request(request)
        normalized_lf = request.load_factor.strip().upper()

        for rep_name, df in pricing_sources.items():
            try:
                logging.info(f"Processing {rep_name}")
                if df.empty:
                    logging.warning(f"{rep_name} DataFrame is empty.")
                    continue

                required_cols = ["Start Month", "Utility", "Congestion Zone", "Load Factor"]
                if not all(col in df.columns for col in required_cols):
                    logging.warning(f"{rep_name}: Missing required columns: {df.columns}")
                    continue
                
                df = df.dropna(subset=required_cols)
                resolved_utility = resolve_utility_for_rep(request.utility, rep_name)
                filtered = df[
                    (df["Start Month"].apply(normalize_start_month) == normalized_start) &
                    (df["Utility"].apply(normalize_utility) == normalize_utility(resolved_utility)) &
                    (df["Congestion Zone"].apply(normalize_zone) == normalized_zone) &
                    (df["Load Factor"].str.strip().str.upper() == normalized_lf)
                ]
                cleaned = filtered.head(3).replace({np.nan: None}).to_dict("records")
                result[rep_name] = {
                    "match_count": len(filtered),
                    "sample": cleaned
                }
            except Exception as rep_err:
                logging.error(f"Error filtering {rep_name}: {rep_err}", exc_info=True)
                continue  # Don’t let one REP break the endpoint

        final_result = clean_nans(result)
        logging.info(f"Final debug output: {final_result}")
        return final_result

    except Exception:
        import traceback
        err = traceback.format_exc()
        logging.error(err)
        return PlainTextResponse(err, status_code=500)

@app.get("/debug/start-months")
def debug_start_months():
    return {
        "Engie": sorted(engie_df["Start Month"].dropna().unique().tolist()) if engie_df is not None else [],
        "X-Con": sorted(xcon_df["Start Month"].dropna().unique().tolist()) if xcon_df is not None else [],
        "Atlantic": sorted(pricing_sources["Atlantic"]["Start Month"].dropna().unique().tolist()) if pricing_sources.get("Atlantic") is not None else [],
        # Uncomment if Freepoint is needed
        #"Freepoint": sorted(pricing_sources["Freepoint"]["Start Month"].dropna().unique().tolist()) if pricing_sources.get("Freepoint") is not None else []
    }

@app.get("/debug/columns")
def debug_columns():
    return {
        "Engie": list(engie_df.columns) if engie_df is not None else [],
        "X-Con": list(xcon_df.columns) if xcon_df is not None else [],
        "Atlantic": list(pricing_sources["Atlantic"].columns) if pricing_sources.get("Atlantic") is not None else [],
        # Uncomment if Freepoint is needed
        #"Freepoint": list(pricing_sources["Freepoint"].columns) if pricing_sources.get("Freepoint") is not None else []
    }

@app.get("/debug/unique-values")
def debug_unique_values():
    result = {}
    for rep, df in pricing_sources.items():
        result[rep] = {
            "Start Month": sorted(df["Start Month"].dropna().unique().tolist()),
            "Utility": sorted(df["Utility"].dropna().unique().tolist()),
            "Congestion Zone": sorted(df["Congestion Zone"].dropna().unique().tolist()),
            "Load Factor": sorted(df["Load Factor"].dropna().unique().tolist()),
        }
    return result

@app.get("/debug/zip/{zipcode}")
def debug_zip(zipcode: str):
    from utils import normalize_zip, zip_to_zone, load_zip_zone_map
    load_zip_zone_map()
    nz = normalize_zip(zipcode)
    zone = zip_to_zone(nz)
    return {"zip": nz, "zone": zone}

@app.get("/debug/zip-map-status")
def debug_zip_map_status():
    return zip_map_status()

@app.get("/debug/zip-lookup")
def debug_zip_lookup(zip: str = Query(..., min_length=3, max_length=10)):
    zone = zip_to_zone(zip)
    return {"zip": zip, "zone": zone}

@app.post("/debug/reload-zip-map")
def debug_reload_zip_map():
    """Force reload the ZIP→Zone map; returns count. Useful for tests."""
    try:
        m = load_zip_zone_map(force=True)
        return {"loaded_rows": len(m)}
    except Exception as e:
        return PlainTextResponse(str(e), status_code=500)
    
@app.get("/debug/zip-map-peek")
def debug_zip_map_peek():
    try:
        payload = zip_map_peek()
        return JSONResponse(payload)
    except Exception as e:
        logging.exception("zip-map-peek failed")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/refresh-status")
def get_refresh_status():
    return last_refresh_status

@app.get("/status")
def get_status():
    return {
        "refresh_status": last_refresh_status,
        "sources_loaded": list(pricing_sources.keys()),
        "engie_rows": len(engie_df) if engie_df is not None else 0,
        "xcon_rows": len(xcon_df) if xcon_df is not None else 0
    }
