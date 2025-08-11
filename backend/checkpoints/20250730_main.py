from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
import pandas as pd
from typing import List
from datetime import datetime, timezone
import logging
from logging.handlers import TimedRotatingFileHandler
import re
import os
import glob
import threading
import time
from dotenv import load_dotenv # type: ignore
import numpy as np

# --- Load environment variables ---
load_dotenv()

# --- Set up rotating log file ---
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
log_handler = TimedRotatingFileHandler("pricing_api.log", when="midnight", backupCount=7)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[log_handler, console_handler])

app = FastAPI()

# --- In-memory pricing sources ---
pricing_sources = {}
engie_df = None
xcon_df = None

last_refresh_status = {"timestamp": None, "success": False, "error": None}

# --- Helper to auto-detect header row ---
def auto_detect_header(path: str, sheet_name=0, preview_rows=10) -> int:
    preview_df = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=preview_rows, engine="openpyxl")
    target_cols = {"start month", "utility", "congestion zone", "load factor"}
    for idx, row in preview_df.iterrows():
        row_set = set(str(cell).strip().lower() for cell in row if pd.notnull(cell))
        if target_cols.issubset(row_set):
            return idx
    raise ValueError(f"Could not detect header row for {path}")

# --- Get most recent file based on pattern ---
def get_latest_file(directory: str, pattern: str) -> str:
    files = glob.glob(os.path.join(directory, pattern))
    if not files:
        raise FileNotFoundError(f"No files matching pattern {pattern} in {directory}")
    return max(files, key=os.path.getmtime)

# --- Normalize Start Month ---
def normalize_start_month(val):
    if pd.isnull(val):
        logging.warning("Start Month null value found")
        return "Unknown Start Month"
    try:
        if isinstance(val, pd.Timestamp):
            return val.strftime("%B %Y Start")
        if isinstance(val, str):
            val = val.strip()
            val = re.sub(r"\bstart\b", "", val, flags=re.IGNORECASE).strip()
            val = re.sub(r"[^\w\s/-]", "", val).strip()
        for fmt in ["%B %Y", "%b %Y", "%m/%d/%Y", "%Y-%m-%d"]:
            try:
                parsed = datetime.strptime(val, fmt)
                return parsed.strftime("%B %Y Start")
            except ValueError:
                continue
        parsed = pd.to_datetime(val, errors='coerce')
        if pd.isnull(parsed):
            raise ValueError("Unable to parse date")
        return parsed.strftime("%B %Y Start")
    except Exception as e:
        logging.warning(f"Failed to normalize Start Month '{val}': {e}")
        return "Unknown Start Month"

# --- Load pricing data from latest files ---
def refresh_pricing_data():
    global engie_df, xcon_df, pricing_sources, last_refresh_status
    try:
        pricing_dir = "pricing_data"
        engie_path = get_latest_file(pricing_dir, "TX_MATRIX_*.xlsx")
        freepoint_path = get_latest_file(pricing_dir, "*_Freepoint_Matrix_Offer_ERCOT_Adj.xlsx")

        engie_header_row = auto_detect_header(engie_path, sheet_name="All In Matrix")
        xcon_header_row = auto_detect_header(engie_path, sheet_name="X-Con Matrix")
        freepoint_header_row = auto_detect_header(freepoint_path, sheet_name=0)

        engie_df = pd.read_excel(engie_path, sheet_name="All In Matrix", header=engie_header_row, engine="openpyxl")
        xcon_df = pd.read_excel(engie_path, sheet_name="X-Con Matrix", header=xcon_header_row, engine="openpyxl")
        freepoint_df = pd.read_excel(freepoint_path, sheet_name=0, header=freepoint_header_row, engine="openpyxl")

        for col in freepoint_df.columns:
            if col.strip().lower() == "start month":
                freepoint_df.rename(columns={col: "Start Month"}, inplace=True)
                break

        freepoint_df["Start Month"] = freepoint_df["Start Month"].apply(normalize_start_month)
        engie_df["Start Month"] = engie_df["Start Month"].apply(normalize_start_month)
        xcon_df["Start Month"] = xcon_df["Start Month"].apply(normalize_start_month)

        pricing_sources = {
            "Engie": engie_df,
            "Freepoint": freepoint_df,
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
    congestion_zone: str
    load_factor: str  # 'HI' or 'LO'
    annual_volume: float
    include_congestion: bool = True

class PriceResult(BaseModel):
    rep: str
    term: int
    price_cents_per_kwh: float

@app.post("/get-prices", response_model=List[PriceResult])
def get_prices(req: PriceRequest):
    results = []
    for rep_name, df in pricing_sources.items():
        df_filtered = df[
            (df["Start Month"] == req.start_month)
            & (df["Utility"].str.lower() == req.utility.lower())
            & (df["Congestion Zone"].str.lower() == req.congestion_zone.lower())
            & (df["Load Factor"].str.upper() == req.load_factor.upper())
        ]

        if df_filtered.empty:
            continue

        found_match = False
        if rep_name == "Freepoint":
            volume_col = None
            if req.annual_volume < 100_000:
                volume_col = "0-100,000"
            elif req.annual_volume < 250_000:
                volume_col = "100,000-250,000"
            else:
                volume_col = "250,000-1,000,000"

            # Match columns like '6 Month', '12 Month', etc.
            term_columns = [col for col in df_filtered.columns if re.match(r"^\d+ Month$", str(col))]
            if not term_columns:
                logging.warning(f"Freepoint: No term columns found for {rep_name}. Columns: {list(df_filtered.columns)}")
                continue

            volume_matches = df_filtered[df_filtered["kWh/Year"] == volume_col]
            if not volume_matches.empty:
                for _, row in volume_matches.iterrows():
                    for term_col in term_columns:
                        try:
                            price = row.get(term_col)
                            if pd.notnull(price) and price > 0:
                                # Extract the number of months from the column name, e.g., '12 Month' -> 12
                                term = int(term_col.split()[0])
                                results.append(PriceResult(
                                    rep=rep_name,
                                    term=term,
                                    price_cents_per_kwh=price
                                ))
                                found_match = True
                        except Exception as e:
                            logging.warning(f"Freepoint: Error parsing '{term_col}' in row: {e}")

        else:  # Engie
            volume_brackets = [
                (0, "0 - 199,999"),
                (200_000, "200,000 - 399,999"),
                (400_000, "400,000 - 599,999"),
                (600_000, "600,000 - 799,999"),
                (800_000, "800,000 - 999,999")
            ]
            bracket_col = None
            for threshold, col in volume_brackets:
                if req.annual_volume >= threshold:
                    bracket_col = col

            for _, row in df_filtered.iterrows():
                term = row.get("Term")
                if pd.isnull(term) or pd.isnull(row.get(bracket_col)):
                    continue
                price = row.get(bracket_col)
                if pd.notnull(price) and price != 0:
                    results.append(PriceResult(
                        rep=rep_name,
                        term=int(term),
                        price_cents_per_kwh=round(float(price), 4)
                    ))
                    found_match = True

        if not found_match:
            logging.info(f"No matching volume/term columns found for {rep_name}")

    return sorted(results, key=lambda r: (r.term, r.rep))

@app.post("/debug-pricing-filters")
def debug_filters(req: PriceRequest):
    result = {}
    for rep, df in pricing_sources.items():
        filtered = df[
            (df["Start Month"] == req.start_month)
            & (df["Utility"].str.lower() == req.utility.lower())
            & (df["Congestion Zone"].str.lower() == req.congestion_zone.lower())
            & (df["Load Factor"].str.upper() == req.load_factor.upper())
        ]
        cleaned = filtered.head(3).replace({np.nan: None}).to_dict("records")
        result[rep] = {
            "match_count": len(filtered),
            "sample": cleaned
        }
    return result

@app.get("/debug/start-months")
def debug_start_months():
    return {
        "Engie": sorted(engie_df["Start Month"].dropna().unique().tolist()) if engie_df is not None else [],
        "Freepoint": sorted(pricing_sources.get("Freepoint", pd.DataFrame())["Start Month"].dropna().unique().tolist())
    }

@app.get("/debug/columns")
def debug_columns():
    return {
        "Engie": list(engie_df.columns) if engie_df is not None else [],
        "Freepoint": list(pricing_sources.get("Freepoint", pd.DataFrame()).columns)
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
