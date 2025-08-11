import pandas as pd
import logging
import re
from datetime import datetime

def auto_detect_header(path: str, sheet_name=0, preview_rows=10) -> int:
    preview_df = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=preview_rows, engine="openpyxl")
    target_cols = {"start month", "utility", "congestion zone", "load factor"}
    for idx, row in preview_df.iterrows():
        row_set = set(str(cell).strip().lower() for cell in row if pd.notnull(cell))
        if target_cols.issubset(row_set):
            return idx
    raise ValueError(f"Could not detect header row for {path}")

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

def load_engie(engie_path, sheet_name="All In Matrix"):
    header_row = auto_detect_header(engie_path, sheet_name=sheet_name)
    df = pd.read_excel(engie_path, sheet_name=sheet_name, header=header_row, engine="openpyxl")
    df["Start Month"] = df["Start Month"].apply(normalize_start_month)
    return df

def filter_engie_data(df, req):
    results = []
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

    for _, row in df.iterrows():
        term = row.get("Term")
        price = row.get(bracket_col)
        if term is None or price is None:
            continue
        if price != 0:
            results.append({
                "rep": "Engie",
                "term": int(term),
                "price_cents_per_kwh": round(float(price), 4)
            })
    return results
