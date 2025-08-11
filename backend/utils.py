from __future__ import annotations
import os
import re
import csv
import logging
import pandas as pd
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Tuple, Optional

UTILITY_MAPPING = {
    "centerpoint": {"engie": "cpt", "atlantic": "centerpoint"},
    "aep texas central": {"engie": "aepcpl", "atlantic": "aep central"},
    "aep texas north": {"engie": "aepwtu", "atlantic": "aep north"},
    "oncor": {"engie": "oncor", "atlantic": "oncor"},
    "texas-new mexico power": {"engie": "tnmp", "atlantic": "tnmp"},
    # Add more mappings as needed
}

_DEFAULT_XLSX = os.path.join("pricing_data", "ZipCodeMap.xlsx")
_DEFAULT_CSV  = os.path.join("pricing_data", "ZipCodeMap.csv")
#_ZIP_MAP_PATH = os.getenv("ZIP_MAP_PATH") or (_DEFAULT_XLSX if os.path.isfile(_DEFAULT_XLSX) else _DEFAULT_CSV)

def normalize_start_month(val) -> str:
    #"""Normalize various date formats to 'Month YYYY'"""
    try:
        if pd.isnull(val):
            return "Unknown Start Month"
        if isinstance(val, datetime):
            return val.strftime("%B %Y")
        if not isinstance(val, str):
            val = str(val)
        val = val.strip()
        val = re.sub(r"\bstart\b", "", val, flags=re.IGNORECASE).strip()
        val = re.sub(r"[^\w\s/-]", "", val).strip()
        for fmt in ["%B %Y", "%b %Y", "%m/%d/%Y", "%Y-%m-%d"]:
            try:
                parsed = datetime.strptime(val, fmt)
                return parsed.strftime("%B %Y")
            except ValueError:
                continue
        parsed = pd.to_datetime(val, errors='coerce')
        if pd.isnull(parsed):
            raise ValueError("Unable to parse date")
        return parsed.strftime("%B %Y")
    except Exception as e:
        logging.warning(f"Failed to normalize Start Month '{val}': {e}")
        return "Unknown Start Month"
    
def normalize_utility(val: str) -> str:
    try:
        return val.strip().lower().replace(" ", "")
    except Exception as e:
        logging.warning(f"Failed to normalize Utility '{val}': {e}")
        return ""

def normalize_zone(val: str) -> str:
    try:
        return val.strip().upper()
    except Exception as e:
        logging.warning(f"Failed to normalize Zone '{val}': {e}")
        return ""
    
def normalize_zip(val: Optional[str]) -> Optional[str]:
    s = re.sub(r"\D", "", str(val)) if val is not None else ""
    return s[:5] if len(s) >= 5 else None
    
def resolve_utility_for_rep(input_val: str, rep_name: str) -> str:
    try:
        normalized = normalize_utility(input_val)
        rep_key = rep_name.lower()
        return UTILITY_MAPPING.get(normalized, {}).get(rep_key, normalized)
    except Exception as e:
        logging.warning(f"Failed to resolve utility for '{input_val}' and rep '{rep_name}': {e}")
        return normalized
    
def debug_column_headers(df):
    logging.info(f"Column headers: {list(df.columns)}")
    for i, col in enumerate(df.columns):
        logging.info(f"Col[{i}] = {repr(col)}")

def find_start_month_column(df):
    for col in df.columns:
        if isinstance(col, datetime):
            return col
        if isinstance(col, str) and re.search(r"start\s*date", col, re.IGNORECASE):
            return col
        if isinstance(col, str) and re.match(r"\d{4}-\d{2}-\d{2}", col.strip()):
            return col
    return None

# --- ZIP → Zone mapping (cached) ---
_ZIP_MAP_CACHE: Dict[str, Any] = {"exact": {}, "ranges": [], "prefixes": []}
_ZIP_MAP_LOADED = False
_ZIP_MAP_PATH_ACTUAL: Optional[str] = None

def _coerce_zone(v) -> Optional[str]:
    if v is None: 
        return None
    if isinstance(v, float) and pd.isna(v): 
        return None
    try: 
        return normalize_zone(str(v))
    except Exception: 
        return None

def _norm_zip_str(z: Any) -> str:
    digits = "".join(ch for ch in str(z) if ch.isdigit())
    return digits[:5].zfill(5) if digits else ""

def _to_int_zip(z: Any) -> int:
    try:
        return int(_norm_zip_str(z))
    except Exception:
        return -1
    
_HEADER_ALIASES: Dict[str, List[str]] = {
    "zip": [
        "zip","zipcode","zip_code","postal","postalcode","zip5","5-digit zip",
        "zip code","zip (5)", "zip5digit"
    ],
    "zone": [
        "zone","congestionzone","congestion zone","loadzone","ercotzone","ercot zone",
        "region","market","load zone","zone name"
    ],
    "fromzip": ["fromzip","from_zip","zipfrom","startzip","from zip","start zip"],
    "tozip":   ["tozip","to_zip","zipto","endzip","to zip","end zip"],
    "prefix":  ["prefix","zipprefix","zip_prefix","zip prefix"],
}
    
def _standardize_headers(cols: List[str]) -> Dict[str, str]:
    return { str(c).strip().lower().replace(" ", "").replace("_", ""): c for c in cols }

def _match_header(headers_std: Dict[str, str], logical: str) -> Optional[str]:
    for probe in _HEADER_ALIASES.get(logical, [logical]):
        probe_std = probe.replace(" ", "").replace("_", "").lower()
        if probe_std in headers_std:
            return headers_std[probe_std]
    return None

def _iter_rows_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield { (k or "").strip(): v for k, v in (row or {}).items() }

def _iter_rows_xlsx(path: str):
    df = pd.read_excel(path, sheet_name=0, dtype=str, engine="openpyxl")
    df = df.where(pd.notnull(df), None)
    for _, row in df.iterrows():
        yield { str(k): (None if v is None else str(v)) for k, v in row.to_dict().items() }

def _iter_rows(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        yield from _iter_rows_xlsx(path)
    else:
        yield from _iter_rows_csv(path)

def _resolve_zip_map_path() -> Optional[str]:
    path = os.getenv("ZIP_MAP_PATH")
    if not path:
        path = _DEFAULT_XLSX if os.path.isfile(_DEFAULT_XLSX) else _DEFAULT_CSV
    return path if os.path.isfile(path) else None

def load_zip_zone_map(force: bool = False) -> Dict[str, Any]:
    """Loads XLSX with columns Zip, Zone. Cached. Environment override: ZIP_MAP_PATH."""
    global _ZIP_MAP_CACHE, _ZIP_MAP_LOADED, _ZIP_MAP_PATH_ACTUAL
    if _ZIP_MAP_LOADED and not force and any(_ZIP_MAP_CACHE.values()):
        return _ZIP_MAP_CACHE
    
    path = _resolve_zip_map_path()
    if not path:
        logging.warning("Zip map file not found (set ZIP_MAP_PATH or place ZipCodeMap.xlsx/.csv in pricing_data/)")
        _ZIP_MAP_CACHE = {"exact": {}, "ranges": [], "prefixes": []}
        _ZIP_MAP_LOADED = True
        _ZIP_MAP_PATH_ACTUAL = None
        return _ZIP_MAP_CACHE

    exact: Dict[str, str] = {}
    ranges: List[Tuple[int, int, str]] = []
    prefixes: List[Tuple[str, str]] = []

    parsed_exact = parsed_ranges = parsed_prefix = 0
    skipped_no_zip = skipped_no_zone = skipped_malformed = 0

    try:
        rows = list(_iter_rows(path))
        if not rows:
            _ZIP_MAP_CACHE = {"exact": {}, "ranges": [], "prefixes": []}
            _ZIP_MAP_LOADED = True
            _ZIP_MAP_PATH_ACTUAL = path
            logging.info("ZIP map is empty.")
            return _ZIP_MAP_CACHE

        headers_std = _standardize_headers(list(rows[0].keys()))
        zip_col    = _match_header(headers_std, "zip")
        zone_col   = _match_header(headers_std, "zone")
        from_col   = _match_header(headers_std, "fromzip")
        to_col     = _match_header(headers_std, "tozip")
        pref_col   = _match_header(headers_std, "prefix")

        for row in rows:
            # Column values (if columns exist)
            z_raw   = row.get(zip_col)  if zip_col  else None
            zn_raw  = row.get(zone_col) if zone_col else None
            a_raw   = row.get(from_col) if from_col else None
            b_raw   = row.get(to_col)   if to_col   else None
            p_raw   = row.get(pref_col) if pref_col else None

            # 1) Exact only if a Zip value is present
            if z_raw is not None and str(z_raw).strip() != "":
                z  = _norm_zip_str(z_raw)
                zn = _coerce_zone(zn_raw)
                if not z:
                    skipped_no_zip += 1
                elif not zn:
                    skipped_no_zone += 1
                else:
                    exact[z] = zn
                    parsed_exact += 1
                continue  # handled exact path

            # 2) Range: require FromZip, ToZip, Zone
            if a_raw and b_raw and zn_raw:
                zn2 = _coerce_zone(zn_raw)
                a, b = _to_int_zip(a_raw), _to_int_zip(b_raw)
                if zn2 and a != -1 and b != -1 and a <= b:
                    ranges.append((a, b, zn2))
                    parsed_ranges += 1
                    continue
                else:
                    skipped_malformed += 1
                    continue

            # 3) Prefix: require Prefix, Zone
            if p_raw and zn_raw:
                zn3 = _coerce_zone(zn_raw)
                p = "".join(ch for ch in str(p_raw) if ch.isdigit())
                if zn3 and p:
                    prefixes.append((p, zn3))
                    parsed_prefix += 1
                    continue
                else:
                    skipped_malformed += 1
                    continue

            # 4) Nothing matched
            # if a row has only zone and no zip/from/to/prefix, it's incomplete
            if zn_raw and not (a_raw or b_raw or p_raw or z_raw):
                skipped_no_zip += 1
            else:
                skipped_malformed += 1

        ranges.sort(key=lambda x: (x[0], x[1]))
        prefixes.sort(key=lambda x: len(x[0]), reverse=True)

        _ZIP_MAP_CACHE = {"exact": exact, "ranges": ranges, "prefixes": prefixes}
        _ZIP_MAP_LOADED = True
        _ZIP_MAP_PATH_ACTUAL = path
        logging.info(
            "ZIP map loaded from %s: %d exact, %d ranges, %d prefixes (skipped: no_zip=%d, no_zone=%d, malformed=%d)",
            path, len(exact), len(ranges), len(prefixes),
            skipped_no_zip, skipped_no_zone, skipped_malformed
        )
        return _ZIP_MAP_CACHE
    except Exception as e:
        logging.exception(f"Failed to load ZIP map from {path}: {e}")
        _ZIP_MAP_CACHE = {"exact": {}, "ranges": [], "prefixes": []}
        _ZIP_MAP_LOADED = True
        _ZIP_MAP_PATH_ACTUAL = path
        return _ZIP_MAP_CACHE

    #candidates = []
    #env_path = os.getenv("ZIP_MAP_PATH")
    #if env_path:
    #    candidates.append(env_path)
    #candidates += [
    #    os.path.join("pricing_data", "ZipCodeMap.xlsx"),
    #]

    #for path in candidates:
    #    try:
    #        if not os.path.exists(path):
    #            continue
    #        if path.lower().endswith(".xlsx"):
    #            df = pd.read_excel(path, engine="openpyxl")

    #        cols = {str(c).strip().lower(): c for c in df.columns}
    #        zip_col = cols.get("zip") or list(df.columns)[0]
    #        zone_col = cols.get("zone") or list(df.columns)[1]
    #        df = df[[zip_col, zone_col]].copy()
    #        df.columns = ["zip", "zone"]

    #        df["zip"] = df["zip"].apply(normalize_zip)
    #        df["zone"] = df["zone"].apply(_coerce_zone)
    #        df = df.dropna(subset=["zip", "zone"])

    #        _ZIP_ZONE_MAP = {z: zn for z, zn in zip(df["zip"], df["zone"])}
    #        _ZIP_MAP_LOADED = True
    #        logging.info(f"Loaded ZIP map with {len(_ZIP_ZONE_MAP)} entries from {path}")
    #        return _ZIP_ZONE_MAP
    #    except Exception as e:
    #        logging.warning(f"Failed to load ZIP map from {path}: {e}")

    #_ZIP_ZONE_MAP = {}
    #_ZIP_MAP_LOADED = True
    #logging.warning("No ZIP map found; ZIP→Zone resolution will return None.")
    #return _ZIP_ZONE_MAP

def zip_to_zone(zipcode: Optional[str]) -> Optional[str]:
    if not _ZIP_MAP_LOADED:
        load_zip_zone_map()
    z5 = normalize_zip(zipcode)
    if not z5:
        return None
    cache = _ZIP_MAP_CACHE
    if z5 in cache["exact"]:
        return cache["exact"][z5]
    zi = int(z5)
    for a, b, zone in cache["ranges"]:
        if a <= zi <= b:
            return zone
    for pref, zone in cache["prefixes"]:
        if z5.startswith(pref):
            return zone
    return None

def zip_map_status() -> Dict[str, Any]:
    """For debugging in an endpoint."""
    return {
        "path": _ZIP_MAP_PATH_ACTUAL,
        "loaded": _ZIP_MAP_LOADED,
        "counts": {
            "exact": len(_ZIP_MAP_CACHE.get("exact", {})),
            "ranges": len(_ZIP_MAP_CACHE.get("ranges", [])),
            "prefixes": len(_ZIP_MAP_CACHE.get("prefixes", [])),
        }
    }

def zip_map_peek(max_rows: int = 10) -> Dict[str, Any]:
    """Inspect the active file: headers + first rows (for debugging)."""
    path = _resolve_zip_map_path()
    if not path:
        return {"path": None, "error": "file not found"}
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, sheet_name=0, dtype=str, engine="openpyxl")
    else:
        df = pd.read_csv(path, dtype=str)
    df = df.where(pd.notnull(df), None)
    cols = list(map(str, df.columns.tolist()))
    head = df.head(max_rows).to_dict(orient="records")
    return {"path": path, "columns": cols, "sample": head}

    #z = normalize_zip(zipcode)
    #if not z:
    #    return None
    #if not _ZIP_MAP_LOADED:
    #    load_zip_zone_map()
    #return _ZIP_ZONE_MAP.get(z)