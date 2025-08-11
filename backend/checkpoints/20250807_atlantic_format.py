import pandas as pd
import logging
import re
from datetime import datetime
from utils import normalize_start_month, normalize_utility, normalize_zone, debug_column_headers, find_start_month_column

def auto_detect_header(path: str, sheet_name=0, preview_rows=10) -> int:
    preview_df = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=preview_rows, engine="openpyxl")
    target_cols = {"start date", "utility", "zone", "load factor"}
    logging.info(f"Previewing first {preview_rows} rows to detect header in sheet: {sheet_name}")
    for idx, row in preview_df.iterrows():
        row_set = set(str(cell).strip().lower() for cell in row if pd.notnull(cell))
        logging.debug(f"Row {idx}: {row_set}")
        if target_cols.issubset(row_set):
            logging.info(f"Header row detected at index: {idx}")
            return idx
    logging.warning(f"Could not detect header row for {path}. Defaulting to row 10.")
    return 10

def load_atlantic(atlantic_path, sheet_name="AE Texas Matrix"):
    logging.info(f"Loading Atlantic data from file: {atlantic_path}, sheet: {sheet_name}")
    df = pd.read_excel(atlantic_path, sheet_name=sheet_name, header=None, engine="openpyxl")

    # Attempt to detect header row by looking for known labels
    header_row = auto_detect_header(atlantic_path, sheet_name=sheet_name)
    df.columns = df.iloc[header_row]
    df = df[header_row + 1:].reset_index(drop=True)

    debug_column_headers(df)

    col = find_start_month_column(df)
    if col:
        df.rename(columns={col: "Start Month"}, inplace=True)
        df["Start Month"] = df["Start Month"].apply(normalize_start_month)
    else:
        raise ValueError("Could not find or assign 'Start Month' column in Atlantic sheet.")

    df["Utility"] = df["Utility"].apply(normalize_utility)
    df["Zone"] = df["Zone"].apply(normalize_zone)
    df.rename(columns={"Zone": "Congestion Zone"}, inplace=True)

    return df

def filter_atlantic_data(df, req):
    results = []

    term_columns = [col for col in df.columns if isinstance(col, str) and col.endswith("m")]
    if not term_columns:
        logging.warning(f"Atlantic: No term columns found. Columns: {list(df.columns)}")
        return results
    
    melted = df.melt(
        id_vars=["Utility", "Congestion Zone", "Load Factor", "Start Month"],
        value_vars=term_columns,
        var_name="Term",
        value_name="Price"
    )

    # Convert '6m' → 6, etc.
    melted["Term"] = melted["Term"].str.replace("m", "").astype(int)
    melted["Price"] = pd.to_numeric(melted["Price"], errors="coerce")
    melted.dropna(subset=["Price"], inplace=True)

    for _, row in melted.iterrows():
        if (
            normalize_start_month(row["Start Month"]) == req.start_month
            and row["Utility"] == normalize_utility(req.utility)
            and row["Congestion Zone"] == req.congestion_zone.upper()
            and row["Load Factor"] == req.load_factor.upper()
        ):
            results.append({
                "rep": "Atlantic",
                "term": int(row["Term"]),
                "price_cents_per_kwh": round(float(row["Price"])*100, 4)
            })
    return results
