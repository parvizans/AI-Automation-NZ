import json
import math
import base64
import time
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
from PIL import Image


st.set_page_config(
    page_title="AutomationPark GeoMap MapLibre",
    page_icon="🗺️",
    layout="wide",
)

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
BRAND_WORDMARK_FILE = ASSET_DIR / "automationpark-wordmark.png"
BRAND_MARK_FILE = ASSET_DIR / "automationpark-mark.png"
CELL_FILE = ROOT / "datasets" / "CCell-Site.csv"
NEIGHBOR_FILE = ROOT / "datasets" / "Neighbors-OK.csv"
DEFAULT_DT_FILE = (
    ROOT
    / "datasets"
    / "SRWT-20260620T045003Z-3-001"
    / "SRWT"
    / "Export DT SRWT"
    / "SRWT_LTE_DL - Copy.CSV"
)
DEFAULT_KPI_FILE = ROOT / "datasets" / "Traffic.csv"
ATOLL_PREDICTION_DIR = (
    ROOT
    / "datasets"
    / "SRWT-20260620T045003Z-3-001"
    / "SRWT"
    / "SRWT Prediction"
)
ATOLL_RASTER_FILE = ATOLL_PREDICTION_DIR / "LTE_Graduated Downlink Coverage 5m.tif"
ATOLL_WORLD_FILE = ATOLL_PREDICTION_DIR / "LTE_Graduated Downlink Coverage 5m.tfw"


def clean_value(value):
    if pd.isna(value):
        return ""
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


@st.cache_data(show_spinner=False)
def image_data_uri(path_text):
    path = Path(path_text)
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def destination_point(lat, lon, bearing_deg, distance_km):
    radius_km = 6371.0088
    bearing = math.radians(float(bearing_deg))
    lat1 = math.radians(float(lat))
    lon1 = math.radians(float(lon))
    angular = float(distance_km) / radius_km

    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular)
        + math.cos(lat1) * math.sin(angular) * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angular) * math.cos(lat1),
        math.cos(angular) - math.sin(lat1) * math.sin(lat2),
    )
    return [math.degrees(lon2), math.degrees(lat2)]


def normalized_carrier_key_py(carrier):
    carrier = str(carrier or "").upper().strip()
    if "F4" in carrier:
        return "F4"
    if "F3" in carrier:
        return "F3"
    if "F2" in carrier:
        return "F2"
    if "F1" in carrier:
        return "F1"
    if "N35" in carrier or "NR35" in carrier or "NR3500" in carrier or "N3500" in carrier:
        return "N35"
    if "NR26" in carrier or "NR2600" in carrier or "N26" in carrier or "N2600" in carrier:
        return "NR2600"
    if "L23" in carrier or "L2300" in carrier or "N23" in carrier or "NR23" in carrier:
        return "L2300"
    if "L21" in carrier or "L2100" in carrier:
        return "L2100"
    if "L18" in carrier or "L1800" in carrier:
        return "L18"
    if "N09" in carrier or "NR09" in carrier or "N900" in carrier or "NR900" in carrier:
        return "NR900"
    if "L07" in carrier or "NR07" in carrier or "L700" in carrier or "NR700" in carrier:
        return "L07"
    return carrier or "Unknown"


def band_radius_km(carrier):
    # Inner -> outer shell design for dense multi-carrier sites such as SITE_216.
    # Future placeholders F1-F4 are included so later bands can be activated by data only.
    key = normalized_carrier_key_py(carrier)
    carrier_radius = {
        # Inner -> outer. Wider spacing makes 7+ carriers visible on one site.
        "F4": 0.35,
        "F3": 0.50,
        "N35": 0.68,
        "F2": 0.82,
        "NR2600": 1.00,
        "L2300": 1.20,
        "L2100": 1.42,
        "L18": 1.68,
        "F1": 1.96,
        "NR900": 2.25,
        "L07": 2.60,
    }
    return carrier_radius.get(key, 1.28)


def band_color(carrier):
    key = normalized_carrier_key_py(carrier)
    carrier_colors = {
        "F4": "#f0abfc",
        "F3": "#c084fc",
        "N35": "#ff3df2",
        "F2": "#818cf8",
        "NR2600": "#8b5cf6",
        "L2300": "#0ea5e9",
        "L2100": "#38bdf8",
        "L18": "#ffb000",
        "F1": "#facc15",
        "NR900": "#14b8a6",
        "L07": "#20ff7a",
    }
    return carrier_colors.get(key, "#a78bfa")


def hash_color(value):
    text = str(value or "")
    score = sum((idx + 1) * ord(char) for idx, char in enumerate(text))
    hue = score % 360
    return f"hsl({hue}, 88%, 56%)"


def tech_color(technology):
    tech = str(technology).upper()
    if "NR" in tech or "5G" in tech:
        return "#a855f7"
    if "LTE" in tech or "4G" in tech:
        return "#22c55e"
    if "UMTS" in tech or "3G" in tech:
        return "#38bdf8"
    return "#a78bfa"


def rsrp_color(value):
    try:
        value = float(value)
    except Exception:
        return "#64748b"
    if value > -50:
        return "#ff0000"
    if value > -70:
        return "#cc0000"
    if value > -80:
        return "#e8b6b6"
    if value > -90:
        return "#ffd84d"
    if value > -105:
        return "#00cc00"
    if value > -110:
        return "#73d2e8"
    if value > -120:
        return "#1148e8"
    return "#0b2f9f"


def rsrq_color(value):
    try:
        value = float(value)
    except Exception:
        return "#64748b"
    if value > -7:
        return "#2563eb"
    if value > -10:
        return "#22c55e"
    if value > -13:
        return "#fde047"
    if value > -16:
        return "#f97316"
    return "#ef4444"


def sinr_color(value):
    try:
        value = float(value)
    except Exception:
        return "#64748b"
    if value >= 20:
        return "#7c3aed"
    if value >= 13:
        return "#2563eb"
    if value >= 7:
        return "#22c55e"
    if value >= 0:
        return "#fde047"
    if value >= -3:
        return "#f97316"
    return "#ef4444"


def kpi_heat_color(value, minimum, maximum):
    try:
        value = float(value)
    except Exception:
        return "#64748b"
    if maximum <= minimum:
        return "#22c55e"
    ratio = clamp((value - minimum) / (maximum - minimum))
    if ratio >= 0.84:
        return "#ef4444"
    if ratio >= 0.66:
        return "#f97316"
    if ratio >= 0.42:
        return "#fde047"
    if ratio >= 0.24:
        return "#38bdf8"
    if ratio >= 0.10:
        return "#2dd4bf"
    return "#16a34a"


def preferred_kpi_candidate(candidates):
    if not candidates:
        return None
    preferred_tokens = [
        "traffic",
        "throughput",
        "thp",
        "prb",
        "utilisation",
        "utilization",
        "util",
        "load",
        "volume",
        "vol",
        "usage",
        "capacity",
        "resource",
    ]

    def score(item):
        column, filled_count = item
        key = str(column).strip().lower().replace(" ", "").replace("_", "")
        token_score = 0
        for rank, token in enumerate(preferred_tokens):
            if token in key:
                token_score = max(token_score, (len(preferred_tokens) - rank) * 100000)
        return token_score + filled_count

    return sorted(candidates, key=score, reverse=True)[0][0]


def is_rf_quality_column(column):
    key = str(column).strip().lower().replace(" ", "").replace("_", "")
    return any(token in key for token in ("rsrp", "rsrq", "sinr", "cqi", "pci"))


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


def rsrp_weight(value):
    try:
        value = float(value)
    except Exception:
        return 0.0
    return clamp((value + 140) / 90)


def rsrq_weight(value):
    try:
        value = float(value)
    except Exception:
        return 0.0
    return clamp((value + 20) / 16)


def sinr_weight(value):
    try:
        value = float(value)
    except Exception:
        return 0.0
    return clamp((value + 5) / 35)


NZMG_A = 6378388.0
NZMG_LAT0 = -41.0
NZMG_LON0 = 173.0
NZMG_FALSE_NORTHING = 6023150.0
NZMG_FALSE_EASTING = 2510000.0
NZMG_B = [
    complex(0.7557853228, 0.0),
    complex(0.249204646, 0.003371507),
    complex(-0.001541739, 0.041058560),
    complex(-0.10162907, 0.01727609),
    complex(-0.26623489, -0.36249218),
    complex(-0.6870983, -1.1651967),
]
NZMG_C = [
    complex(1.3231270439, 0.0),
    complex(-0.577245789, -0.007809598),
    complex(0.508307513, -0.112208952),
    complex(-0.15094762, 0.18200602),
    complex(1.01418179, 1.64497696),
    complex(1.9660549, 2.5127645),
]
NZMG_D = [
    1.5627014243,
    0.5185406398,
    -0.03333098,
    -0.1052906,
    -0.0368594,
    0.007317,
    0.01220,
    0.00394,
    -0.0013,
]


def nzmg_to_lonlat(easting, northing):
    z = complex(
        (float(northing) - NZMG_FALSE_NORTHING) / NZMG_A,
        (float(easting) - NZMG_FALSE_EASTING) / NZMG_A,
    )
    theta = sum(coef * z ** power for power, coef in enumerate(NZMG_C, start=1))
    for _ in range(2):
        numerator = z + sum(
            (power - 1) * coef * theta ** power
            for power, coef in enumerate(NZMG_B, start=1)
            if power > 1
        )
        denominator = sum(
            power * coef * theta ** (power - 1)
            for power, coef in enumerate(NZMG_B, start=1)
        )
        theta = numerator / denominator

    dpsi = theta.real
    dlon = theta.imag
    dlat = sum(coef * dpsi ** power for power, coef in enumerate(NZMG_D, start=1))
    lat = NZMG_LAT0 + (100000.0 / 3600.0) * dlat
    lon = NZMG_LON0 + (180.0 / math.pi) * dlon
    return [lon, lat]


def shell_polygon(row):
    lat = float(row["LATITUDE"])
    lon = float(row["LONGITUDE"])
    azimuth = float(row.get("AZIMUTH", 0) or 0)
    beamwidth = float(row.get("BEAMWIDTH", 65) or 65)
    radius_km = band_radius_km(row.get("CARRIER", ""))

    points = [[lon, lat]]
    start = azimuth - beamwidth / 2
    end = azimuth + beamwidth / 2
    for angle in [start + (end - start) * idx / 18 for idx in range(19)]:
        points.append(destination_point(lat, lon, angle, radius_km))
    points.append([lon, lat])
    return points


@st.cache_data(show_spinner=False)
def load_cells():
    df = pd.read_csv(CELL_FILE)
    df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).copy()
    df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
    df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
    df["AZIMUTH"] = pd.to_numeric(df["AZIMUTH"], errors="coerce").fillna(0)
    for column in ["HEIGHT", "PMAX"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
        else:
            df[column] = 0
    df = df.dropna(subset=["LATITUDE", "LONGITUDE"])
    return df


@st.cache_data(show_spinner=False)
def load_neighbors():
    if not NEIGHBOR_FILE.exists():
        return pd.DataFrame(columns=["source_sector", "target_sector", "relation_type"])
    nbr_df = pd.read_csv(NEIGHBOR_FILE)
    required = ["source_sector", "target_sector"]
    if any(column not in nbr_df.columns for column in required):
        return pd.DataFrame(columns=["source_sector", "target_sector", "relation_type"])
    nbr_df = nbr_df.dropna(subset=required).copy()
    nbr_df["source_sector"] = nbr_df["source_sector"].astype(str).str.strip()
    nbr_df["target_sector"] = nbr_df["target_sector"].astype(str).str.strip()
    if "relation_type" not in nbr_df.columns:
        nbr_df["relation_type"] = "Unknown"
    nbr_df["relation_type"] = nbr_df["relation_type"].astype(str).str.strip()
    return nbr_df


@st.cache_data(show_spinner=False)
def build_anr_summary(neighbor_df, valid_cell_names):
    valid_cells = {str(cell).strip() for cell in valid_cell_names if str(cell).strip()}
    valid_cell_keys = {cell.upper() for cell in valid_cells}

    def normalize_relation(value):
        key = str(value).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
        if key == "intrafreq":
            return "IntraFreq"
        if key == "interfreq":
            return "InterFreq"
        if key == "irat":
            return "IRAT"
        return str(value).strip() or "Unknown"

    if neighbor_df.empty:
        return {
            "total": 0,
            "oneWay": 0,
            "missingTargets": 0,
            "relationCounts": {"IntraFreq": 0, "InterFreq": 0, "IRAT": 0},
            "duplicateRows": 0,
            "duplicatePairs": 0,
            "issueRows": 0,
            "auditRows": [],
            "byCell": {},
        }

    clean_df = neighbor_df[["source_sector", "target_sector", "relation_type"]].dropna(subset=["source_sector", "target_sector"]).copy()
    clean_df["source_sector"] = clean_df["source_sector"].astype(str).str.strip()
    clean_df["target_sector"] = clean_df["target_sector"].astype(str).str.strip()
    clean_df["relation_type"] = clean_df["relation_type"].apply(normalize_relation)
    clean_df["source_key"] = clean_df["source_sector"].str.upper()
    clean_df["target_key"] = clean_df["target_sector"].str.upper()
    relation_counts = {
        "IntraFreq": int((clean_df["relation_type"] == "IntraFreq").sum()),
        "InterFreq": int((clean_df["relation_type"] == "InterFreq").sum()),
        "IRAT": int((clean_df["relation_type"] == "IRAT").sum()),
    }

    pairs = set(zip(clean_df["source_key"], clean_df["target_key"]))
    one_way_pairs = {
        (source, target)
        for source, target in pairs
        if (target, source) not in pairs
    }
    clean_df["is_one_way"] = clean_df.apply(lambda row: (row["source_key"], row["target_key"]) in one_way_pairs, axis=1)
    clean_df["is_missing_target"] = ~clean_df["target_key"].isin(valid_cell_keys)
    duplicate_counts = clean_df.groupby(["source_key", "target_key", "relation_type"]).size().to_dict()
    clean_df["duplicate_count"] = clean_df.apply(
        lambda row: int(duplicate_counts.get((row["source_key"], row["target_key"], row["relation_type"]), 0)),
        axis=1,
    )
    clean_df["is_duplicate"] = clean_df["duplicate_count"] > 1
    missing_targets_df = clean_df[clean_df["is_missing_target"]].copy()
    duplicate_df = clean_df[clean_df["is_duplicate"]].copy()

    incoming = clean_df.groupby("target_sector").size().to_dict()
    outgoing = clean_df.groupby("source_sector").size().to_dict()
    outgoing_relation_counts = clean_df.groupby(["source_sector", "relation_type"]).size().to_dict()
    duplicate_by_source = duplicate_df.groupby("source_sector").size().to_dict() if not duplicate_df.empty else {}
    one_way_by_cell = {}
    for source, target in one_way_pairs:
        one_way_by_cell[source] = one_way_by_cell.get(source, 0) + 1
        one_way_by_cell[target] = one_way_by_cell.get(target, 0) + 1
    missing_by_source = missing_targets_df.groupby("source_sector").size().to_dict() if not missing_targets_df.empty else {}

    by_cell = {}
    for cell in valid_cells:
        cell_key = cell.upper()
        by_cell[cell] = {
            "incoming": int(incoming.get(cell, 0)),
            "outgoing": int(outgoing.get(cell, 0)),
            "oneWay": int(one_way_by_cell.get(cell_key, 0)),
            "missing": int(missing_by_source.get(cell, 0)),
            "duplicates": int(duplicate_by_source.get(cell, 0)),
            "intra": int(outgoing_relation_counts.get((cell, "IntraFreq"), 0)),
            "inter": int(outgoing_relation_counts.get((cell, "InterFreq"), 0)),
            "irat": int(outgoing_relation_counts.get((cell, "IRAT"), 0)),
        }

    audit_rows = []
    for idx, row in clean_df.reset_index(drop=True).iterrows():
        issues = []
        if bool(row["is_one_way"]):
            issues.append("One-way")
        if bool(row["is_missing_target"]):
            issues.append("Missing target")
        if bool(row["is_duplicate"]):
            issues.append(f"Duplicate x{int(row['duplicate_count'])}")
        audit_rows.append({
            "id": int(idx + 1),
            "source": row["source_sector"],
            "target": row["target_sector"],
            "relation": row["relation_type"],
            "issue": " | ".join(issues) if issues else "OK",
            "isOneWay": bool(row["is_one_way"]),
            "isMissingTarget": bool(row["is_missing_target"]),
            "isDuplicate": bool(row["is_duplicate"]),
            "duplicateCount": int(row["duplicate_count"]),
        })

    issue_rows = int(
        (clean_df["is_one_way"] | clean_df["is_missing_target"] | clean_df["is_duplicate"]).sum()
    )

    return {
        "total": int(len(clean_df)),
        "oneWay": int(clean_df["is_one_way"].sum()),
        "missingTargets": int(len(missing_targets_df.drop_duplicates())),
        "duplicateRows": int(len(duplicate_df)),
        "duplicatePairs": int(sum(1 for count in duplicate_counts.values() if count > 1)),
        "issueRows": issue_rows,
        "relationCounts": relation_counts,
        "auditRows": audit_rows,
        "byCell": by_cell,
    }


@st.cache_data(show_spinner=False)
def build_geojson(df):
    cell_features = []
    shell_features = []
    palette = [
        "#22d3ee",
        "#f59e0b",
        "#a855f7",
        "#22c55e",
        "#fb7185",
        "#38bdf8",
        "#f472b6",
        "#84cc16",
        "#f97316",
        "#14b8a6",
    ]
    vendor_values = sorted(str(value) for value in df.get("VENDOR", pd.Series(dtype=str)).dropna().unique())
    tac_values = sorted(str(value) for value in df.get("TAC", pd.Series(dtype=str)).dropna().unique())
    vendor_colors = {value: palette[idx % len(palette)] for idx, value in enumerate(vendor_values)}
    tac_palette = ["#ef4444", "#22c55e", "#38bdf8", "#f59e0b", "#a855f7", "#14b8a6", "#fb7185", "#84cc16"]
    tac_colors = {value: tac_palette[idx % len(tac_palette)] for idx, value in enumerate(tac_values)}

    for _, row in df.iterrows():
        props = {
            key: clean_value(row.get(key, ""))
            for key in [
                "SITE_NAME",
                "CELL_NAME",
                "Technology",
                "CARRIER",
                "VENDOR",
                "CLUSTER_AREA",
                "TAC",
                "PCI",
                "AZIMUTH",
                "HEIGHT",
                "ANTENNA",
                "PMAX",
                "RSPOWER (dBm)",
                "traffic",
                "utilization",
                "rsrp",
                "sinr",
            ]
        }
        props["color"] = band_color(row.get("CARRIER", ""))
        props["carrierColor"] = band_color(row.get("CARRIER", ""))
        props["technologyColor"] = tech_color(row.get("Technology", ""))
        props["vendorColor"] = vendor_colors.get(str(row.get("VENDOR", "")), hash_color(row.get("VENDOR", "")))
        props["pciColor"] = hash_color(row.get("PCI", ""))
        props["tacColor"] = tac_colors.get(str(row.get("TAC", "")), hash_color(row.get("TAC", "")))

        point = [float(row["LONGITUDE"]), float(row["LATITUDE"])]
        cell_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": point},
            "properties": props,
        })

        shell_features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [shell_polygon(row)]},
            "properties": props,
        })

    return (
        {"type": "FeatureCollection", "features": cell_features},
        {"type": "FeatureCollection", "features": shell_features},
    )


def find_column(columns, candidates):
    normalized = {str(col).strip().lower().replace(" ", "").replace("_", ""): col for col in columns}
    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "")
        if key in normalized:
            return normalized[key]
    for col in columns:
        lowered = str(col).lower()
        if any(candidate.lower() in lowered for candidate in candidates):
            return col
    return None


@st.cache_data(show_spinner=False)
def read_dt_table_from_bytes(file_bytes, suffix):
    def read_table(source):
        try:
            return pd.read_csv(source)
        except Exception:
            return pd.read_csv(source, sep=None, engine="python")

    source = BytesIO(file_bytes)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source)
    return read_table(source)


@st.cache_data(show_spinner=False)
def read_dt_table_from_path(path_text, modified_ns):
    path = Path(path_text)

    def read_table(source):
        try:
            return pd.read_csv(source)
        except Exception:
            return pd.read_csv(source, sep=None, engine="python")

    return read_table(path)


def load_dt_dataframe(uploaded_file=None, load_default=False):
    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix.lower()
        return read_dt_table_from_bytes(uploaded_file.getvalue(), suffix)
    if load_default and DEFAULT_KPI_FILE.exists():
        return read_dt_table_from_path(str(DEFAULT_KPI_FILE), DEFAULT_KPI_FILE.stat().st_mtime_ns)
    if load_default and DEFAULT_DT_FILE.exists():
        return read_dt_table_from_path(str(DEFAULT_DT_FILE), DEFAULT_DT_FILE.stat().st_mtime_ns)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def build_dt_geojson(dt_df, cell_df=None):
    if dt_df.empty:
        return {"type": "FeatureCollection", "features": []}, {}

    lat_col = find_column(dt_df.columns, ["Latitude", "LATITUDE", "Lat", "GPS_LAT", "Y"])
    lon_col = find_column(dt_df.columns, ["Longitude", "LONGITUDE", "Lon", "Long", "Lng", "GPS_LON", "X"])
    pci_col = find_column(dt_df.columns, ["LTE_UE_PCI", "PCI"])
    rsrp_col = find_column(dt_df.columns, ["LTE_UE_RSRP", "RSRP"])
    rsrq_col = find_column(dt_df.columns, ["LTE_UE_RSRQ", "RSRQ"])
    sinr_col = find_column(dt_df.columns, ["LTE_UE_SINR", "SINR"])
    time_col = find_column(dt_df.columns, ["Time", "Timestamp", "DateTime"])
    cell_col = find_column(dt_df.columns, ["ServingCellID", "CELL_NAME", "Cell Name", "CellName", "Cell ID", "Cell_ID", "CELL_ID", "Cell"])
    kpi_col = None
    kpi_mode = False
    rf_quality_mode = any(col is not None for col in [rsrp_col, rsrq_col, sinr_col])

    work = dt_df.copy()
    if (lat_col is None or lon_col is None) and cell_col is not None and cell_df is not None:
        numeric_candidates = []
        excluded_metric_names = {
            str(cell_col).strip().lower(),
            str(pci_col).strip().lower() if pci_col else "",
            "tac",
            "lac",
            "eci",
            "enbid",
            "enb id",
            "siteid",
            "site id",
        }
        for column in work.columns:
            column_key = str(column).strip().lower()
            if column == cell_col or column_key in excluded_metric_names:
                continue
            if is_rf_quality_column(column):
                continue
            numeric_series = pd.to_numeric(work[column], errors="coerce")
            if numeric_series.notna().sum() > 0:
                numeric_candidates.append((column, numeric_series.notna().sum()))
        if numeric_candidates:
            kpi_col = preferred_kpi_candidate(numeric_candidates)

        planned_cell_col = find_column(cell_df.columns, ["CELL_NAME", "Cell Name", "CellName", "Cell ID", "Cell_ID", "CELL_ID", "Cell"])
        planned_lat_col = find_column(cell_df.columns, ["Latitude", "LATITUDE", "Lat"])
        planned_lon_col = find_column(cell_df.columns, ["Longitude", "LONGITUDE", "Lon", "Long", "Lng"])
        if planned_cell_col and planned_lat_col and planned_lon_col:
            lookup_columns = [
                planned_cell_col,
                planned_lat_col,
                planned_lon_col,
                *[column for column in ["SITE_NAME", "PCI", "CARRIER", "Technology"] if column in cell_df.columns],
            ]
            cell_lookup = cell_df[lookup_columns].dropna(subset=[planned_cell_col]).drop_duplicates(subset=[planned_cell_col]).copy()
            cell_lookup["_JOIN_CELL_NAME"] = cell_lookup[planned_cell_col].astype(str).str.strip().str.upper()
            work["_JOIN_CELL_NAME"] = work[cell_col].astype(str).str.strip().str.upper()
            work = work.merge(cell_lookup, on="_JOIN_CELL_NAME", how="left", suffixes=("", "_CELL"))
            lat_col = planned_lat_col
            lon_col = planned_lon_col
            if pci_col is None and "PCI" in work.columns:
                pci_col = "PCI"
            kpi_mode = kpi_col is not None
            rf_quality_mode = not kpi_mode and any(col is not None for col in [rsrp_col, rsrq_col, sinr_col])

    required = [lat_col, lon_col]
    if any(col is None for col in required):
        return {"type": "FeatureCollection", "features": []}, {
            "error": "Missing Latitude/Longitude columns. For KPI/traffic files, include CELL_NAME so GeoMap can join to planned cells."
        }

    work["DT_LATITUDE"] = pd.to_numeric(work[lat_col], errors="coerce")
    work["DT_LONGITUDE"] = pd.to_numeric(work[lon_col], errors="coerce")
    for source_col, target_col in [
        (pci_col, "DT_PCI"),
        (rsrp_col, "DT_RSRP"),
        (rsrq_col, "DT_RSRQ"),
        (sinr_col, "DT_SINR"),
    ]:
        if source_col is not None:
            work[target_col] = pd.to_numeric(work[source_col], errors="coerce")
        else:
            work[target_col] = None

    if kpi_mode:
        work["DT_KPI_VALUE"] = pd.to_numeric(work[kpi_col], errors="coerce")
    else:
        work["DT_KPI_VALUE"] = pd.to_numeric(work["DT_RSRP"], errors="coerce")

    work = work.dropna(subset=["DT_LATITUDE", "DT_LONGITUDE"]).copy()
    if work.empty:
        return {"type": "FeatureCollection", "features": []}, {
            "error": "No map-ready rows found after loading the file. Check CELL_NAME values or Latitude/Longitude columns."
        }
    if kpi_mode:
        kpi_min = float(work["DT_KPI_VALUE"].min()) if work["DT_KPI_VALUE"].notna().any() else 0.0
        kpi_max = float(work["DT_KPI_VALUE"].max()) if work["DT_KPI_VALUE"].notna().any() else 1.0
    else:
        kpi_min = 0.0
        kpi_max = 1.0

    features = []
    dt_records = work.to_dict("records")
    for idx, row in enumerate(dt_records):
        pci = clean_value(row.get("DT_PCI", ""))
        rsrp = clean_value(row.get("DT_RSRP", ""))
        rsrq = clean_value(row.get("DT_RSRQ", ""))
        sinr = clean_value(row.get("DT_SINR", ""))
        kpi_value = clean_value(row.get("DT_KPI_VALUE", ""))
        try:
            kpi_numeric = float(kpi_value)
        except Exception:
            kpi_numeric = None
        heat_abs_weight = abs(kpi_numeric) if kpi_numeric is not None else 0.0
        kpi_weight = clamp((kpi_numeric - kpi_min) / (kpi_max - kpi_min)) if kpi_mode and kpi_numeric is not None and kpi_max > kpi_min else rsrp_weight(rsrp)
        props = {
            "index": int(idx),
            "time": clean_value(row.get(time_col, "")) if time_col else "",
            "servingCell": clean_value(row.get(cell_col, "")) if cell_col else "",
            "PCI": pci,
            "RSRP": rsrp,
            "RSRQ": rsrq,
            "SINR": sinr,
            "DATA_KIND": "traffic" if kpi_mode else ("rf_quality" if rf_quality_mode else "drive_test"),
            "KPI_NAME": kpi_col or "RSRP",
            "KPI_VALUE": kpi_value,
            "kpiAbsWeight": heat_abs_weight,
            "rsrpColor": rsrp_color(rsrp),
            "rsrqColor": rsrq_color(rsrq),
            "sinrColor": sinr_color(sinr),
            "pciColor": hash_color(pci),
            "kpiColor": kpi_heat_color(kpi_value, kpi_min, kpi_max) if kpi_mode else rsrp_color(rsrp),
            "rsrpWeight": rsrp_weight(rsrp),
            "rsrqWeight": rsrq_weight(rsrq),
            "sinrWeight": sinr_weight(sinr),
            "kpiWeight": kpi_weight,
        }
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["DT_LONGITUDE"]), float(row["DT_LATITUDE"])],
            },
            "properties": props,
        })

    summary = {
        "rows": len(work),
        "lat_col": lat_col,
        "lon_col": lon_col,
        "pci_col": pci_col,
        "rsrp_col": rsrp_col,
        "rsrq_col": rsrq_col,
        "sinr_col": sinr_col,
        "kpi_col": kpi_col,
        "mode": "cell_kpi" if kpi_mode else "drive_test",
        "rf_quality_mode": bool(rf_quality_mode),
    }
    return {"type": "FeatureCollection", "features": features}, summary


def atoll_prediction_inventory():
    if not ATOLL_PREDICTION_DIR.exists():
        return []
    wanted = {".shp", ".dbf", ".shx", ".prj", ".tif", ".tfw", ".cfg"}
    return [
        {
            "File": path.name,
            "Type": path.suffix.lower(),
            "Size MB": round(path.stat().st_size / (1024 * 1024), 2),
        }
        for path in sorted(ATOLL_PREDICTION_DIR.iterdir())
        if path.is_file() and path.suffix.lower() in wanted
    ]


def raster_color_legend(image_array, limit=7):
    visible_pixels = image_array[image_array[:, :, 3] > 0][:, :3]
    if visible_pixels.size == 0:
        return []
    quantized = ((visible_pixels.astype(np.uint16) // 32) * 32 + 16).clip(0, 255).astype(np.uint8)
    colors, counts = np.unique(quantized, axis=0, return_counts=True)
    order = np.argsort(counts)[::-1]
    total = max(int(counts.sum()), 1)
    legend = []
    for idx in order[:limit]:
        r, g, b = [int(value) for value in colors[idx]]
        legend.append({
            "color": f"#{r:02x}{g:02x}{b:02x}",
            "label": f"Raster class {len(legend) + 1}",
            "pct": round(float(counts[idx]) / total * 100, 1),
        })
    return legend


@st.cache_data(show_spinner=False)
def build_atoll_raster_overlay(raster_mtime_ns=None, world_mtime_ns=None):
    if not ATOLL_RASTER_FILE.exists() or not ATOLL_WORLD_FILE.exists():
        return {"available": False}

    world_values = [
        float(line.strip())
        for line in ATOLL_WORLD_FILE.read_text().splitlines()
        if line.strip()
    ]
    pixel_x, _, _, pixel_y, top_left_x, top_left_y = world_values

    image = Image.open(ATOLL_RASTER_FILE).convert("RGBA")
    original_width, original_height = image.size
    image.thumbnail((900, 900), Image.Resampling.NEAREST)
    width, height = image.size

    image_array = np.array(image)
    white_mask = (
        (image_array[:, :, 0] > 245)
        & (image_array[:, :, 1] > 245)
        & (image_array[:, :, 2] > 245)
    )
    image_array[:, :, 3] = np.where(white_mask, 0, 170).astype(np.uint8)
    legend = raster_color_legend(image_array)
    image = Image.fromarray(image_array, "RGBA")

    png_buffer = BytesIO()
    image.save(png_buffer, format="PNG", optimize=False)
    data_uri = "data:image/png;base64," + base64.b64encode(png_buffer.getvalue()).decode("ascii")

    left_x = top_left_x - pixel_x / 2
    top_y = top_left_y - pixel_y / 2
    right_x = left_x + pixel_x * original_width
    bottom_y = top_y + pixel_y * original_height
    coordinates = [
        nzmg_to_lonlat(left_x, top_y),
        nzmg_to_lonlat(right_x, top_y),
        nzmg_to_lonlat(right_x, bottom_y),
        nzmg_to_lonlat(left_x, bottom_y),
    ]

    return {
        "available": True,
        "url": data_uri,
        "coordinates": coordinates,
        "width": original_width,
        "height": original_height,
        "display_width": width,
        "display_height": height,
        "source": ATOLL_RASTER_FILE.name,
        "projection": "NZGD49 / New Zealand Map Grid",
        "legend": legend,
    }


def app_css():
    st.markdown(
        """
<style>
body, .stApp {
    background: #07101f;
    color: #f8fafc;
}
.block-container {
    padding-top: 1.2rem;
    max-width: 100%;
}
.ap-hero {
    border: 1px solid rgba(34,211,238,0.22);
    border-radius: 14px;
    padding: 16px 20px;
    background:
      radial-gradient(circle at 20% 20%, rgba(34,211,238,0.14), transparent 28%),
      linear-gradient(135deg, rgba(15,23,42,0.96), rgba(3,7,18,0.96));
    box-shadow: 0 18px 60px rgba(0,0,0,0.28);
    margin-bottom: 14px;
}
.ap-hero-logo {
    display: block;
    width: min(560px, 100%);
    height: auto;
    object-fit: contain;
    margin: 0;
}
.ap-hero p {
    color: #a7f3d0;
    margin: 10px 0 0 0;
    font-weight: 700;
}
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(8,13,29,0.96)) !important;
    border: 1px solid rgba(59,130,246,0.52) !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 14px 38px rgba(0,0,0,0.22) !important;
}
[data-testid="stMetric"] * {
    color: #f8fafc !important;
    opacity: 1 !important;
}
[data-testid="stMetricLabel"] p {
    color: #bae6fd !important;
    font-weight: 900 !important;
    letter-spacing: .2px;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 950 !important;
    text-shadow: 0 0 20px rgba(34,211,238,0.18);
}
div[data-testid="column"]:nth-of-type(1) [data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(20,83,45,0.82), rgba(8,13,29,0.96)) !important;
    border-color: rgba(16,185,129,0.74) !important;
}
div[data-testid="column"]:nth-of-type(2) [data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(30,64,175,0.72), rgba(8,13,29,0.96)) !important;
    border-color: rgba(59,130,246,0.74) !important;
}
div[data-testid="column"]:nth-of-type(3) [data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(126,34,206,0.62), rgba(8,13,29,0.96)) !important;
    border-color: rgba(168,85,247,0.72) !important;
}
div[data-testid="column"]:nth-of-type(4) [data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(180,83,9,0.62), rgba(8,13,29,0.96)) !important;
    border-color: rgba(245,158,11,0.72) !important;
}
div[data-testid="column"]:nth-of-type(5) [data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(190,24,93,0.55), rgba(8,13,29,0.96)) !important;
    border-color: rgba(244,114,182,0.68) !important;
}
div[data-testid="column"]:nth-of-type(6) [data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(15,118,110,0.62), rgba(8,13,29,0.96)) !important;
    border-color: rgba(20,184,166,0.72) !important;
}
[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
}
.ap-kpi-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(140px, 1fr));
    gap: 12px;
    margin: 10px 0 16px 0;
}
.ap-kpi-card {
    min-height: 92px;
    padding: 15px 16px;
    border-radius: 12px;
    border: 1px solid rgba(59,130,246,0.52);
    background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(8,13,29,0.96));
    box-shadow: 0 16px 42px rgba(0,0,0,0.26);
}
.ap-kpi-card span {
    display:block;
    color:#e0f2fe;
    font-size:12px;
    font-weight:950;
    letter-spacing:.35px;
    text-transform:uppercase;
}
.ap-kpi-card strong {
    display:block;
    margin-top:10px;
    color:#ffffff;
    font-size:30px;
    line-height:1;
    font-weight:950;
    text-shadow:0 0 22px rgba(34,211,238,0.18);
}
.ap-kpi-card.sites {
    background:linear-gradient(135deg, rgba(20,83,45,0.82), rgba(8,13,29,0.96));
    border-color:rgba(16,185,129,0.74);
}
.ap-kpi-card.cells {
    background:linear-gradient(135deg, rgba(30,64,175,0.74), rgba(8,13,29,0.96));
    border-color:rgba(59,130,246,0.76);
}
.ap-kpi-card.lte {
    background:linear-gradient(135deg, rgba(126,34,206,0.62), rgba(8,13,29,0.96));
    border-color:rgba(168,85,247,0.74);
}
.ap-kpi-card.nr {
    background:linear-gradient(135deg, rgba(180,83,9,0.62), rgba(8,13,29,0.96));
    border-color:rgba(245,158,11,0.72);
}
.ap-kpi-card.vendors {
    background:linear-gradient(135deg, rgba(14,116,144,0.66), rgba(8,13,29,0.96));
    border-color:rgba(34,211,238,0.72);
}
.ap-kpi-card.clusters {
    background:linear-gradient(135deg, rgba(190,24,93,0.58), rgba(8,13,29,0.96));
    border-color:rgba(244,114,182,0.72);
}
@media (max-width: 1200px) {
    .ap-kpi-grid { grid-template-columns: repeat(3, minmax(140px, 1fr)); }
}
@media (max-width: 720px) {
    .ap-kpi-grid { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
}
section[data-testid="stSidebar"] {
    overflow-y: auto !important;
}
section[data-testid="stSidebar"] > div {
    overflow-y: auto !important;
    max-height: 100vh !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    overflow-y: auto !important;
    max-height: calc(100vh - 32px) !important;
    padding-bottom: 32px;
}
div[data-testid="stAlert"] {
    background: rgba(8, 47, 73, 0.88) !important;
    border: 1px solid rgba(34, 211, 238, 0.34) !important;
    border-radius: 12px !important;
    color: #f8fafc !important;
}
div[data-testid="stAlert"] * {
    color: #f8fafc !important;
}
div[data-testid="stCaptionContainer"] {
    color: #c4f1ff !important;
    font-weight: 700;
}
div[data-testid="stExpander"] {
    background: rgba(8, 13, 29, 0.86) !important;
    border: 1px solid rgba(34, 211, 238, 0.20) !important;
    border-radius: 14px !important;
    box-shadow: 0 14px 42px rgba(0, 0, 0, 0.22);
}
div[data-testid="stExpander"] details,
div[data-testid="stExpander"] summary {
    background: transparent !important;
    color: #f8fafc !important;
}
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span {
    color: #e0f2fe !important;
    font-weight: 900 !important;
}
div[data-testid="stFileUploader"] {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.94)) !important;
    border: 1px solid rgba(34, 211, 238, 0.42) !important;
    border-radius: 14px !important;
    padding: 12px !important;
    box-shadow: 0 14px 38px rgba(0,0,0,0.24);
}
div[data-testid="stFileUploader"] section {
    background: rgba(2, 6, 23, 0.86) !important;
    border: 1px dashed rgba(125, 211, 252, 0.58) !important;
    border-radius: 12px !important;
}
div[data-testid="stFileUploader"] * {
    color: #f8fafc !important;
    opacity: 1 !important;
}
div[data-testid="stFileUploader"] button {
    background: #061b3f !important;
    color: #ffffff !important;
    border: 1px solid rgba(59, 130, 246, 0.65) !important;
    border-radius: 10px !important;
}
div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] *,
div[data-testid="stFileUploader"] [data-baseweb],
div[data-testid="stFileUploader"] [role="button"],
div[data-testid="stFileUploader"] li {
    background: rgba(15, 23, 42, 0.96) !important;
    color: #e0f2fe !important;
    border-color: rgba(125, 211, 252, 0.48) !important;
}
div[data-testid="stFileUploader"] svg {
    color: #67e8f9 !important;
    fill: #67e8f9 !important;
}
div[data-testid="stStatusWidget"],
div[data-testid="stSpinner"],
div[data-testid="stProgress"] {
    color: #f8fafc !important;
}
div[data-testid="stProgress"] > div {
    background: rgba(15, 23, 42, 0.98) !important;
    border: 1px solid rgba(34, 211, 238, 0.34) !important;
    border-radius: 12px !important;
    padding: 6px !important;
}
div[data-testid="stProgress"] [role="progressbar"] {
    background: linear-gradient(90deg, #22d3ee, #22c55e, #fbbf24) !important;
}
.stApp [aria-busy="true"] {
    color: #f8fafc !important;
}
.ap-dt-card {
    margin: 16px 0 12px 0;
    padding: 14px;
    border: 1px solid rgba(34, 211, 238, 0.46);
    border-radius: 14px;
    background:
      radial-gradient(circle at 8% 20%, rgba(34,211,238,0.16), transparent 24%),
      linear-gradient(135deg, rgba(8,13,29,0.98), rgba(2,6,23,0.94));
    box-shadow: 0 18px 48px rgba(0,0,0,0.28);
}
.ap-dt-card h3 {
    margin: 0 0 4px 0;
    color: #f8fafc;
    font-size: 18px;
}
.ap-dt-card p {
    margin: 0;
    color: #bae6fd;
    font-weight: 700;
}

/* Compact top command band: brand/upload left, processing status right. */
.ap-hero {
    min-height: 122px;
    padding: 12px 14px;
    display: flex;
    align-items: center;
    margin-bottom: 8px;
}
.ap-hero-logo { width: min(430px, 100%); }
.ap-hero p { display:none; }
[data-testid="stFileUploader"] {
    border: 1px solid rgba(250,204,21,0.28);
    border-radius: 12px;
    padding: 8px 10px;
    background: rgba(2,6,23,0.58);
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] p {
    color: #f8fafc !important;
    font-weight: 800 !important;
}
[data-testid="stProgress"] { margin-top: 8px; }
.ap-status-spacer { height: 122px; }
@media (max-width: 900px) {
    .ap-status-spacer { height: 0; }
}
.ap-kpi-grid { margin-top: 8px; margin-bottom: 10px; }
</style>
""",
        unsafe_allow_html=True,
    )


def map_html(cells_geojson, shells_geojson, dt_geojson, anr_summary, atoll_overlay, center_lon, center_lat):
    cells_json = json.dumps(cells_geojson)
    shells_json = json.dumps(shells_geojson)
    dt_json = json.dumps(dt_geojson)
    anr_json = json.dumps(anr_summary)
    atoll_json = json.dumps(atoll_overlay)
    brand_wordmark_url = image_data_uri(str(BRAND_WORDMARK_FILE))
    brand_mark_url = image_data_uri(str(BRAND_MARK_FILE))

    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
  <style>
    html, body { margin:0; height:100%; background:#07101f; font-family: Segoe UI, Arial, sans-serif; }
    #map { position:absolute; inset:0; border-radius:16px; overflow:hidden; }
    #networkCanvas {
      position:absolute; inset:0; z-index:2; pointer-events:none; border-radius:16px;
    }
    .maplibregl-ctrl-top-right { top:12px; right:12px; }
    .maplibregl-ctrl-group {
      background:rgba(8,13,29,0.92) !important;
      border:1px solid rgba(34,211,238,0.35) !important;
      border-radius:12px !important;
      overflow:hidden;
      box-shadow:0 14px 36px rgba(0,0,0,0.32) !important;
    }
    .maplibregl-ctrl-group button {
      background:#f8fafc !important;
      border-color:rgba(59,130,246,0.25) !important;
      width:34px !important;
      height:34px !important;
      filter:none !important;
    }
    .maplibregl-ctrl-group button:hover {
      background:#dbeafe !important;
    }
    .maplibregl-ctrl-attrib {
      background:rgba(2,6,23,0.72) !important;
      color:#dbeafe !important;
      border-radius:10px 0 0 0 !important;
      font-weight:700;
    }
    .maplibregl-ctrl-attrib a { color:#67e8f9 !important; }
    .panel {
      position:absolute; z-index:5; left:18px; top:18px; width:330px;
      background:rgba(9,15,31,0.92); border:1px solid rgba(34,211,238,0.28);
      border-radius:14px; color:#f8fafc; padding:14px; box-shadow:0 18px 60px rgba(0,0,0,0.34);
      backdrop-filter: blur(10px); max-height:calc(100% - 36px); overflow-y:auto; box-sizing:border-box;
    }
    .panel::-webkit-scrollbar { width:8px; }
    .panel::-webkit-scrollbar-track { background:rgba(15,23,42,0.55); border-radius:10px; }
    .panel::-webkit-scrollbar-thumb { background:rgba(34,211,238,0.45); border-radius:10px; }
    .scroll-tools {
      position:sticky; bottom:-4px; z-index:6; display:grid; grid-template-columns:1fr 1fr; gap:8px;
      margin-top:10px; padding-top:10px;
      background:linear-gradient(180deg, rgba(9,15,31,0), rgba(9,15,31,0.98) 32%);
    }
    .scroll-tools button {
      padding:8px; min-height:34px; border-color:rgba(34,211,238,0.45);
      background:rgba(6,27,63,0.96); color:#dffcff; font-size:12px;
    }
    .panel h2 { margin:0 0 8px 0; font-size:17px; }
    .brand-lockup {
      display:flex; align-items:center; gap:10px; margin-bottom:12px;
      padding:10px; border:1px solid rgba(34,211,238,0.28); border-radius:12px;
      background:linear-gradient(135deg, rgba(8,47,73,0.74), rgba(15,23,42,0.66));
    }
    .brand-mark-img {
      width:48px; height:48px; object-fit:cover; flex:0 0 auto;
      border-radius:10px; border:1px solid rgba(45,212,191,0.55);
      box-shadow:0 12px 28px rgba(34,211,238,0.22);
    }
    .brand-name { color:#f8fafc; font-weight:950; font-size:15px; line-height:1.1; }
    .brand-sub { color:#bae6fd; font-size:11px; font-weight:800; margin-top:3px; }
    body.cursor-select #map,
    body.cursor-select #map canvas,
    body.cursor-select #map .maplibregl-canvas { cursor: crosshair !important; }
    body.cursor-pan #map,
    body.cursor-pan #map canvas,
    body.cursor-pan #map .maplibregl-canvas { cursor: grab !important; }
    body.cursor-pan #map:active,
    body.cursor-pan #map canvas:active,
    body.cursor-pan #map .maplibregl-canvas:active { cursor: grabbing !important; }
    .hint {
      color:#dcfce7; font-size:12px; line-height:1.5; margin-bottom:12px;
      background:rgba(20,83,45,0.34); border:1px solid rgba(134,239,172,0.34);
      border-radius:10px; padding:9px 10px; font-weight:800;
    }
    .mini-hint {
      margin-top:-2px; margin-bottom:8px; padding:7px 9px; font-size:11px;
      color:#bae6fd; background:rgba(15,23,42,0.7); border-color:rgba(34,211,238,0.24);
    }
    .row { display:flex; gap:10px; margin-bottom:10px; }
    .quick-row {
      gap:12px; margin-bottom:12px; padding:8px;
      border:1px solid rgba(125,211,252,0.18); border-radius:12px;
      background:rgba(8,47,73,0.18);
    }
    button {
      flex:1; border:1px solid rgba(59,130,246,0.55); color:#fff; background:#061b3f;
      border-radius:8px; padding:11px 10px; font-weight:800; cursor:pointer;
    }
    .quick-row button {
      min-height:42px; background:linear-gradient(135deg, rgba(8,145,178,0.92), rgba(14,116,144,0.72));
      border-color:rgba(125,211,252,0.68); box-shadow:0 10px 24px rgba(8,145,178,0.16);
    }
    #searchBtn {
      background:linear-gradient(135deg, #06b6d4, #0e7490);
      border-color:#67e8f9; box-shadow:0 12px 28px rgba(6,182,212,0.24);
    }
    #homeBtn {
      background:linear-gradient(135deg, #10b981, #0f766e);
      border-color:#6ee7b7; box-shadow:0 12px 28px rgba(16,185,129,0.22);
    }
    #fitBtn {
      background:linear-gradient(135deg, #3b82f6, #1d4ed8);
      border-color:#93c5fd; box-shadow:0 12px 28px rgba(59,130,246,0.22);
    }
    #cleanMapBtn {
      background:linear-gradient(135deg, #f59e0b, #b45309);
      border-color:#fde68a; color:#08111f; box-shadow:0 12px 28px rgba(245,158,11,0.22);
    }
    .quick-row button:hover {
      filter:brightness(1.08);
      transform:translateY(-1px);
    }
    button.active { background:#16a34a; border-color:#86efac; }
    button.warn { background:#7f1d1d; border-color:#f87171; }
    button.gold { background:linear-gradient(135deg,#f5b84b,#f97316); color:#06111f; border:0; }
    input, textarea {
      width:100%; box-sizing:border-box; border:1px solid rgba(226,232,240,0.7);
      background:#0f172a; color:#e0f2fe; border-radius:10px; padding:10px; margin-bottom:10px;
      outline:none;
    }
    textarea {
      min-height:76px; max-height:140px; resize:vertical; font-family:Consolas, "Segoe UI", monospace;
      font-size:12px; line-height:1.45;
    }
    input[type="range"] {
      padding:0; margin:4px 0 8px 0; background:transparent; accent-color:#22d3ee;
      border:0;
    }
    select {
      width:100%; box-sizing:border-box; border:1px solid rgba(34,211,238,0.35);
      background:#0f172a; color:#e0f2fe; border-radius:10px; padding:10px; margin:6px 0 10px 0;
      outline:none; font-weight:800;
    }
    .section-title {
      margin:14px 0 8px 0; padding:8px 10px; border:1px solid rgba(186,230,253,0.16);
      border-left:4px solid #bae6fd;
      border-radius:8px; background:linear-gradient(135deg, rgba(186,230,253,0.12), rgba(15,23,42,0.64)); color:#f0f9ff;
      font-size:11px; font-weight:900; letter-spacing:.45px; text-transform:uppercase;
    }
    .section-title.danger {
      border-left-color:#fda4af; background:linear-gradient(135deg, rgba(244,63,94,0.20), rgba(15,23,42,0.68));
    }
    .section-title.map-section {
      border-left-color:#99f6e4; background:linear-gradient(135deg, rgba(45,212,191,0.18), rgba(15,23,42,0.68));
    }
    .section-title.rf-section {
      border-left-color:#fde68a; background:linear-gradient(135deg, rgba(245,158,11,0.18), rgba(15,23,42,0.68));
    }
    .section-title.vnr-section {
      border-left-color:#ddd6fe; background:linear-gradient(135deg, rgba(168,85,247,0.16), rgba(15,23,42,0.68));
    }
    .section-title.dt-section {
      border-left-color:#7dd3fc; background:linear-gradient(135deg, rgba(56,189,248,0.18), rgba(15,23,42,0.68));
    }
    .section-title.filter-section {
      border-left-color:#bfdbfe; background:linear-gradient(135deg, rgba(96,165,250,0.16), rgba(15,23,42,0.68));
    }
    .section-title.color-section {
      border-left-color:#7dd3fc; background:linear-gradient(135deg, rgba(14,165,233,0.24), rgba(15,23,42,0.70)); color:#e0f7ff;
    }
    .section-title.layers-section {
      border-left-color:#86efac; background:linear-gradient(135deg, rgba(34,197,94,0.22), rgba(15,23,42,0.70)); color:#ecfdf5;
    }
    .section-title.pointer-section {
      border-left-color:#c4b5fd; background:linear-gradient(135deg, rgba(139,92,246,0.22), rgba(15,23,42,0.70)); color:#f5f3ff;
    }
    .section-title.shell-section {
      border-left-color:#fcd34d; background:linear-gradient(135deg, rgba(245,158,11,0.24), rgba(15,23,42,0.70)); color:#fffbeb;
    }
    .section-title.marker-section {
      border-left-color:#f0abfc; background:linear-gradient(135deg, rgba(217,70,239,0.20), rgba(15,23,42,0.70)); color:#fdf4ff;
    }
    .section-title.area-section {
      border-left-color:#5eead4; background:linear-gradient(135deg, rgba(20,184,166,0.24), rgba(15,23,42,0.70)); color:#f0fdfa;
    }
    .section-title.builder-section {
      border-left-color:#fb923c; background:linear-gradient(135deg, rgba(249,115,22,0.22), rgba(15,23,42,0.70)); color:#fff7ed;
    }
    .section-title.ncell-filter-section {
      border-left-color:#93c5fd; background:linear-gradient(135deg, rgba(59,130,246,0.22), rgba(15,23,42,0.70)); color:#eff6ff;
    }

    .ap-module {
      margin:12px 0 0 0;
      border:1px solid rgba(34,211,238,0.24);
      border-radius:12px;
      background:linear-gradient(135deg, rgba(8,13,29,0.82), rgba(2,6,23,0.64));
      overflow:hidden;
      box-shadow:0 12px 30px rgba(0,0,0,0.20);
    }
    .ap-module[open] {
      border-color:rgba(34,211,238,0.44);
      box-shadow:0 16px 38px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.04);
    }
    .ap-module > summary {
      list-style:none;
      cursor:pointer;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:8px;
      padding:9px 10px;
      color:#f8fafc;
      font-size:11px;
      line-height:1;
      font-weight:950;
      letter-spacing:.55px;
      text-transform:uppercase;
      background:linear-gradient(135deg, rgba(30,41,59,0.86), rgba(15,23,42,0.72));
      border-left:4px solid #22d3ee;
      user-select:none;
    }
    .ap-module > summary::-webkit-details-marker { display:none; }
    .ap-module > summary::after {
      content:'+';
      width:20px;
      height:20px;
      display:grid;
      place-items:center;
      border-radius:999px;
      color:#03111f;
      background:#67e8f9;
      font-size:15px;
      font-weight:950;
      box-shadow:0 0 18px rgba(34,211,238,0.28);
    }
    .ap-module[open] > summary::after { content:'−'; }
    .ap-module-body { padding:10px; }
    .ap-module.anr > summary { border-left-color:#c4b5fd; }
    .ap-module.area > summary { border-left-color:#5eead4; }
    .ap-module.audit > summary { border-left-color:#fb923c; }
    .ap-module.ai > summary { border-left-color:#22c55e; }
    .ap-module.future > summary { border-left-color:#f472b6; }
    .ap-future-grid { display:grid; grid-template-columns:1fr 1fr; gap:7px; }
    .ap-future-pill {
      padding:8px 9px;
      border-radius:10px;
      border:1px solid rgba(125,211,252,0.28);
      background:rgba(15,23,42,0.78);
      color:#dffcff;
      font-size:11px;
      font-weight:900;
      text-align:center;
    }

    .toggle-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }
    .toggle-grid button { min-height:36px; padding:8px; font-size:12px; }
    .three-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; margin-bottom:8px; }
    .three-grid button { min-height:34px; padding:8px; font-size:11px; }
    .mode-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }
    .mode-grid button { min-height:36px; padding:8px; font-size:12px; }
    .mini {
      display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:8px 0 10px 0;
    }
    .stat {
      background:rgba(15,23,42,0.78); border:1px solid rgba(59,130,246,0.28);
      border-radius:10px; padding:8px; font-size:12px;
    }
    .stat b { display:block; color:#67e8f9; font-size:18px; margin-top:3px; }
    #selectedList {
      color:#f8fafc; font-size:12px; line-height:1.45; max-height:86px; overflow:auto;
      background:rgba(15,23,42,0.92); border:1px solid rgba(125,211,252,0.32);
      border-radius:10px; padding:8px; margin-top:8px;
    }
    .small-list {
      color:#f8fafc; font-size:12px; line-height:1.45; max-height:72px; overflow:auto;
      background:rgba(15,23,42,0.84); border:1px solid rgba(251,113,133,0.34);
      border-radius:10px; padding:8px; margin:6px 0 10px 0;
    }
    .link-row {
      display:flex; align-items:center; justify-content:space-between; gap:8px;
      border-bottom:1px solid rgba(148,163,184,0.13); padding:4px 0;
    }
    .link-row:last-child { border-bottom:0; }
    .link-target { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .link-pill {
      flex:0 0 auto; border-radius:999px; padding:2px 7px; font-size:10px; font-weight:900;
      color:#03111f; background:#67e8f9;
    }
    .link-pill.intra { background:#22c55e; color:#03130a; }
    .link-pill.inter { background:#38bdf8; color:#03111f; }
    .link-pill.irat { background:#fb923c; color:#1f0a03; }
    .link-pill.issue { background:#fb7185; color:#1f0508; }
    .link-pill.warn { background:#facc15; color:#1f1600; }
    .link-pill.ok { background:#34d399; color:#03130a; }
    .hidden-metrics { display:none; }
    .maplibregl-popup-content {
      background:#0b1224; color:#f8fafc; border:1px solid rgba(34,211,238,0.34);
      border-radius:12px; box-shadow:0 18px 50px rgba(0,0,0,0.45);
    }
    .maplibregl-popup-close-button { color:#fff; font-size:20px; }
    .ap-popup-title { font-size:15px; font-weight:900; color:#67e8f9; margin-bottom:6px; }
    .ap-popup-row { font-size:12px; margin:2px 0; color:#dbeafe; }
    .compare-strip {
      position:absolute; z-index:4; left:390px; right:auto; top:14px;
      width:min(620px, calc(100% - 640px));
      display:grid; grid-template-columns:1fr .9fr .72fr; gap:8px;
      pointer-events:none;
    }
    .compare-card {
      background:rgba(9,15,31,0.78); border:1px solid rgba(34,211,238,0.22);
      box-shadow:0 12px 34px rgba(0,0,0,0.24); border-radius:10px; padding:7px 10px;
      color:#e0f2fe; backdrop-filter:blur(8px);
    }
    .compare-card:nth-child(1) {
      background:linear-gradient(135deg, rgba(14,116,144,0.82), rgba(9,15,31,0.86));
      border-color:rgba(34,211,238,0.48);
    }
    .compare-card:nth-child(2) {
      background:linear-gradient(135deg, rgba(146,64,14,0.72), rgba(9,15,31,0.9));
      border-color:rgba(245,158,11,0.48);
    }
    .compare-card:nth-child(3) {
      background:linear-gradient(135deg, rgba(88,28,135,0.72), rgba(9,15,31,0.9));
      border-color:rgba(168,85,247,0.46);
    }
    .compare-card span { display:block; color:#93c5fd; font-size:9px; font-weight:900; text-transform:uppercase; letter-spacing:.5px; }
    .compare-card b { display:block; margin-top:2px; color:#fff; font-size:14px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .map-actionbar {
      position:absolute; z-index:4; left:390px; right:74px; top:72px;
      display:grid; grid-template-columns:120px minmax(140px, 1.05fr) minmax(145px, 1.05fr) repeat(6, minmax(84px, .72fr)) 130px;
      gap:8px; align-items:center;
      pointer-events:auto;
      background:linear-gradient(135deg, rgba(8,13,29,0.84), rgba(15,23,42,0.62));
      border:1px solid rgba(34,211,238,0.26);
      border-radius:12px; padding:8px;
      box-shadow:0 14px 42px rgba(0,0,0,0.25);
      backdrop-filter:blur(10px);
    }
    .map-actionbar .bar-label {
      color:#fbbf24; font-size:10px; font-weight:950; letter-spacing:.5px; text-transform:uppercase;
      white-space:nowrap;
    }
    .map-actionbar select,
    .map-actionbar button,
    .map-actionbar input[type="range"] {
      margin:0; min-height:34px;
    }
    .map-actionbar select {
      padding:8px 10px; font-size:11px;
      background:#0b1830; border-color:rgba(34,211,238,0.42);
    }
    .map-actionbar button {
      padding:8px 10px; font-size:11px; min-width:0;
    }
    .map-actionbar input[type="range"] {
      width:100%; accent-color:#f59e0b;
    }
    .heat-tuning {
      grid-column:1 / -1;
      display:grid;
      grid-template-columns:110px repeat(4, minmax(140px, 1fr));
      gap:8px;
      align-items:center;
      padding-top:4px;
      border-top:1px solid rgba(34,211,238,0.16);
    }
    .heat-tuning span,
    .heat-tuning label {
      color:#c7d2fe;
      font-size:10px;
      font-weight:900;
      text-transform:uppercase;
      letter-spacing:.35px;
    }
    .heat-tuning label {
      display:grid;
      grid-template-columns:68px 1fr 34px;
      gap:7px;
      align-items:center;
      padding:4px 8px;
      border:1px solid rgba(56,189,248,0.24);
      border-radius:9px;
      background:rgba(2,6,23,0.42);
    }
    .heat-tuning b {
      color:#f8fafc;
      font-size:10px;
      text-align:right;
      white-space:nowrap;
    }
    .compare-note {
      position:absolute; z-index:4; left:372px; right:18px; bottom:16px;
      pointer-events:none; color:#dcfce7; font-size:12px; font-weight:900;
      background:rgba(4,47,46,0.9); border:1px solid rgba(45,212,191,0.5);
      border-radius:12px; padding:10px 13px; backdrop-filter:blur(8px);
      box-shadow:0 14px 42px rgba(0,0,0,0.28);
      display:none;
    }
    #floatingLegend, #dtFloatingLegend {
      position:absolute; z-index:4; right:18px; width:286px; overflow:auto;
      background:rgba(2,6,23,0.92); border:1px solid rgba(34,211,238,0.42);
      border-radius:14px; padding:12px; color:#f8fafc; box-shadow:0 18px 52px rgba(0,0,0,0.38);
      backdrop-filter:blur(10px);
    }
    #dtFloatingLegend { bottom:260px; max-height:280px; }
    #floatingLegend { bottom:24px; max-height:220px; }
    #floatingLegend::-webkit-scrollbar, #dtFloatingLegend::-webkit-scrollbar { width:8px; }
    #floatingLegend::-webkit-scrollbar-track, #dtFloatingLegend::-webkit-scrollbar-track { background:rgba(15,23,42,0.65); border-radius:10px; }
    #floatingLegend::-webkit-scrollbar-thumb, #dtFloatingLegend::-webkit-scrollbar-thumb { background:rgba(34,211,238,0.48); border-radius:10px; }
    @media (max-width: 980px) {
      .compare-strip, .compare-note { left:18px; right:18px; width:auto; }
      .compare-strip { grid-template-columns:1fr 1fr; top:auto; bottom:54px; }
      .map-actionbar { display:none; }
      .compare-note { display:none; }
      #floatingLegend, #dtFloatingLegend { display:none; }
    }
    .legend-row {
      display:grid; grid-template-columns:18px 1fr auto; align-items:center; gap:8px;
      color:#cbd5e1; font-size:12px; padding:4px 0;
    }
    .legend-separator {
      height:1px;
      margin:10px 0;
      background:linear-gradient(90deg, rgba(34,211,238,0.05), rgba(34,211,238,0.42), rgba(34,211,238,0.05));
    }
    .swatch { width:16px; height:16px; border-radius:5px; border:1px solid rgba(255,255,255,0.32); }

    /* Phase 2 sidebar polish: black cockpit, yellow/blue controls, white/black text. */
    .panel {
      left:0; top:0; width:306px; max-height:100%; padding:10px;
      border-radius:0 16px 16px 0; border:1px solid rgba(250,204,21,0.62);
      background:linear-gradient(180deg, rgba(2,6,23,0.98), rgba(0,12,24,0.96));
      box-shadow:12px 0 44px rgba(0,0,0,0.45);
    }
    .panel::-webkit-scrollbar-thumb { background:rgba(250,204,21,0.72); }
    .brand-lockup {
      justify-content:center; text-align:center; background:#020817;
      border-color:rgba(250,204,21,0.54); border-radius:10px; padding:10px 8px;
    }
    .brand-mark-img { width:54px; height:54px; border-color:rgba(250,204,21,0.7); box-shadow:0 12px 32px rgba(250,204,21,0.16); }
    .brand-name { color:#ffffff; font-size:17px; letter-spacing:.5px; text-transform:uppercase; }
    .brand-sub { color:#facc15; letter-spacing:.9px; text-transform:uppercase; }
    input, textarea, select {
      background:#020817; border-color:rgba(250,204,21,0.38); color:#ffffff; border-radius:7px;
    }
    input::placeholder, textarea::placeholder { color:rgba(255,255,255,0.62); }
    .section-title {
      margin:12px 0 7px 0; padding:7px 8px; border-radius:0; border:0; border-top:1px solid rgba(250,204,21,0.25);
      background:transparent; color:#facc15; font-size:10px; letter-spacing:.55px;
    }
    .section-title::before { content:'▸ '; color:#facc15; }
    .section-title.color-section::before { content:'▸ '; }
    .section-title.layers-section::before { content:'▸ '; }
    .section-title.pointer-section::before { content:'▸ '; }
    .section-title.filter-section::before { content:'▸ '; }
    .section-title.shell-section::before { content:'▸ '; }
    .section-title.marker-section::before { content:'▸ '; }
    button {
      border-radius:7px; border:1px solid rgba(250,204,21,0.55);
      background:linear-gradient(180deg,#facc15,#eab308); color:#07101f;
      min-height:34px; padding:8px 9px; font-size:12px;
      box-shadow:none;
    }
    .row button:first-child, .quick-row button:first-child,
    .toggle-grid button:nth-child(odd), .three-grid button:nth-child(odd), .mode-grid button:nth-child(odd) {
      background:linear-gradient(180deg,#2563eb,#1d4ed8); color:#ffffff; border-color:rgba(96,165,250,0.8);
    }
    button.active {
      background:linear-gradient(180deg,#2563eb,#1d4ed8); color:#ffffff; border-color:#93c5fd;
      box-shadow:0 0 0 1px rgba(147,197,253,0.18) inset;
    }
    button.warn, button.gold, #cleanMapBtn {
      background:linear-gradient(180deg,#facc15,#eab308); color:#07101f; border-color:#fde047;
    }
    #searchBtn, #fitBtn { background:linear-gradient(180deg,#2563eb,#1d4ed8); color:#ffffff; border-color:#93c5fd; }
    #homeBtn { background:linear-gradient(180deg,#facc15,#eab308); color:#07101f; border-color:#fde047; }
    .quick-row { background:rgba(2,6,23,0.68); border-color:rgba(250,204,21,0.16); padding:5px; gap:7px; }
    .toggle-grid, .three-grid, .mode-grid { gap:7px; }
    .three-grid { grid-template-columns:repeat(2, 1fr); }
    .carrier-grid { grid-template-columns:repeat(2, 1fr); }
    .future-carrier { display:none !important; }
    .hint, .mini-hint, .stat, #selectedList, .small-list {
      background:rgba(2,6,23,0.82); border-color:rgba(250,204,21,0.22); color:#ffffff;
    }
    .stat b { color:#facc15; }
    .ap-module {
      margin:8px 0; border:1px solid rgba(250,204,21,0.28); border-radius:8px; background:rgba(2,6,23,0.72); overflow:hidden;
    }
    .ap-module summary {
      cursor:pointer; list-style:none; padding:9px 10px; color:#07101f; background:linear-gradient(180deg,#facc15,#eab308);
      font-weight:950; text-transform:uppercase; font-size:11px;
    }
    .ap-module summary::-webkit-details-marker { display:none; }
    .ap-module summary::after { content:'›'; float:right; font-size:18px; line-height:10px; }
    .ap-module[open] summary::after { content:'⌄'; }
    .ap-module-body { padding:9px 8px 2px 8px; }
    .scroll-tools { background:linear-gradient(180deg, rgba(2,6,23,0), rgba(2,6,23,0.98) 30%); }
    /* Keep the four high-use command buttons distinct. */
    #searchBtn {
      background:linear-gradient(135deg, #06b6d4, #0e7490) !important;
      color:#ffffff !important; border-color:#67e8f9 !important;
      box-shadow:0 12px 28px rgba(6,182,212,0.22) !important;
    }
    #homeBtn {
      background:linear-gradient(135deg, #10b981, #0f766e) !important;
      color:#ffffff !important; border-color:#6ee7b7 !important;
      box-shadow:0 12px 28px rgba(16,185,129,0.20) !important;
    }
    #fitBtn {
      background:linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
      color:#ffffff !important; border-color:#93c5fd !important;
      box-shadow:0 12px 28px rgba(59,130,246,0.22) !important;
    }
    #cleanMapBtn {
      background:linear-gradient(135deg, #f59e0b, #b45309) !important;
      color:#08111f !important; border-color:#fde68a !important;
      box-shadow:0 12px 28px rgba(245,158,11,0.22) !important;
    }
  
/* Compact top command band: brand/upload left, processing status right. */
.ap-hero {
    min-height: 122px;
    padding: 12px 14px;
    display: flex;
    align-items: center;
    margin-bottom: 8px;
}
.ap-hero-logo { width: min(430px, 100%); }
.ap-hero p { display:none; }
[data-testid="stFileUploader"] {
    border: 1px solid rgba(250,204,21,0.28);
    border-radius: 12px;
    padding: 8px 10px;
    background: rgba(2,6,23,0.58);
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] p {
    color: #f8fafc !important;
    font-weight: 800 !important;
}
[data-testid="stProgress"] { margin-top: 8px; }
.ap-kpi-grid { margin-top: 8px; margin-bottom: 10px; }
</style>
</head>
<body>
  <div id="map"></div>
  <canvas id="networkCanvas"></canvas>
  <div class="compare-strip">
    <div class="compare-card"><span>Traffic / KPI</span><b id="stripDtLayer">Traffic heatmap</b></div>
    <div class="compare-card"><span>Coverage</span><b id="stripAtoll">Coverage ON</b></div>
    <div class="compare-card"><span>Map Points</span><b id="stripDtCount">0 cells</b></div>
  </div>
  <div class="map-actionbar" id="dtAtollToolbar">
    <div class="bar-label">Traffic / Coverage</div>
    <select id="dtColorMode">
      <option value="kpiColor">KPI / Traffic</option>
      <option value="rsrpColor">DT RSRP</option>
      <option value="rsrqColor">DT RSRQ</option>
      <option value="sinrColor">DT SINR</option>
      <option value="pciColor">DT PCI Identity</option>
    </select>
    <select id="dtViewMode">
      <option value="both">Heatmap + points</option>
      <option value="heatmap">Heatmap only</option>
      <option value="points">Points only</option>
    </select>
    <button id="dtBtn">Traffic OFF</button>
    <button id="dtFitBtn">Fit Traffic</button>
    <button id="atollBtn">Coverage OFF</button>
    <button id="atollFitBtn">Fit Coverage</button>
    <button id="compareFitBtn">Compare</button>
    <button id="clearViewBtn">Clean</button>
    <div class="heat-tuning">
      <span>Heat Tuning</span>
      <label>Radius <input id="heatRadius" type="range" min="10" max="120" value="42" title="Heatmap radius" /><b id="heatRadiusValue">42px</b></label>
      <label>Intensity <input id="heatIntensity" type="range" min="0.2" max="5" step="0.1" value="1.2" title="Heatmap intensity" /><b id="heatIntensityValue">1.2x</b></label>
      <label>Opacity <input id="heatOpacity" type="range" min="40" max="100" value="78" title="Heatmap opacity" /><b id="heatOpacityValue">78%</b></label>
      <label>Atoll opacity <input id="atollOpacity" type="range" min="0" max="100" value="62" title="Prediction opacity" /><b id="atollOpacityValue">62%</b></label>
    </div>
  </div>
  <div class="compare-note" id="compareNote">Review Traffic/KPI heatmap with optional Atoll coverage overlay. Use Fit Traffic or Fit Coverage to jump between views.</div>
  <div id="dtFloatingLegend"></div>
  <div id="floatingLegend"></div>
  <div class="panel">
    <div class="brand-lockup">
      <img class="brand-mark-img" src="__BRAND_MARK__" alt="AutomationPark" />
      <div>
        <div class="brand-name">AP GeoMap</div>
        <div class="brand-sub">automationpark.tech</div>
      </div>
    </div>
    <input id="searchBox" placeholder="Search Site / Cell / PCI / TAC" />
    <div class="row quick-row">
      <button id="searchBtn">Focus</button>
      <button id="homeBtn">Home</button>
    </div>
    <div class="row quick-row">
      <button id="fitBtn">Fit Network</button>
      <button id="cleanMapBtn">Clean Map</button>
    </div>
    <div class="section-title color-section">Network Coloring</div>
    <select id="colorMode">
      <option value="carrierColor">Carrier / Band</option>
      <option value="technologyColor">Technology</option>
      <option value="tacColor">LAC / TAC</option>
      <option value="vendorColor">Vendor</option>
    </select>
    <div class="section-title layers-section">Map Layers</div>
    <div class="toggle-grid">
      <button id="dotsBtn">Site Marker OFF</button>
      <button id="shellsBtn" class="active">Shells ON</button>
      <button id="labelsBtn">Labels OFF</button>
      <button id="ncellBtn">NCell OFF</button>
      <button id="popupBtn" class="active">Info ON</button>
    </div>
    <select id="labelMode">
      <option value="cell">Cell Labels</option>
      <option value="site">Site Labels</option>
      <option value="both">Site + Cell Labels</option>
    </select>
    <div class="section-title pointer-section">Pointer Mode</div>
    <div class="mode-grid">
      <button id="pointerSelectBtn">Sharp Select</button>
      <button id="pointerHandBtn" class="active">Hand Pan</button>
    </div>
    <div class="section-title filter-section">Carrier Layers</div>
    <div class="three-grid carrier-grid">
      <button id="carrierAllBtn" class="active">All</button>
      <button id="carrierL07Btn">L07</button>
      <button id="carrierL18Btn">L18</button>
      <button id="carrierL21Btn">L2100</button>
      <button id="carrierL23Btn">L2300</button>
      <button id="carrierNR26Btn">NR2600</button>
      <button id="carrierNR900Btn">NR900</button>
      <button id="carrierN35Btn">N35</button>
      <button id="carrierF1Btn" class="future-carrier">F1</button>
      <button id="carrierF2Btn" class="future-carrier">F2</button>
      <button id="carrierF3Btn" class="future-carrier">F3</button>
      <button id="carrierF4Btn" class="future-carrier">F4</button>
    </div>
    <div class="section-title shell-section">RF Shell Size</div>
    <input id="shellSize" type="range" min="5" max="130" value="10" />
    <div class="hint mini-hint" id="shellSizeText">Shell radius: 10%</div>
    <input id="shellWidth" type="range" min="35" max="120" value="65" />
    <div class="hint mini-hint" id="shellWidthText">Shell width: 65%</div>
    <div class="section-title marker-section">Site Marker Size</div>
    <input id="siteMarkerSize" type="range" min="80" max="300" value="80" />
    <div class="hint mini-hint" id="siteMarkerSizeText">Site marker: 80%</div>
    <details class="ap-module anr" open>
      <summary>Existing ANR Lines</summary>
      <div class="ap-module-body">
        <div class="hint mini-hint">Click any cell with Selection OFF to draw its current ANR neighbors. Intra, Inter, and IRAT use different line colors.</div>
        <div class="mini">
          <div class="stat">Focus Cell<b id="existingAnrFocus">-</b></div>
          <div class="stat">Lines<b id="existingAnrCount">0</b></div>
        </div>
        <div class="row">
          <button id="existingAnrFitBtn">Fit ANR</button>
          <button id="existingAnrClearBtn" class="warn">Clear ANR Lines</button>
        </div>
        <div id="existingAnrList" class="small-list">Click a cell to show existing ANR lines.</div>
      </div>
    </details>

    <details class="ap-module anr">
      <summary>ANR/VNR Analysis</summary>
      <div class="ap-module-body">
        <div class="section-title builder-section">ANR / VNR Builder</div>
        <div class="hint mini-hint">Selection ON: first click sets Cell-A, next clicks add target NCells and draw/export lines.</div>
        <div class="section-title vnr-section">New NCell Type</div>
        <div class="three-grid">
          <button id="linkAutoBtn" class="active">Auto</button>
          <button id="linkIntraBtn">Intra</button>
          <button id="linkInterBtn">Inter</button>
          <button id="linkIratBtn">IRAT</button>
        </div>
        <div class="row">
          <button id="selectBtn">Selection OFF</button>
          <button id="clearBtn" class="warn">Clear</button>
        </div>
        <div class="row">
          <button id="meshBtn">Group Mesh OFF</button>
        </div>
        <div class="hint mini-hint" id="meshHint">Normal: Cell-A exports to selected targets. Group Mesh: every selected cell exports to every other selected cell.</div>
        <div class="row">
          <button id="downloadBtn" class="gold">Download NCell CSV</button>
          <button id="copyBtn">Copy CSV</button>
        </div>
        <div class="mini">
          <div class="stat">New Type<b id="linkTypeText">Auto</b></div>
          <div class="stat">CSV Rows<b id="csvRowCount">0</b></div>
        </div>
        <div class="mini">
          <div class="stat">Source Cell-A<b id="sourceText">-</b></div>
          <div class="stat">Targets<b id="targetCount">0</b></div>
        </div>
        <div id="selectedList">No selected NCells yet.</div>
        <div class="section-title ncell-filter-section">NCell Type Filter</div>
        <div class="three-grid">
          <button id="ncellAllBtn" class="active">All</button>
          <button id="ncellIntraBtn">Intra</button>
          <button id="ncellInterBtn">Inter</button>
          <button id="ncellIratBtn">IRAT</button>
        </div>
        <div class="section-title vnr-section">ANR & VNR Audit</div>
        <div class="mini">
          <div class="stat">NCell Rows<b id="anrTotal">0</b></div>
          <div class="stat">One-Way<b id="anrOneWay">0</b></div>
        </div>
        <div class="mini">
          <div class="stat">Missing Targets<b id="anrMissing">0</b></div>
          <div class="stat">Cell Audit<b id="anrCellStatus">-</b></div>
        </div>
        <div class="mini">
          <div class="stat">IntraFreq<b id="anrIntra">0</b></div>
          <div class="stat">InterFreq<b id="anrInter">0</b></div>
        </div>
        <div class="mini">
          <div class="stat">IRAT<b id="anrIrat">0</b></div>
          <div class="stat">ANR Status<b id="anrHealth">Ready</b></div>
        </div>
        <div class="mini">
          <div class="stat">Issue Rows<b id="anrIssueRows">0</b></div>
          <div class="stat">Duplicates<b id="anrDuplicates">0</b></div>
        </div>
        <div class="section-title vnr-section">Neighbor Audit Report</div>
        <div class="hint mini-hint">Audit filters show one-way, missing-target, and duplicate NCell rows. Cell-A Audit follows the selected source cell.</div>
        <div class="three-grid">
          <button id="auditIssuesBtn" class="active">Issues</button>
          <button id="auditOneWayBtn">1-Way</button>
          <button id="auditMissingBtn">Missing</button>
          <button id="auditDupBtn">Dup</button>
        </div>
        <div class="row">
          <button id="auditSelectedBtn">Cell-A Audit</button>
          <button id="auditExportBtn" class="gold">Export Audit CSV</button>
        </div>
        <div id="auditList" class="small-list">No audit rows loaded.</div>
      </div>
    </details>

    <details class="ap-module area">
      <summary>Area Tools</summary>
      <div class="ap-module-body">
        <div class="hint mini-hint">Area ON lets you click polygon points on the map, close the shape, count cells/sites inside it, then export the selected cells.</div>
        <div class="row">
          <button id="areaBtn">Area OFF</button>
          <button id="areaCloseBtn">Close Area</button>
        </div>
        <div class="row">
          <button id="areaUndoBtn">Undo Point</button>
          <button id="areaClearBtn" class="warn">Clear Area</button>
        </div>
        <div class="row">
          <button id="areaFitBtn">Fit Area</button>
          <button id="areaDownloadBtn" class="gold">Export Area CSV</button>
        </div>
        <div class="mini">
          <div class="stat">Points<b id="areaPointCount">0</b></div>
          <div class="stat">Cells<b id="areaCellCount">0</b></div>
        </div>
        <div class="mini">
          <div class="stat">Sites<b id="areaSiteCount">0</b></div>
          <div class="stat">Tech<b id="areaTechText">-</b></div>
        </div>
        <div id="areaList" class="small-list">No area selected.</div>
      </div>
    </details>

    <details class="ap-module audit">
      <summary>Optimization Audit</summary>
      <div class="ap-module-body">
        <div class="section-title danger">Worst Cell Analysis</div>
        <textarea id="worstInput" placeholder="Paste worst Cell IDs or Site IDs...&#10;S115-L07-1-A&#10;S259-L18-3-C"></textarea>
        <div class="row">
          <button id="worstLoadBtn">Load Worst</button>
          <button id="worstFitBtn">Center Worst</button>
        </div>
        <div class="row">
          <button id="worstClearBtn" class="warn">Clear Worst</button>
          <button id="worstDownloadBtn" class="gold">Export Worst CSV</button>
        </div>
        <div class="mini">
          <div class="stat">Loaded<b id="worstLoaded">0</b></div>
          <div class="stat">Matched<b id="worstMatched">0</b></div>
        </div>
        <div id="worstList" class="small-list">No worst cells loaded.</div>
      </div>
    </details>

    <details class="ap-module ai">
      <summary>Auto Suggestions</summary>
      <div class="ap-module-body">
        <div class="hint mini-hint">First-pass generator: select Cell-A, then suggest nearby missing neighbors by distance, azimuth, technology, and frequency.</div>
        <div class="row">
          <button id="suggestBtn">Suggest Cell-A</button>
          <button id="suggestAddBtn" class="gold">Add Top 5</button>
        </div>
        <div class="mini">
          <div class="stat">Candidates<b id="suggestCount">0</b></div>
          <div class="stat">Existing Skipped<b id="suggestSkipped">0</b></div>
        </div>
        <div id="suggestList" class="small-list">Select Cell-A, then run suggestions.</div>
      </div>
    </details>

    <details class="ap-module future">
      <summary>Terrain / LOS</summary>
      <div class="ap-module-body">
        <div class="hint mini-hint">Phase 3 v1 is active on NCell/ANR line clicks. It uses real coordinates, azimuth, antenna height, carrier frequency, FSPL, radio horizon, Fresnel clearance, and earth curvature.</div>
        <div class="mini">
          <div class="stat">Mode<b>Geom LOS</b></div>
          <div class="stat">DEM<b>Next</b></div>
        </div>
        <div class="small-list">Turn NCell/ANR lines ON, then click a line to inspect Terrain / LOS metrics.</div>
      </div>
    </details>

    <details class="ap-module future">
      <summary>Future Modules</summary>
      <div class="ap-module-body">
        <div class="ap-future-grid">
          <div class="ap-future-pill">Emergency Sites</div>
          <div class="ap-future-pill">Special Events</div>
          <div class="ap-future-pill">National Roaming</div>
          <div class="ap-future-pill">Transmission</div>
          <div class="ap-future-pill">NOC Operations</div>
          <div class="ap-future-pill">Sales & Marketing</div>
          <div class="ap-future-pill">Coverage Planning</div>
          <div class="ap-future-pill">Capacity Planning</div>
          <div class="ap-future-pill">Terrain / LOS</div>
          <div class="ap-future-pill">Hexagon Shells</div>
        </div>
      </div>
    </details>
    <div class="hidden-metrics" aria-hidden="true">
      <span id="cellCount">0</span>
      <span id="linkCount">0</span>
      <span id="dtCount">0</span>
      <span id="dtModeText">RSRP</span>
      <span id="atollStatus">-</span>
      <span id="atollSize">-</span>
    </div>
    <div class="scroll-tools">
      <button id="panelTopBtn">Top</button>
      <button id="panelMoreBtn">More</button>
    </div>
  </div>
  <script>
    const cells = __CELLS__;
    const shells = __SHELLS__;
    const dtPoints = __DT_POINTS__;
    const anrSummary = __ANR_SUMMARY__;
    const atollOverlay = __ATOLL_OVERLAY__;
    const startCenter = [__CENTER_LON__, __CENTER_LAT__];
    let selectionMode = false;
    let shellsVisible = true;
    let dotsVisible = false;
    let labelsVisible = false;
    let ncellVisible = false;
    let popupsVisible = true;
    let legendVisible = true;
    let carrierFilter = 'all';
    let labelMode = 'cell';
    let ncellRelationFilter = 'all';
    let linkRelationMode = 'auto';
    let pointerMode = 'pan';
    let colorMode = 'carrierColor';
    let dtVisible = false;
    const dtDataKind = dtPoints.features[0]?.properties?.DATA_KIND || '';
    const hasTrafficLayer = dtDataKind === 'traffic';
    const hasMeasuredCoverageLayer = dtPoints.features.length > 0 && dtDataKind !== 'traffic';
    let dtColorMode = hasTrafficLayer ? 'kpiColor' : 'rsrpColor';
    let dtViewMode = 'both';
    let atollVisible = false;
    let heatRadiusScale = 42;
    let heatIntensityScale = 1.2;
    let heatOpacityScale = 0.78;
    let selectedDtSample = null;
    let selectedDtPoint = null;
    let selectedPciMatchCount = 0;
    let selectedNearestCells = [];
    let selectedNearestCellNames = [];
    let sourceCell = null;
    let targets = [];
    let groupMeshMode = false;
    const meshLinkSoftLimit = 350;
    let worstTokens = [];
    let worstMatchedFeatures = [];
    let worstMatchedNames = [];
    let areaMode = false;
    let areaPoints = [];
    let areaClosed = false;
    let areaSelectedFeatures = [];
    let shellScale = 0.25;
    let shellWidthScale = 0.65;
    let siteMarkerScale = 0.8;
    let auditFilterMode = 'issues';
    let auditSelectedOnly = false;
    let suggestRows = [];
    let suggestSkippedExisting = 0;
    let suggestHasRun = false;
    let existingAnrFocusCell = null;
    let existingAnrRows = [];
    let existingAnrNeighborNames = [];
    let lastCellOpenAt = 0;

    function escapeHtml(value) {
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function escapeCsv(value) {
      return `"${String(value ?? '').replace(/"/g, '""')}"`;
    }

    function normalizeCellName(value) {
      return String(value || '').trim().toUpperCase();
    }

    function existingNeighborKey(source, target) {
      return `${normalizeCellName(source)}-->${normalizeCellName(target)}`;
    }

    const existingNeighborPairs = new Set((anrSummary.auditRows || []).map(row => existingNeighborKey(row.source, row.target)));

    function relationType(srcProps, tgtProps) {
      const st = String(srcProps.Technology || '').toUpperCase();
      const tt = String(tgtProps.Technology || '').toUpperCase();
      const sc = String(srcProps.CARRIER || '').toUpperCase();
      const tc = String(tgtProps.CARRIER || '').toUpperCase();
      if (st !== tt) return 'IRAT';
      if (sc !== tc) return 'InterFreq';
      return 'IntraFreq';
    }

    function relationColor(relation) {
      if (relation === 'IntraFreq') return '#22c55e';
      if (relation === 'InterFreq') return '#38bdf8';
      if (relation === 'IRAT') return '#f97316';
      return '#ff2d2d';
    }

    function relationShortLabel(relation) {
      if (relation === 'IntraFreq') return 'Intra';
      if (relation === 'InterFreq') return 'Inter';
      if (relation === 'IRAT') return 'IRAT';
      return relation || '-';
    }

    function relationClass(relation) {
      if (relation === 'IntraFreq') return 'intra';
      if (relation === 'InterFreq') return 'inter';
      if (relation === 'IRAT') return 'irat';
      return '';
    }

    function selectedRelationType(srcProps, tgtProps) {
      return linkRelationMode === 'auto'
        ? relationType(srcProps, tgtProps)
        : linkRelationMode;
    }

    function selectedRelationLabel() {
      return linkRelationMode === 'auto' ? 'Auto' : relationShortLabel(linkRelationMode);
    }

    function carrierFrequencyMhz(carrier) {
      const key = normalizedCarrierValue(carrier);
      const frequencies = {
        L07: 700,
        NR900: 900,
        L18: 1800,
        L2100: 2100,
        L2300: 2300,
        NR2600: 2600,
        N35: 3500,
      };
      return frequencies[key] || 1800;
    }

    function numericOr(value, fallback = 0) {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : fallback;
    }

    function formatNumber(value, digits = 1, suffix = '') {
      const parsed = Number(value);
      if (!Number.isFinite(parsed)) return '-';
      return `${parsed.toFixed(digits)}${suffix}`;
    }

    function angularDifference(a, b) {
      const first = Number(a);
      const second = Number(b);
      if (!Number.isFinite(first) || !Number.isFinite(second)) return 0;
      return Math.abs(((first - second + 540) % 360) - 180);
    }

    function anrForCell(cellName) {
      return (anrSummary.byCell && anrSummary.byCell[cellName])
        ? anrSummary.byCell[cellName]
        : { incoming:0, outgoing:0, oneWay:0, missing:0, duplicates:0, intra:0, inter:0, irat:0 };
    }

    function auditRowsForMode() {
      const rows = anrSummary.auditRows || [];
      return rows.filter(row => {
        if (auditSelectedOnly && sourceCell) {
          const key = normalizeCellName(sourceCell);
          if (normalizeCellName(row.source) !== key && normalizeCellName(row.target) !== key) return false;
        } else if (auditSelectedOnly && !sourceCell) {
          return false;
        }
        if (auditFilterMode === 'oneWay') return row.isOneWay;
        if (auditFilterMode === 'missing') return row.isMissingTarget;
        if (auditFilterMode === 'duplicate') return row.isDuplicate;
        if (auditFilterMode === 'all') return true;
        return row.isOneWay || row.isMissingTarget || row.isDuplicate;
      });
    }

    function auditIssueClass(row) {
      if (row.isMissingTarget) return 'issue';
      if (row.isOneWay || row.isDuplicate) return 'warn';
      return 'ok';
    }

    function updateAuditUi() {
      const issueEl = document.getElementById('anrIssueRows');
      const dupEl = document.getElementById('anrDuplicates');
      if (issueEl) issueEl.textContent = Number(anrSummary.issueRows || 0).toLocaleString();
      if (dupEl) dupEl.textContent = Number(anrSummary.duplicateRows || 0).toLocaleString();
      const buttons = {
        issues: document.getElementById('auditIssuesBtn'),
        oneWay: document.getElementById('auditOneWayBtn'),
        missing: document.getElementById('auditMissingBtn'),
        duplicate: document.getElementById('auditDupBtn'),
      };
      Object.entries(buttons).forEach(([mode, btn]) => {
        if (btn) btn.classList.toggle('active', auditFilterMode === mode);
      });
      const selectedBtn = document.getElementById('auditSelectedBtn');
      if (selectedBtn) {
        selectedBtn.classList.toggle('active', auditSelectedOnly);
        selectedBtn.textContent = auditSelectedOnly ? 'Cell-A Audit ON' : 'Cell-A Audit';
      }
      const listEl = document.getElementById('auditList');
      if (!listEl) return;
      const rows = auditRowsForMode();
      if (!rows.length) {
        listEl.textContent = auditSelectedOnly && !sourceCell
          ? 'Select Cell-A first.'
          : 'No audit rows for this filter.';
        return;
      }
      listEl.innerHTML = rows.slice(0, 28).map(row => `
        <div class="link-row">
          <span class="link-target">${escapeHtml(row.source)} -> ${escapeHtml(row.target)} (${escapeHtml(row.relation)})</span>
          <span class="link-pill ${auditIssueClass(row)}">${escapeHtml(row.issue)}</span>
        </div>
      `).join('') + (rows.length > 28 ? `<div class="hint mini-hint">${rows.length - 28} more rows in CSV export.</div>` : '');
    }

    function setAuditMode(mode) {
      auditFilterMode = mode;
      updateAuditUi();
    }

    function updateAnrUi(cellName = null) {
      const totalEl = document.getElementById('anrTotal');
      const oneWayEl = document.getElementById('anrOneWay');
      const missingEl = document.getElementById('anrMissing');
      const cellEl = document.getElementById('anrCellStatus');
      const intraEl = document.getElementById('anrIntra');
      const interEl = document.getElementById('anrInter');
      const iratEl = document.getElementById('anrIrat');
      const healthEl = document.getElementById('anrHealth');
      if (!totalEl || !oneWayEl || !missingEl || !cellEl) return;
      const relationCounts = anrSummary.relationCounts || {};
      totalEl.textContent = Number(anrSummary.total || 0).toLocaleString();
      oneWayEl.textContent = Number(anrSummary.oneWay || 0).toLocaleString();
      missingEl.textContent = Number(anrSummary.missingTargets || 0).toLocaleString();
      if (intraEl) intraEl.textContent = Number(relationCounts.IntraFreq || 0).toLocaleString();
      if (interEl) interEl.textContent = Number(relationCounts.InterFreq || 0).toLocaleString();
      if (iratEl) iratEl.textContent = Number(relationCounts.IRAT || 0).toLocaleString();
      if (healthEl) {
        healthEl.textContent = anrSummary.total ? 'Ready' : 'No Data';
      }
      if (!cellName) {
        cellEl.textContent = '-';
        updateAuditUi();
        return;
      }
      const audit = anrForCell(cellName);
      cellEl.textContent = `In ${audit.incoming || 0} / Out ${audit.outgoing || 0} / 1W ${audit.oneWay || 0} / Dup ${audit.duplicates || 0}`;
      updateAuditUi();
    }

    function scaledCoordinate(origin, center, coordinate) {
      const radial = [
        origin[0] + (coordinate[0] - origin[0]) * shellScale,
        origin[1] + (coordinate[1] - origin[1]) * shellScale
      ];
      const centerScaled = [
        origin[0] + (center[0] - origin[0]) * shellScale,
        origin[1] + (center[1] - origin[1]) * shellScale
      ];
      return [
        centerScaled[0] + (radial[0] - centerScaled[0]) * shellWidthScale,
        centerScaled[1] + (radial[1] - centerScaled[1]) * shellWidthScale
      ];
    }

    function scaledRing(ring) {
      if (!ring || ring.length < 3) return ring || [];
      const origin = ring[0];
      const lastIndex = ring.length - 1;
      const center = ring[Math.floor(ring.length / 2)] || ring[1];
      return ring.map((coordinate, index) => (
        index === 0 || index === lastIndex
          ? origin
          : scaledCoordinate(origin, center, coordinate)
      ));
    }

    function scaledShellFeature(feature) {
      return {
        ...feature,
        geometry: {
          ...feature.geometry,
          coordinates: [scaledRing(feature.geometry.coordinates[0] || [])]
        }
      };
    }

    function scaledShellsGeojson() {
      return {
        type: 'FeatureCollection',
        features: shells.features.map(scaledShellFeature)
      };
    }

    function shellTip(feature) {
      const ring = scaledRing(feature.geometry.coordinates[0] || []);
      return ring[Math.floor(ring.length / 2)];
    }

    function cellPopup(props) {
      const audit = anrForCell(props.CELL_NAME);
      return `
        <div class="ap-popup-title">${props.CELL_NAME || '-'}</div>
        <div class="ap-popup-row"><b>Site:</b> ${props.SITE_NAME || '-'}</div>
        <div class="ap-popup-row"><b>Tech/Carrier:</b> ${props.Technology || '-'} / ${props.CARRIER || '-'}</div>
        <div class="ap-popup-row"><b>Azimuth:</b> ${props.AZIMUTH || '-'} deg | <b>PCI:</b> ${props.PCI || '-'}</div>
        <div class="ap-popup-row"><b>Antenna:</b> ${props.ANTENNA || '-'}</div>
        <div class="ap-popup-row"><b>Height:</b> ${props.HEIGHT || '-'} m | <b>PMAX:</b> ${props.PMAX || '-'} dBm</div>
        <div class="ap-popup-row"><b>ANR:</b> In ${audit.incoming || 0} | Out ${audit.outgoing || 0} | One-way ${audit.oneWay || 0} | Missing ${audit.missing || 0}</div>
      `;
    }

    function dtPopup(props) {
      const isKpi = dtColorMode === 'kpiColor';
      const kpiLine = isKpi
        ? `<div class="ap-popup-row"><b>${escapeHtml(props.KPI_NAME || 'KPI')}:</b> ${escapeHtml(props.KPI_VALUE ?? '-')}</div>`
        : '';
      const nearestRows = selectedNearestCells.length
        ? selectedNearestCells.map(item => `<div class="ap-popup-row"><b>${item.rank}.</b> ${item.cell} | PCI ${item.pci || '-'} | ${item.carrier || '-'} | ${item.distanceKm.toFixed(2)} km</div>`).join('')
        : '<div class="ap-popup-row">No nearest planned cells calculated.</div>';
      return `
        <div class="ap-popup-title">${isKpi ? 'Traffic/KPI Cell' : 'Drive Test Sample'} ${props.index ?? ''}</div>
        ${kpiLine}
        <div class="ap-popup-row"><b>PCI:</b> ${props.PCI ?? '-'}</div>
        <div class="ap-popup-row"><b>RSRP:</b> ${props.RSRP ?? '-'} dBm</div>
        <div class="ap-popup-row"><b>RSRQ:</b> ${props.RSRQ ?? '-'} dB</div>
        <div class="ap-popup-row"><b>SINR:</b> ${props.SINR ?? '-'} dB</div>
        <div class="ap-popup-row"><b>Serving:</b> ${props.servingCell || '-'}</div>
        <div class="ap-popup-row"><b>Time:</b> ${props.time || '-'}</div>
        <div class="ap-popup-title" style="margin-top:10px">Nearest Planned Cells</div>
        ${nearestRows}
      `;
    }

    function haversineKm(a, b) {
      const toRad = deg => deg * Math.PI / 180;
      const R = 6371.0088;
      const dLat = toRad(b[1] - a[1]);
      const dLon = toRad(b[0] - a[0]);
      const lat1 = toRad(a[1]);
      const lat2 = toRad(b[1]);
      const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
      return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
    }

    function nearestCellsToPoint(point, limit = 5) {
      return cells.features
        .map(feature => ({
          cell: feature.properties.CELL_NAME || '-',
          site: feature.properties.SITE_NAME || '-',
          pci: feature.properties.PCI || '-',
          carrier: feature.properties.CARRIER || '-',
          technology: feature.properties.Technology || '-',
          distanceKm: haversineKm(point, feature.geometry.coordinates),
        }))
        .sort((a, b) => a.distanceKm - b.distanceKm)
        .slice(0, limit)
        .map((item, index) => ({ ...item, rank:index + 1 }));
    }

    function nearestCellsSummary() {
      if (!selectedNearestCells.length) return '';
      return selectedNearestCells
        .slice(0, 3)
        .map(item => `${item.rank}) ${item.cell} PCI ${item.pci} ${item.distanceKm.toFixed(2)} km`)
        .join(' | ');
    }

    function azimuthDelta(sourceAzimuth, sourceCoord, targetCoord) {
      const planned = Number(sourceAzimuth);
      if (!Number.isFinite(planned)) return 0;
      const bearing = bearingDegrees(sourceCoord, targetCoord);
      return angularDifference(bearing, planned);
    }

    function bearingDegrees(sourceCoord, targetCoord) {
      const toRad = deg => deg * Math.PI / 180;
      const toDeg = rad => rad * 180 / Math.PI;
      const lon1 = toRad(sourceCoord[0]);
      const lat1 = toRad(sourceCoord[1]);
      const lon2 = toRad(targetCoord[0]);
      const lat2 = toRad(targetCoord[1]);
      const y = Math.sin(lon2 - lon1) * Math.cos(lat2);
      const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1);
      return (toDeg(Math.atan2(y, x)) + 360) % 360;
    }

    function fsplDb(distanceKm, frequencyMhz) {
      const d = Math.max(Number(distanceKm) || 0, 0.001);
      const f = Math.max(Number(frequencyMhz) || 1800, 1);
      return 32.44 + 20 * Math.log10(d) + 20 * Math.log10(f);
    }

    function radioHorizonKm(sourceHeightM, targetHeightM) {
      const source = Math.max(0, Number(sourceHeightM) || 0);
      const target = Math.max(0, Number(targetHeightM) || 0);
      return 4.12 * (Math.sqrt(source) + Math.sqrt(target));
    }

    function earthBulgeMeters(distanceKm, kFactor = 4 / 3) {
      const d = Math.max(Number(distanceKm) || 0, 0);
      return (d * d) / (4 * 12.75 * kFactor);
    }

    function fresnelMidpointMeters(distanceKm, frequencyMhz) {
      const d = Math.max(Number(distanceKm) || 0, 0.001);
      const fGhz = Math.max((Number(frequencyMhz) || 1800) / 1000, 0.1);
      return 17.32 * Math.sqrt((d / 4) / fGhz);
    }

    function losStatusForMetrics(distanceKm, horizonKm, clearanceM) {
      if (distanceKm > horizonKm) return 'Beyond radio horizon';
      if (clearanceM >= 0) return 'Likely geometric LOS';
      return 'Terrain profile needed';
    }

    function azimuthStatus(delta) {
      if (delta <= 45) return 'Main beam';
      if (delta <= 75) return 'Sector edge';
      if (delta <= 120) return 'Side/back risk';
      return 'Back-lobe';
    }

    function terrainLosMetrics(sourceName, targetName) {
      const sourceFeature = cellFeatureForCell(sourceName);
      const targetFeature = cellFeatureForCell(targetName);
      if (!sourceFeature || !targetFeature) return null;
      const sourceProps = sourceFeature.properties || {};
      const targetProps = targetFeature.properties || {};
      const sourceCoord = sourceFeature.geometry.coordinates;
      const targetCoord = targetFeature.geometry.coordinates;
      const distanceKm = haversineKm(sourceCoord, targetCoord);
      const forwardBearing = bearingDegrees(sourceCoord, targetCoord);
      const reverseBearing = bearingDegrees(targetCoord, sourceCoord);
      const sourceDelta = angularDifference(forwardBearing, sourceProps.AZIMUTH);
      const targetDelta = angularDifference(reverseBearing, targetProps.AZIMUTH);
      const sourceHeight = numericOr(sourceProps.HEIGHT, 10);
      const targetHeight = numericOr(targetProps.HEIGHT, 10);
      const frequencyMhz = carrierFrequencyMhz(sourceProps.CARRIER);
      const horizonKm = radioHorizonKm(sourceHeight, targetHeight);
      const bulgeM = earthBulgeMeters(distanceKm);
      const fresnelM = fresnelMidpointMeters(distanceKm, frequencyMhz);
      const clearanceM = ((sourceHeight + targetHeight) / 2) - bulgeM - (0.6 * fresnelM);
      const status = losStatusForMetrics(distanceKm, horizonKm, clearanceM);
      return {
        sourceProps,
        targetProps,
        distanceKm,
        forwardBearing,
        reverseBearing,
        sourceDelta,
        targetDelta,
        sourceHeight,
        targetHeight,
        frequencyMhz,
        fspl: fsplDb(distanceKm, frequencyMhz),
        horizonKm,
        bulgeM,
        fresnelM,
        clearanceM,
        status,
        relation: relationType(sourceProps, targetProps),
      };
    }

    function terrainLosPopupHtml(sourceName, targetName, relation = null) {
      const metrics = terrainLosMetrics(sourceName, targetName);
      if (!metrics) {
        return '<div class="ap-popup-row">Terrain/LOS: source or target cell not found.</div>';
      }
      const sourceCarrier = escapeHtml(normalizedCarrierValue(metrics.sourceProps.CARRIER));
      const targetCarrier = escapeHtml(normalizedCarrierValue(metrics.targetProps.CARRIER));
      const statusColor = metrics.status === 'Likely geometric LOS' ? '#22c55e'
        : metrics.status === 'Terrain profile needed' ? '#facc15'
        : '#ef4444';
      return `
        <div class="ap-popup-title" style="margin-top:10px">Terrain / LOS v1</div>
        <div class="ap-popup-row"><b>Status:</b> <span style="color:${statusColor};font-weight:900">${escapeHtml(metrics.status)}</span></div>
        <div class="ap-popup-row"><b>Distance:</b> ${formatNumber(metrics.distanceKm, 2, ' km')} | <b>Relation:</b> ${escapeHtml(relation || metrics.relation)}</div>
        <div class="ap-popup-row"><b>Bearing:</b> ${formatNumber(metrics.forwardBearing, 0, ' deg')} src -> tgt | ${formatNumber(metrics.reverseBearing, 0, ' deg')} tgt -> src</div>
        <div class="ap-popup-row"><b>Az align:</b> Src ${formatNumber(metrics.sourceDelta, 0, ' deg')} (${azimuthStatus(metrics.sourceDelta)}) | Tgt ${formatNumber(metrics.targetDelta, 0, ' deg')} (${azimuthStatus(metrics.targetDelta)})</div>
        <div class="ap-popup-row"><b>Heights:</b> ${formatNumber(metrics.sourceHeight, 1, ' m')} -> ${formatNumber(metrics.targetHeight, 1, ' m')} | <b>Carriers:</b> ${sourceCarrier} -> ${targetCarrier}</div>
        <div class="ap-popup-row"><b>Freq:</b> ${formatNumber(metrics.frequencyMhz, 0, ' MHz')} | <b>FSPL:</b> ${formatNumber(metrics.fspl, 1, ' dB')}</div>
        <div class="ap-popup-row"><b>Radio horizon:</b> ${formatNumber(metrics.horizonKm, 2, ' km')} | <b>Mid clearance:</b> ${formatNumber(metrics.clearanceM, 1, ' m')}</div>
        <div class="ap-popup-row"><b>Mid Fresnel 60%:</b> ${formatNumber(metrics.fresnelM * 0.6, 1, ' m')} | <b>Earth bulge:</b> ${formatNumber(metrics.bulgeM, 1, ' m')}</div>
        <div class="ap-popup-row"><b>DEM:</b> not loaded yet; this is geometry + height + curvature.</div>
      `;
    }

    function suggestionDistanceLimitKm(sourceProps) {
      const carrier = String(sourceProps.CARRIER || '').toUpperCase();
      if (carrier.includes('N35') || carrier.includes('NR35')) return 2.2;
      if (carrier.includes('L18') || carrier.includes('L21')) return 3.2;
      if (carrier.includes('L07') || carrier.includes('NR07')) return 5.2;
      return 3.6;
    }

    function buildSuggestionsForSource(sourceName) {
      const srcFeature = cellFeatureForCell(sourceName);
      if (!srcFeature) return { rows: [], skipped: 0 };
      const srcProps = srcFeature.properties || {};
      const srcCoord = srcFeature.geometry.coordinates;
      const maxDistance = suggestionDistanceLimitKm(srcProps);
      let skipped = 0;
      const candidates = [];
      for (const feature of cells.features) {
        const props = feature.properties || {};
        const targetName = props.CELL_NAME;
        if (!targetName || targetName === sourceName) continue;
        if (existingNeighborPairs.has(existingNeighborKey(sourceName, targetName))) {
          skipped += 1;
          continue;
        }
        const distanceKm = haversineKm(srcCoord, feature.geometry.coordinates);
        if (distanceKm > maxDistance) continue;
        const relation = relationType(srcProps, props);
        const azDelta = azimuthDelta(srcProps.AZIMUTH, srcCoord, feature.geometry.coordinates);
        const sameSitePenalty = props.SITE_NAME === srcProps.SITE_NAME ? 18 : 0;
        const techBonus = relation === 'IRAT' ? 6 : 0;
        const score = Math.max(0, 100 - (distanceKm / maxDistance) * 52 - Math.min(azDelta, 180) * 0.22 - sameSitePenalty + techBonus);
        candidates.push({
          source: sourceName,
          target: targetName,
          relation,
          distanceKm,
          azimuthDelta: azDelta,
          score,
          reason: `${distanceKm.toFixed(2)} km | az ${azDelta.toFixed(0)} deg | ${relation}`
        });
      }
      return {
        rows: candidates.sort((a, b) => b.score - a.score).slice(0, 18),
        skipped
      };
    }

    function renderSuggestions() {
      const countEl = document.getElementById('suggestCount');
      const skippedEl = document.getElementById('suggestSkipped');
      const listEl = document.getElementById('suggestList');
      if (countEl) countEl.textContent = suggestRows.length.toLocaleString();
      if (skippedEl) skippedEl.textContent = suggestSkippedExisting.toLocaleString();
      if (!listEl) return;
      if (!sourceCell) {
        listEl.textContent = 'Select Cell-A, then run suggestions.';
        return;
      }
      if (!suggestHasRun) {
        listEl.textContent = 'Cell-A selected. Run suggestions to find missing neighbors.';
        return;
      }
      if (!suggestRows.length) {
        listEl.textContent = 'No missing-neighbor candidates found for Cell-A.';
        return;
      }
      listEl.innerHTML = suggestRows.slice(0, 10).map(row => `
        <div class="link-row">
          <span class="link-target">${escapeHtml(row.target)} | ${escapeHtml(row.reason)}</span>
          <span class="link-pill ${relationClass(row.relation)}">${row.score.toFixed(0)}</span>
        </div>
      `).join('');
    }

    function runSuggestions() {
      if (!sourceCell) {
        suggestRows = [];
        suggestSkippedExisting = 0;
        suggestHasRun = false;
        renderSuggestions();
        return;
      }
      const result = buildSuggestionsForSource(sourceCell);
      suggestRows = result.rows;
      suggestSkippedExisting = result.skipped;
      suggestHasRun = true;
      renderSuggestions();
    }

    function addTopSuggestions(limit = 5) {
      if (!sourceCell || !suggestRows.length) return;
      for (const row of suggestRows.slice(0, limit)) {
        if (row.target !== sourceCell && !targets.includes(row.target)) {
          targets.push(row.target);
        }
      }
      updateSelectionUI();
    }

    function nearestCandidateLines() {
      if (!selectedDtPoint || !selectedNearestCells.length) {
        return { type:'FeatureCollection', features:[] };
      }
      const features = selectedNearestCells.map(item => {
        const targetFeature = cells.features.find(feature => feature.properties.CELL_NAME === item.cell);
        if (!targetFeature) return null;
        return {
          type:'Feature',
          geometry:{ type:'LineString', coordinates:[selectedDtPoint, targetFeature.geometry.coordinates] },
          properties:{
            rank:item.rank,
            cell:item.cell,
            pci:item.pci,
            distanceKm:item.distanceKm.toFixed(2)
          }
        };
      }).filter(Boolean);
      return { type:'FeatureCollection', features };
    }

    function normalizedCarrierValue(carrier) {
      const text = String(carrier || '').toUpperCase().trim();
      if (text.includes('F4')) return 'F4';
      if (text.includes('F3')) return 'F3';
      if (text.includes('F2')) return 'F2';
      if (text.includes('F1')) return 'F1';
      if (text.includes('N35') || text.includes('NR35') || text.includes('NR3500') || text.includes('N3500')) return 'N35';
      if (text.includes('NR26') || text.includes('NR2600') || text.includes('N26') || text.includes('N2600')) return 'NR2600';
      if (text.includes('L23') || text.includes('L2300') || text.includes('N23') || text.includes('NR23')) return 'L2300';
      if (text.includes('L21') || text.includes('L2100')) return 'L2100';
      if (text.includes('L18') || text.includes('L1800')) return 'L18';
      if (text.includes('N09') || text.includes('NR09') || text.includes('N900') || text.includes('NR900')) return 'NR900';
      if (text.includes('L07') || text.includes('NR07') || text.includes('L700') || text.includes('NR700')) return 'L07';
      return text || 'Unknown';
    }

    function shortCarrierLabel(props) {
      const carrier = normalizedCarrierValue(props.CARRIER);
      if (!carrier || carrier === 'Unknown') return '';
      return carrier;
    }

    function carrierColorForValue(carrier) {
      const key = normalizedCarrierValue(carrier);
      if (key === 'F4') return '#f0abfc';
      if (key === 'F3') return '#c084fc';
      if (key === 'N35') return '#ff3df2';
      if (key === 'F2') return '#818cf8';
      if (key === 'NR2600') return '#8b5cf6';
      if (key === 'L2300') return '#0ea5e9';
      if (key === 'L2100') return '#38bdf8';
      if (key === 'L18') return '#ffb000';
      if (key === 'F1') return '#facc15';
      if (key === 'NR900') return '#14b8a6';
      if (key === 'L07') return '#20ff7a';
      return '#c084fc';
    }

    function technologyKeyForValue(technology) {
      const tech = String(technology || '').toUpperCase();
      if (tech.includes('NR') || tech.includes('5G')) return '5G';
      if (tech.includes('LTE') || tech.includes('4G')) return '4G';
      if (tech.includes('UMTS') || tech.includes('3G')) return '3G';
      return technology || 'Unknown';
    }

    function technologyColorForValue(technology) {
      const key = technologyKeyForValue(technology);
      if (key === '5G') return '#a855f7';
      if (key === '4G') return '#22c55e';
      if (key === '3G') return '#38bdf8';
      return '#a78bfa';
    }

    function carrierColorExpression() {
      const carrier = ['upcase', ['to-string', ['get', 'CARRIER']]];
      return [
        'case',
        ['in', 'F4', carrier], '#f0abfc',
        ['in', 'F3', carrier], '#c084fc',
        ['any', ['in', 'N35', carrier], ['in', 'NR35', carrier]], '#a855f7',
        ['in', 'F2', carrier], '#818cf8',
        ['any', ['in', 'NR26', carrier], ['in', 'NR2600', carrier], ['in', 'N26', carrier], ['in', 'N2600', carrier]], '#8b5cf6',
        ['any', ['in', 'N09', carrier], ['in', 'NR09', carrier], ['in', 'N900', carrier], ['in', 'NR900', carrier]], '#14b8a6',
        ['any', ['in', 'L23', carrier], ['in', 'L2300', carrier]], '#0ea5e9',
        ['any', ['in', 'L21', carrier], ['in', 'L2100', carrier]], '#38bdf8',
        ['in', 'L18', carrier], '#f59e0b',
        ['in', 'F1', carrier], '#facc15',
        ['any', ['in', 'L07', carrier], ['in', 'NR07', carrier]], '#22c55e',
        '#a78bfa'
      ];
    }

    function technologyColorExpression() {
      const tech = ['upcase', ['to-string', ['get', 'Technology']]];
      return [
        'case',
        ['any', ['in', 'NR', tech], ['in', '5G', tech]], '#a855f7',
        ['any', ['in', 'LTE', tech], ['in', '4G', tech]], '#22c55e',
        ['any', ['in', 'UMTS', tech], ['in', '3G', tech]], '#38bdf8',
        '#a78bfa'
      ];
    }

    function propertyColorExpression() {
      return ['get', colorMode];
    }

    function legendKeyForMode(props) {
      if (colorMode === 'technologyColor') {
        return technologyKeyForValue(props.Technology);
      }
      if (colorMode === 'tacColor') return `TAC ${props.TAC || 'Unknown'}`;
      if (colorMode === 'pciColor') return `PCI ${props.PCI || 'Unknown'}`;
      if (colorMode === 'vendorColor') return props.VENDOR || 'Unknown';
      return normalizedCarrierValue(props.CARRIER);
    }

    function legendColorForMode(props) {
      if (colorMode === 'carrierColor') return carrierColorForValue(props.CARRIER);
      if (colorMode === 'technologyColor') return technologyColorForValue(props.Technology);
      return props[colorMode] || props.carrierColor || '#38bdf8';
    }

    const dtLegends = {
      kpiColor: [
        ['#ef4444', 'Critical traffic load', 0],
        ['#f97316', 'High traffic load', 0],
        ['#fde047', 'Medium traffic load', 0],
        ['#38bdf8', 'Moderate traffic load', 0],
        ['#2dd4bf', 'Light traffic load', 0],
        ['#16a34a', 'Very light traffic load', 0],
      ],
      rsrpColor: [
        ['#ff0000', '[-50, 0]', 0],
        ['#cc0000', '[-70, -50]', 0],
        ['#e8b6b6', '[-80, -70]', 0],
        ['#ffd84d', '[-90, -80]', 0],
        ['#00cc00', '[-105, -90]', 0],
        ['#73d2e8', '[-110, -105]', 0],
        ['#1148e8', '[-120, -110]', 0],
        ['#0b2f9f', '[-140, -120]', 0],
      ],
      rsrqColor: [
        ['#2563eb', 'Excellent > -7', 0],
        ['#22c55e', 'Good [-10, -7]', 0],
        ['#fde047', 'Fair [-13, -10]', 0],
        ['#f97316', 'Poor [-16, -13]', 0],
        ['#ef4444', 'Bad <= -16', 0],
      ],
      sinrColor: [
        ['#7c3aed', 'Excellent >= 20', 0],
        ['#2563eb', 'Strong [13, 20)', 0],
        ['#22c55e', 'Good [7, 13)', 0],
        ['#fde047', 'Fair [0, 7)', 0],
        ['#f97316', 'Poor [-3, 0)', 0],
        ['#ef4444', 'Bad < -3', 0],
      ],
    };

    function normalizeLegendColor(color) {
      const text = String(color || '').trim().toLowerCase();
      if (!text) return '';
      if (/^#[0-9a-f]{6}$/.test(text)) return text;
      if (/^[0-9a-f]{6}$/.test(text)) return `#${text}`;
      if (/^#[0-9a-f]{3}$/.test(text)) {
        return `#${text[1]}${text[1]}${text[2]}${text[2]}${text[3]}${text[3]}`;
      }
      if (/^[0-9a-f]{3}$/.test(text)) {
        return `#${text[0]}${text[0]}${text[1]}${text[1]}${text[2]}${text[2]}`;
      }
      return text;
    }

    function normalizedLegendRows(mode) {
      return (dtLegends[mode] || []).map(([color, label, count]) => [normalizeLegendColor(color), label, count]);
    }

    function trafficLegendColorFromWeight(props) {
      const weight = numericValue(props.kpiWeight);
      if (!Number.isFinite(weight)) return '';
      if (weight >= 0.84) return '#ef4444';
      if (weight >= 0.66) return '#f97316';
      if (weight >= 0.42) return '#fde047';
      if (weight >= 0.24) return '#38bdf8';
      if (weight >= 0.10) return '#2dd4bf';
      return '#16a34a';
    }

    function dtLegendColorForFeature(props) {
      const exactColor = normalizeLegendColor(props?.[dtColorMode]);
      const legendColors = new Set(normalizedLegendRows(dtColorMode).map(row => row[0]));
      if (exactColor && legendColors.has(exactColor)) return exactColor;
      if (dtColorMode === 'kpiColor') return trafficLegendColorFromWeight(props || {});
      return exactColor;
    }

    function dtRangeLegend() {
      const total = dtPoints.features.length || 1;
      const bins = normalizedLegendRows(dtColorMode).map(row => [...row]);
      for (const feature of dtPoints.features) {
        const color = dtLegendColorForFeature(feature.properties || {});
        const bin = bins.find(item => item[0] === color);
        if (bin) bin[2] += 1;
      }
      return bins.map(([color, label, count]) => [color, label, ((count / total) * 100).toFixed(1)]);
    }

    function carrierLayerLabel() {
      return carrierFilter === 'all' ? 'All carriers' : carrierFilter;
    }

    function filteredCarrierCells() {
      return cells.features.filter(feature => {
        const carrier = normalizedCarrierValue(feature.properties.CARRIER);
        if (carrierFilter !== 'all') return carrier === carrierFilter;
        return true;
      });
    }

    function carrierLegendBadge() {
      const visibleCells = filteredCarrierCells().length;
      return `<div class="hint" style="margin-bottom:8px">Carrier layer: <b>${carrierLayerLabel()}</b> | Planned cells: ${visibleCells.toLocaleString()}</div>`;
    }

    function plannedMapLegendHtml() {
      const groups = new Map();
      const legendFeatures = filteredCarrierCells();
      for (const feature of legendFeatures) {
        const key = legendKeyForMode(feature.properties);
        const color = legendColorForMode(feature.properties);
        const current = groups.get(key) || { count:0, color };
        if (colorMode === 'technologyColor' && key === '4G') current.color = '#22c55e';
        if (colorMode === 'technologyColor' && key === '5G') current.color = '#a855f7';
        current.count += 1;
        groups.set(key, current);
      }
      const rows = [...groups.entries()]
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, colorMode === 'tacColor' ? 14 : 20);
      const total = legendFeatures.length || 1;
      return `
        <div class="section-title" style="margin-top:0">Planned Network Legend</div>
        ${carrierLegendBadge()}
        <div class="hint" style="margin-bottom:8px">${colorMode === 'tacColor'
          ? 'Planned cells colored by LAC/TAC area.'
          : colorMode === 'vendorColor'
          ? 'Planned cells colored by vendor.'
          : 'Current planned-network map color mode.'}</div>
        ${rows.map(([key, value]) => {
          const pct = ((value.count / total) * 100).toFixed(1);
          return `<div class="legend-row"><span class="swatch" style="background:${value.color}"></span><span>${key}</span><b>${pct}%</b></div>`;
        }).join('')}
      `;
    }

    function dtLegendHtml() {
      if (!dtVisible || !dtPoints.features.length) return '';
      if (dtColorMode !== 'pciColor') {
        const rows = dtRangeLegend();
        const legendTitle = dtColorMode === 'kpiColor'
          ? `${dtModeLabel()} Load Legend`
          : `${hasMeasuredCoverageLayer ? 'Measured Coverage' : 'DT'} ${dtColorMode.replace('Color', '').toUpperCase()} Legend`;
        const legendHint = dtColorMode === 'kpiColor'
          ? 'Weighted numeric traffic/resource values joined to planned cell coordinates.'
          : 'Measured RF quality ranges. Percentages are from loaded samples or cell-level MR values.';
        return `
          <div class="section-title" style="margin-top:0">${legendTitle}</div>
          <div class="hint" style="margin-bottom:8px">${legendHint}</div>
          ${rows.map(([color, label, pct]) => `<div class="legend-row"><span class="swatch" style="background:${color}"></span><span>${label}</span><b>${pct}%</b></div>`).join('')}
        `;
      }
      const groups = new Map();
      for (const feature of dtPoints.features) {
        const key = `PCI ${feature.properties.PCI || 'Unknown'}`;
        const color = feature.properties.pciColor;
        const current = groups.get(key) || { count:0, color };
        current.count += 1;
        groups.set(key, current);
      }
      const rows = [...groups.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 18);
      const total = dtPoints.features.length || 1;
      return `
        <div class="section-title" style="margin-top:0">DT PCI Identity</div>
        <div class="hint" style="margin-bottom:8px">Measured DT samples colored by PCI. Same PCI gets the same color.</div>
        ${rows.map(([key, value]) => {
          const pct = ((value.count / total) * 100).toFixed(1);
          return `<div class="legend-row"><span class="swatch" style="background:${value.color}"></span><span>${key}</span><b>${pct}%</b></div>`;
        }).join('')}
      `;
    }

    function coverageLegendHtml() {
      if (!atollVisible || !atollOverlay.available || !Array.isArray(atollOverlay.legend) || !atollOverlay.legend.length) return '';
      return `
        <div class="section-title" style="margin-top:0">Coverage Prediction Legend</div>
        <div class="hint" style="margin-bottom:8px">Atoll raster colors sampled from ${escapeHtml(atollOverlay.source || 'coverage raster')}.</div>
        ${atollOverlay.legend.map(row => (
          `<div class="legend-row"><span class="swatch" style="background:${row.color}"></span><span>${escapeHtml(row.label)}</span><b>${Number(row.pct || 0).toFixed(1)}%</b></div>`
        )).join('')}
      `;
    }

    function renderLegend() {
      const floatingPanel = document.getElementById('floatingLegend');
      const dtPanel = document.getElementById('dtFloatingLegend');
      if (!legendVisible) {
        floatingPanel.style.display = 'none';
        dtPanel.style.display = 'none';
        return;
      }
      floatingPanel.style.display = 'block';
      floatingPanel.innerHTML = plannedMapLegendHtml();
      const dtHtml = [dtLegendHtml(), coverageLegendHtml()].filter(Boolean).join('<div class="legend-separator"></div>');
      dtPanel.style.display = dtHtml ? 'block' : 'none';
      dtPanel.innerHTML = dtHtml;
    }

    function forceLegendOn() {
      legendVisible = true;
      renderLegend();
    }

    function applyColorMode() {
      const colorExpression = propertyColorExpression();
      if (map.getLayer('site-dots')) {
        map.setPaintProperty('site-dots', 'circle-color', colorExpression);
      }
      if (map.getLayer('rf-shell-fill')) {
        map.setPaintProperty('rf-shell-fill', 'fill-color', colorExpression);
      }
      if (map.getLayer('rf-shell-outline')) {
        map.setPaintProperty('rf-shell-outline', 'line-color', colorExpression);
      }
      drawNetworkOverlay();
      renderLegend();
    }

    function dtWeightProperty() {
      if (dtColorMode === 'kpiColor') return 'kpiWeight';
      if (dtColorMode === 'rsrqColor') return 'rsrqWeight';
      if (dtColorMode === 'sinrColor') return 'sinrWeight';
      return 'rsrpWeight';
    }

    function dtHeatmapColorRamp() {
      if (dtColorMode === 'rsrpColor') {
        return [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0, 0, 0, 0)',
          0.12, '#0b2f9f',
          0.25, '#1148e8',
          0.38, '#73d2e8',
          0.52, '#00cc00',
          0.68, '#ffd84d',
          0.82, '#cc0000',
          1, '#ff0000'
        ];
      }
      if (dtColorMode === 'kpiColor') {
        return [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0, 0, 0, 0)',
          0.10, 'rgba(22, 163, 74, 0.28)',
          0.26, '#16a34a',
          0.42, '#2dd4bf',
          0.58, '#2563eb',
          0.72, '#fde047',
          0.86, '#f97316',
          1, '#ef4444'
        ];
      }
      if (dtColorMode === 'pciColor') {
        return [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0, 0, 0, 0)',
          0.18, '#0f766e',
          0.36, '#0ea5e9',
          0.54, '#8b5cf6',
          0.72, '#f59e0b',
          1, '#ef4444'
        ];
      }
      return [
        'interpolate', ['linear'], ['heatmap-density'],
        0, 'rgba(0, 0, 0, 0)',
        0.15, '#ef4444',
        0.32, '#f97316',
        0.50, '#ffd84d',
        0.68, '#73d2e8',
        1, '#00cc00'
      ];
    }

    function dtHeatmapRadiusExpression() {
      return [
        'interpolate', ['linear'], ['zoom'],
        8, heatRadiusScale,
        12, heatRadiusScale,
        15, heatRadiusScale
      ];
    }

    function dtHeatmapIntensityExpression() {
      return [
        'interpolate', ['linear'], ['zoom'],
        8, heatIntensityScale,
        12, heatIntensityScale,
        15, heatIntensityScale
      ];
    }

    function dtHeatmapOpacityExpression() {
      return [
        'interpolate', ['linear'], ['zoom'],
        8, 0.92 * heatOpacityScale,
        14, 0.82 * heatOpacityScale
      ];
    }

    function applyDtHeatTuning() {
      drawNetworkOverlay();
    }

    function applyDtViewMode() {
      const showPoints = dtVisible && dtPoints.features.length && dtViewMode !== 'heatmap';
      setLayerVisibility(['dt-heatmap'], false);
      setLayerVisibility(['dt-points'], showPoints);
      if (!showPoints && map.getLayer('dt-selected-ring')) {
        map.setFilter('dt-selected-ring', ['==', ['get','index'], -1]);
      }
      raiseShellsAboveHeatmap();
      if (networkCtx && map) drawNetworkOverlay();
    }

    function applyDtColorMode() {
      if (map.getLayer('dt-points')) {
        map.setPaintProperty('dt-points', 'circle-color', ['get', dtColorMode]);
      }
      if (map.getLayer('dt-heatmap')) {
        map.setPaintProperty('dt-heatmap', 'heatmap-weight', ['interpolate', ['linear'], ['get', dtWeightProperty()], 0, 0.12, 1, 1]);
        map.setPaintProperty('dt-heatmap', 'heatmap-color', dtHeatmapColorRamp());
      }
      document.getElementById('dtModeText').textContent = dtModeLabel();
      applyDtViewMode();
      raiseShellsAboveHeatmap();
      renderLegend();
    }

    function setLayerVisibility(layerIds, isVisible) {
      for (const layerId of layerIds) {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, 'visibility', isVisible ? 'visible' : 'none');
        }
      }
    }

    function labelExpression() {
      if (labelMode === 'site') return ['get', 'SITE_NAME'];
      if (labelMode === 'both') return ['concat', ['get', 'SITE_NAME'], ' / ', ['get', 'CARRIER']];
      return ['get', 'CARRIER'];
    }

    function labelTextForProps(props) {
      if (labelMode === 'site') return props.SITE_NAME || '';
      if (labelMode === 'both') return `${props.SITE_NAME || '-'} / ${shortCarrierLabel(props) || '-'}`;
      return shortCarrierLabel(props);
    }

    function shellLabelGeometry(feature) {
      const ring = scaledRing(feature.geometry.coordinates[0] || []);
      if (ring.length < 3) return null;
      const origin = ring[0];
      const tip = ring[Math.floor(ring.length / 2)] || ring[1];
      const anchor = [
        origin[0] + (tip[0] - origin[0]) * 0.58,
        origin[1] + (tip[1] - origin[1]) * 0.58
      ];
      return { origin, tip, anchor };
    }

    function shellLabelPoint(feature) {
      const geometry = shellLabelGeometry(feature);
      return geometry ? geometry.anchor : null;
    }

    function carrierLabelRank(label) {
      const key = normalizedCarrierValue(label);
      const ranks = {
        F4: 5,
        F3: 8,
        N35: 10,
        F2: 20,
        NR2600: 30,
        L2300: 40,
        L2100: 50,
        L18: 60,
        F1: 70,
        NR900: 80,
        L07: 90,
      };
      return ranks[key] || 120;
    }

    function sectorLabelKey(feature) {
      const props = feature.properties || {};
      const origin = feature.geometry.coordinates[0]?.[0] || [];
      const lon = Number(origin[0] || 0).toFixed(5);
      const lat = Number(origin[1] || 0).toFixed(5);
      const azimuth = Math.round(Number(props.AZIMUTH || 0) / 5) * 5;
      return `${props.SITE_NAME || ''}|${lon}|${lat}|${azimuth}`;
    }

    function drawCanvasLabel(text, x, y, fillStyle = '#22d3ee', strokeWidth = 3.2) {
      networkCtx.lineWidth = strokeWidth;
      networkCtx.strokeStyle = 'rgba(2,6,23,0.94)';
      networkCtx.strokeText(text, x, y);
      networkCtx.fillStyle = fillStyle;
      networkCtx.fillText(text, x, y);
    }

    function drawCarrierShellLabels(width, height) {
      const groups = new Map();
      for (const feature of shells.features) {
        const props = feature.properties || {};
        if (!carrierVisibleForOverlay(props)) continue;
        const label = shortCarrierLabel(props);
        if (!label) continue;
        const geometry = shellLabelGeometry(feature);
        if (!geometry) continue;
        const key = sectorLabelKey(feature);
        const group = groups.get(key) || {
          anchor: geometry.anchor,
          labels: [],
        };
        if (!group.labels.includes(label)) group.labels.push(label);
        groups.set(key, group);
      }

      networkCtx.font = `950 ${Math.max(10, Math.min(14, map.getZoom() * 0.88))}px Segoe UI, Arial, sans-serif`;
      networkCtx.textAlign = 'center';
      networkCtx.textBaseline = 'middle';
      for (const group of groups.values()) {
        const point = map.project(group.anchor);
        if (!inLooseViewport(point, width, height, 28)) continue;
        const labels = group.labels.sort((a, b) => carrierLabelRank(b) - carrierLabelRank(a) || a.localeCompare(b));
        const lineHeight = Math.max(12, Math.min(17, map.getZoom() * 1.05));
        const startY = point.y - ((labels.length - 1) * lineHeight) / 2;
        labels.forEach((label, index) => {
          drawCanvasLabel(label, point.x, startY + index * lineHeight, '#38d9ff', 3.4);
        });
      }
    }

    function applyLabelMode() {
      if (map.getLayer('cell-labels')) {
        map.setLayoutProperty('cell-labels', 'text-field', labelExpression());
      }
      setLayerVisibility(['cell-labels'], false);
      drawNetworkOverlay();
    }

    function carrierExpression() {
      if (carrierFilter !== 'all') {
        const carrier = ['upcase', ['to-string', ['get','CARRIER']]];
        const rules = {
          F4: [['in', 'F4', carrier]],
          F3: [['in', 'F3', carrier]],
          N35: [['in', 'N35', carrier], ['in', 'NR35', carrier], ['in', 'NR3500', carrier], ['in', 'N3500', carrier]],
          F2: [['in', 'F2', carrier]],
          NR2600: [['in', 'NR26', carrier], ['in', 'NR2600', carrier], ['in', 'N26', carrier], ['in', 'N2600', carrier]],
          L2300: [['in', 'L23', carrier], ['in', 'L2300', carrier], ['in', 'N23', carrier], ['in', 'NR23', carrier]],
          L2100: [['in', 'L21', carrier], ['in', 'L2100', carrier]],
          L18: [['in', 'L18', carrier], ['in', 'L1800', carrier]],
          F1: [['in', 'F1', carrier]],
          NR900: [['in', 'N09', carrier], ['in', 'NR09', carrier], ['in', 'N900', carrier], ['in', 'NR900', carrier]],
          L07: [['in', 'L07', carrier], ['in', 'NR07', carrier], ['in', 'L700', carrier], ['in', 'NR700', carrier]],
        };
        return ['any', ...(rules[carrierFilter] || [['==', carrier, carrierFilter.toUpperCase()]])];
      }
      return null;
    }

    function ncellRelationExpression() {
      if (ncellRelationFilter === 'all') return null;
      return ['==', ['get','relation'], ncellRelationFilter];
    }

    function applyNcellRelationFilter() {
      setFilterSafe('manual-ncell-lines', ncellRelationExpression());
      setFilterSafe('manual-ncell-hit', ncellRelationExpression());
      setFilterSafe('existing-anr-lines', ncellRelationExpression());
      setFilterSafe('existing-anr-hit', ncellRelationExpression());
      if (networkCtx && map) drawNetworkOverlay();
    }

    function combineFilters(...filters) {
      const realFilters = filters.filter(filter => filter !== null && filter !== true && filter !== undefined);
      if (!realFilters.length) return null;
      if (realFilters.length === 1) return realFilters[0];
      return ['all', ...realFilters];
    }

    function setFilterSafe(layerId, filter) {
      if (map.getLayer(layerId)) map.setFilter(layerId, filter || null);
    }

    function moveLayerSafe(layerId, beforeId = undefined) {
      if (!map.getLayer(layerId)) return;
      if (beforeId && !map.getLayer(beforeId)) return;
      try {
        beforeId ? map.moveLayer(layerId, beforeId) : map.moveLayer(layerId);
      } catch (err) {
        console.warn(`Could not move layer ${layerId}`, err);
      }
    }

    function applyCarrierFilter() {
      const carrier = carrierExpression();
      setFilterSafe('site-dots', carrier);
      setFilterSafe('rf-shell-fill', carrier);
      setFilterSafe('rf-shell-outline', carrier);
      setFilterSafe('cell-labels', carrier);
      applyNcellRelationFilter();
      refreshExistingAnrLayers();
      applySelectedPciMatch();
      applyNearestCellHighlight();
      raiseShellsAboveHeatmap();
      drawNetworkOverlay();
      renderLegend();
    }

    function raiseShellsAboveHeatmap() {
      moveLayerSafe('dt-heatmap', 'rf-shell-fill');
      moveLayerSafe('rf-shell-fill');
      moveLayerSafe('rf-shell-outline');
      moveLayerSafe('manual-ncell-lines');
      moveLayerSafe('manual-ncell-hit');
      moveLayerSafe('existing-anr-lines');
      moveLayerSafe('existing-anr-hit');
      moveLayerSafe('site-dots');
      moveLayerSafe('existing-anr-source-shell-fill');
      moveLayerSafe('existing-anr-neighbor-shells-fill');
      moveLayerSafe('existing-anr-source-shell');
      moveLayerSafe('existing-anr-neighbor-shells');
      moveLayerSafe('existing-anr-neighbor-sites');
      moveLayerSafe('worst-shell-highlight');
      moveLayerSafe('worst-site-highlight');
      moveLayerSafe('cell-labels');
      moveLayerSafe('pci-shell-match');
      moveLayerSafe('pci-site-match');
      moveLayerSafe('nearest-shell-candidates');
      moveLayerSafe('nearest-site-candidates');
      moveLayerSafe('dt-candidate-lines');
      moveLayerSafe('dt-points');
      moveLayerSafe('dt-selected-ring');
    }

    function applyPointerMode() {
      document.body.classList.toggle('cursor-select', pointerMode === 'select');
      document.body.classList.toggle('cursor-pan', pointerMode === 'pan');
      if (map && map.getCanvas) {
        map.getCanvas().style.cursor = pointerMode === 'select' ? 'crosshair' : 'grab';
      }
      const selectBtn = document.getElementById('pointerSelectBtn');
      const handBtn = document.getElementById('pointerHandBtn');
      if (selectBtn && handBtn) {
        selectBtn.classList.toggle('active', pointerMode === 'select');
        handBtn.classList.toggle('active', pointerMode === 'pan');
      }
    }

    function clickableCursor() {
      applyPointerMode();
    }

    function restoreCursor() {
      applyPointerMode();
    }

    function refreshSiteMarkerStyle(redraw = true) {
      if (map && map.getLayer && map.getLayer('site-dots')) {
        map.setPaintProperty('site-dots', 'circle-radius', [
          'interpolate', ['linear'], ['zoom'],
          8, 8 * siteMarkerScale,
          13, 11 * siteMarkerScale,
          16, 14 * siteMarkerScale
        ]);
        map.setPaintProperty('site-dots', 'circle-stroke-width', [
          'interpolate', ['linear'], ['zoom'],
          8, 1.3 * Math.min(siteMarkerScale, 2.2),
          13, 1.9 * Math.min(siteMarkerScale, 2.2),
          16, 2.4 * Math.min(siteMarkerScale, 2.2)
        ]);
      }
      if (redraw) {
        drawNetworkOverlay();
      }
    }

    const networkCanvas = document.getElementById('networkCanvas');
    const networkCtx = networkCanvas.getContext('2d');
    const heatCanvas = document.createElement('canvas');
    const heatCtx = heatCanvas.getContext('2d', { willReadFrequently:true });

    function carrierVisibleForOverlay(props) {
      if (carrierFilter === 'all') return true;
      return normalizedCarrierValue(props.CARRIER) === carrierFilter;
    }

    function cellPassesCarrierFilter(cellName) {
      if (carrierFilter === 'all') return true;
      const feature = featureForCell(cellName) || cellFeatureForCell(cellName);
      return feature ? carrierVisibleForOverlay(feature.properties || {}) : false;
    }

    function resizeNetworkCanvas() {
      const rect = document.getElementById('map').getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      const width = Math.max(1, Math.round(rect.width * ratio));
      const height = Math.max(1, Math.round(rect.height * ratio));
      if (networkCanvas.width !== width || networkCanvas.height !== height) {
        networkCanvas.width = width;
        networkCanvas.height = height;
        networkCanvas.style.width = `${rect.width}px`;
        networkCanvas.style.height = `${rect.height}px`;
      }
      networkCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
      return { width: rect.width, height: rect.height };
    }

    function inLooseViewport(point, width, height, pad = 80) {
      return point.x >= -pad && point.x <= width + pad && point.y >= -pad && point.y <= height + pad;
    }

    function refreshShellGeometry(redraw = true) {
      const shellSource = map && map.getSource ? map.getSource('shells') : null;
      if (shellSource) {
        shellSource.setData(scaledShellsGeojson());
      }
      const ncellSource = map && map.getSource ? map.getSource('manual-ncells') : null;
      if (ncellSource) {
        ncellSource.setData(buildManualLines());
      }
      const existingAnrSource = map && map.getSource ? map.getSource('existing-anr-lines') : null;
      if (existingAnrSource) {
        existingAnrSource.setData(buildExistingAnrLines());
      }
      if (redraw) {
        drawNetworkOverlay();
      }
    }

    function pointInPolygon(point, polygon) {
      let inside = false;
      for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const xi = polygon[i].x;
        const yi = polygon[i].y;
        const xj = polygon[j].x;
        const yj = polygon[j].y;
        const intersects = ((yi > point.y) !== (yj > point.y))
          && (point.x < (xj - xi) * (point.y - yi) / ((yj - yi) || 0.000001) + xi);
        if (intersects) inside = !inside;
      }
      return inside;
    }

    function distanceToSegment(point, start, end) {
      const dx = end.x - start.x;
      const dy = end.y - start.y;
      const lengthSquared = dx * dx + dy * dy;
      if (!lengthSquared) return Math.hypot(point.x - start.x, point.y - start.y);
      const t = Math.max(0, Math.min(1, ((point.x - start.x) * dx + (point.y - start.y) * dy) / lengthSquared));
      const projected = { x: start.x + t * dx, y: start.y + t * dy };
      return Math.hypot(point.x - projected.x, point.y - projected.y);
    }

    function polygonEdgeDistance(point, polygon) {
      let best = Infinity;
      for (let i = 0; i < polygon.length - 1; i++) {
        best = Math.min(best, distanceToSegment(point, polygon[i], polygon[i + 1]));
      }
      return best;
    }

    function nearestOverlayShell(point, tolerance = 14) {
      let bestInside = null;
      let bestInsideDistance = Infinity;
      let bestEdge = null;
      let bestEdgeDistance = tolerance;
      for (const feature of shells.features) {
        const props = feature.properties || {};
        if (!carrierVisibleForOverlay(props)) continue;
        const ring = scaledRing(feature.geometry.coordinates[0] || []);
        if (ring.length < 3) continue;
        const projected = ring.map(([lon, lat]) => map.project([lon, lat]));
        const originDistance = Math.hypot(projected[0].x - point.x, projected[0].y - point.y);
        if (pointInPolygon(point, projected) && originDistance < bestInsideDistance) {
          bestInsideDistance = originDistance;
          bestInside = feature;
        }
        const edgeDistance = polygonEdgeDistance(point, projected);
        if (edgeDistance < bestEdgeDistance) {
          bestEdgeDistance = edgeDistance;
          bestEdge = feature;
        }
      }
      return bestInside || bestEdge;
    }

    function projectedShellRing(feature) {
      const ring = feature.geometry.coordinates[0] || [];
      if (ring.length < 3) return [];
      return scaledRing(ring).map(([lon, lat]) => map.project([lon, lat]));
    }

    function drawProjectedPolygon(projected, fillStyle, strokeStyle, fillAlpha, strokeAlpha, lineWidth) {
      if (!projected.length) return;
      networkCtx.beginPath();
      projected.forEach((point, idx) => {
        if (idx === 0) networkCtx.moveTo(point.x, point.y);
        else networkCtx.lineTo(point.x, point.y);
      });
      networkCtx.closePath();
      networkCtx.fillStyle = fillStyle;
      networkCtx.strokeStyle = strokeStyle;
      networkCtx.lineWidth = lineWidth;
      networkCtx.globalAlpha = fillAlpha;
      networkCtx.fill();
      networkCtx.globalAlpha = strokeAlpha;
      networkCtx.stroke();
      networkCtx.globalAlpha = 1;
    }

    function drawShellOverlayFeature(feature, width, height, fillStyle, strokeStyle, fillAlpha, strokeAlpha, lineWidth) {
      const projected = projectedShellRing(feature);
      if (!projected.length || !projected.some(point => inLooseViewport(point, width, height))) return;
      drawProjectedPolygon(projected, fillStyle, strokeStyle, fillAlpha, strokeAlpha, lineWidth);
    }

    function colorWithAlpha(color, alpha) {
      const text = String(color || '').trim();
      const hex = text.replace('#', '');
      if (/^[0-9a-f]{6}$/i.test(hex)) {
        const red = parseInt(hex.slice(0, 2), 16);
        const green = parseInt(hex.slice(2, 4), 16);
        const blue = parseInt(hex.slice(4, 6), 16);
        return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
      }
      if (/^[0-9a-f]{3}$/i.test(hex)) {
        const red = parseInt(hex[0] + hex[0], 16);
        const green = parseInt(hex[1] + hex[1], 16);
        const blue = parseInt(hex[2] + hex[2], 16);
        return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
      }
      return `rgba(34, 211, 238, ${alpha})`;
    }

    const oldMapHeatColors = [
      [16, 185, 129, 35],
      [34, 211, 238, 80],
      [59, 130, 246, 120],
      [245, 158, 11, 160],
      [239, 68, 68, 220],
    ];

    function numericValue(value) {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    }

    function heatRawValue(props) {
      if (dtColorMode === 'kpiColor') {
        return Math.abs(numericValue(props.KPI_VALUE) ?? numericValue(props.kpiAbsWeight) ?? 0);
      }
      if (dtColorMode === 'rsrqColor') return Math.abs(numericValue(props.RSRQ) ?? 0);
      if (dtColorMode === 'sinrColor') return Math.abs(numericValue(props.SINR) ?? 0);
      return Math.abs(numericValue(props.RSRP) ?? 0);
    }

    function percentile(sortedValues, ratio) {
      if (!sortedValues.length) return 1;
      const index = Math.max(0, Math.min(sortedValues.length - 1, Math.floor((sortedValues.length - 1) * ratio)));
      return sortedValues[index] || 1;
    }

    function oldMapHeatColor(t) {
      const value = Math.max(0, Math.min(1, t));
      const scaled = value * (oldMapHeatColors.length - 1);
      const lower = Math.floor(scaled);
      const upper = Math.min(oldMapHeatColors.length - 1, lower + 1);
      const mix = scaled - lower;
      const a = oldMapHeatColors[lower];
      const b = oldMapHeatColors[upper];
      return [
        Math.round(a[0] + (b[0] - a[0]) * mix),
        Math.round(a[1] + (b[1] - a[1]) * mix),
        Math.round(a[2] + (b[2] - a[2]) * mix),
        Math.round((a[3] + (b[3] - a[3]) * mix) * heatOpacityScale),
      ];
    }

    function ensureHeatCanvas(width, height, scale) {
      const targetWidth = Math.max(1, Math.round(width * scale));
      const targetHeight = Math.max(1, Math.round(height * scale));
      if (heatCanvas.width !== targetWidth || heatCanvas.height !== targetHeight) {
        heatCanvas.width = targetWidth;
        heatCanvas.height = targetHeight;
      }
      heatCtx.setTransform(1, 0, 0, 1, 0, 0);
      heatCtx.clearRect(0, 0, targetWidth, targetHeight);
      return { targetWidth, targetHeight };
    }

    function hexToRgbArray(color) {
      const text = String(color || '').trim().replace('#', '');
      if (/^[0-9a-f]{6}$/i.test(text)) {
        return [parseInt(text.slice(0, 2), 16), parseInt(text.slice(2, 4), 16), parseInt(text.slice(4, 6), 16)];
      }
      if (/^[0-9a-f]{3}$/i.test(text)) {
        return [parseInt(text[0] + text[0], 16), parseInt(text[1] + text[1], 16), parseInt(text[2] + text[2], 16)];
      }
      return null;
    }

    function isCoverageHeatMode() {
      return dtColorMode === 'rsrpColor' || dtColorMode === 'rsrqColor' || dtColorMode === 'sinrColor';
    }

    function drawLegendBinnedCoverageHeatmap(width, height, heatScale, radius) {
      const { targetWidth, targetHeight } = ensureHeatCanvas(width, height, heatScale);
      const groups = new Map();
      for (const feature of dtPoints.features) {
        const coordinate = feature.geometry?.coordinates;
        if (!coordinate) continue;
        const point = map.project(coordinate);
        if (!inLooseViewport(point, width, height, heatRadiusScale + 30)) continue;
        const props = feature.properties || {};
        const color = dtLegendColorForFeature(props);
        if (!color || !hexToRgbArray(color)) continue;
        if (!groups.has(color)) groups.set(color, []);
        groups.get(color).push({ x:point.x * heatScale, y:point.y * heatScale });
      }
      if (!groups.size) return;

      const legendOrder = normalizedLegendRows(dtColorMode).map(row => row[0]);
      const ordered = dtColorMode === 'rsrqColor' || dtColorMode === 'sinrColor'
        ? [...legendOrder].reverse()
        : [...legendOrder];
      for (const color of groups.keys()) {
        if (!ordered.includes(color)) ordered.push(color);
      }

      networkCtx.save();
      networkCtx.globalCompositeOperation = 'source-over';
      for (const color of ordered) {
        const items = groups.get(color);
        if (!items || !items.length) continue;
        const rgb = hexToRgbArray(color);
        if (!rgb) continue;
        ensureHeatCanvas(width, height, heatScale);
        heatCtx.save();
        heatCtx.globalCompositeOperation = 'source-over';
        const alpha = Math.min(0.38, Math.max(0.035, 0.085 * heatIntensityScale));
        for (const item of items) {
          const gradient = heatCtx.createRadialGradient(item.x, item.y, 0, item.x, item.y, radius);
          gradient.addColorStop(0, `rgba(255,255,255,${alpha})`);
          gradient.addColorStop(0.45, `rgba(255,255,255,${alpha * 0.55})`);
          gradient.addColorStop(1, 'rgba(255,255,255,0)');
          heatCtx.fillStyle = gradient;
          heatCtx.beginPath();
          heatCtx.arc(item.x, item.y, radius, 0, Math.PI * 2);
          heatCtx.fill();
        }
        heatCtx.restore();

        const image = heatCtx.getImageData(0, 0, targetWidth, targetHeight);
        const data = image.data;
        for (let idx = 0; idx < data.length; idx += 4) {
          const density = data[idx + 3] / 255;
          if (density < 0.018) {
            data[idx + 3] = 0;
            continue;
          }
          data[idx] = rgb[0];
          data[idx + 1] = rgb[1];
          data[idx + 2] = rgb[2];
          data[idx + 3] = Math.round(Math.min(172, data[idx + 3] * heatOpacityScale * 0.78));
        }
        heatCtx.putImageData(image, 0, 0);
        networkCtx.drawImage(heatCanvas, 0, 0, width, height);
      }
      networkCtx.restore();
    }

    function drawTrafficHeatmapOverlay(width, height) {
      if (!dtVisible || !dtPoints.features.length || dtViewMode === 'points' || dtColorMode === 'pciColor' || !heatCtx) return;
      const heatScale = 0.58;
      const radius = Math.max(10, Math.min(120, heatRadiusScale)) * heatScale;
      if (isCoverageHeatMode()) {
        drawLegendBinnedCoverageHeatmap(width, height, heatScale, radius);
        return;
      }
      const { targetWidth, targetHeight } = ensureHeatCanvas(width, height, heatScale);
      const visible = [];
      const weights = [];
      for (const feature of dtPoints.features) {
        const coordinate = feature.geometry?.coordinates;
        if (!coordinate) continue;
        const point = map.project(coordinate);
        if (!inLooseViewport(point, width, height, heatRadiusScale + 30)) continue;
        const raw = heatRawValue(feature.properties || {});
        if (!Number.isFinite(raw) || raw <= 0) continue;
        visible.push({ x:point.x * heatScale, y:point.y * heatScale, raw });
        weights.push(raw);
      }
      if (!visible.length) return;
      weights.sort((a, b) => a - b);
      const reference = Math.max(1, percentile(weights, 0.90));

      heatCtx.save();
      heatCtx.globalCompositeOperation = 'lighter';
      for (const item of visible) {
        const weight = Math.max(0.06, Math.min(1, item.raw / reference));
        const alpha = Math.min(0.72, Math.max(0.045, weight * 0.24 * heatIntensityScale));
        const gradient = heatCtx.createRadialGradient(item.x, item.y, 0, item.x, item.y, radius);
        gradient.addColorStop(0, `rgba(255,255,255,${alpha})`);
        gradient.addColorStop(0.42, `rgba(255,255,255,${alpha * 0.52})`);
        gradient.addColorStop(1, 'rgba(255,255,255,0)');
        heatCtx.fillStyle = gradient;
        heatCtx.beginPath();
        heatCtx.arc(item.x, item.y, radius, 0, Math.PI * 2);
        heatCtx.fill();
      }
      heatCtx.restore();

      const image = heatCtx.getImageData(0, 0, targetWidth, targetHeight);
      const data = image.data;
      const threshold = 0.05;
      for (let idx = 0; idx < data.length; idx += 4) {
        const density = data[idx + 3] / 255;
        if (density < threshold) {
          data[idx + 3] = 0;
          continue;
        }
        const t = Math.max(0, Math.min(1, (density - threshold) / (1 - threshold)));
        const color = oldMapHeatColor(t);
        data[idx] = color[0];
        data[idx + 1] = color[1];
        data[idx + 2] = color[2];
        data[idx + 3] = color[3];
      }
      heatCtx.putImageData(image, 0, 0);
      networkCtx.save();
      networkCtx.imageSmoothingEnabled = true;
      networkCtx.drawImage(heatCanvas, 0, 0, width, height);
      networkCtx.restore();
    }
    function relationVisibleForOverlay(relation) {
      return ncellRelationFilter === 'all' || relation === ncellRelationFilter;
    }

    function drawManualNcellOverlay(width, height) {
      if (!ncellVisible) return;
      const rows = manualLinkRows().filter(row => row && relationVisibleForOverlay(row.relation));
      if (!rows.length) return;
      for (const row of rows) {
        const edgeCoordinates = shellEdgeLineCoordinates(row.source, row.target);
        if (!edgeCoordinates) continue;
        const source = map.project(edgeCoordinates[0]);
        const target = map.project(edgeCoordinates[1]);
        if (!inLooseViewport(source, width, height, 120) && !inLooseViewport(target, width, height, 120)) continue;
        networkCtx.globalAlpha = 0.96;
        networkCtx.lineCap = 'round';
        networkCtx.beginPath();
        networkCtx.moveTo(source.x, source.y);
        networkCtx.lineTo(target.x, target.y);
        networkCtx.strokeStyle = 'rgba(2,6,23,0.86)';
        networkCtx.lineWidth = Math.max(3.6, Math.min(6.2, map.getZoom() * 0.40));
        networkCtx.stroke();
        networkCtx.beginPath();
        networkCtx.moveTo(source.x, source.y);
        networkCtx.lineTo(target.x, target.y);
        networkCtx.strokeStyle = row.relationColor || relationColor(row.relation);
        networkCtx.lineWidth = Math.max(1.4, Math.min(3.0, map.getZoom() * 0.20));
        networkCtx.stroke();
      }
      networkCtx.globalAlpha = 1;
    }

    function drawExistingAnrOverlay(width, height) {
      if (!ncellVisible || !existingAnrFocusCell) return;
      const rows = existingAnrVisibleRows();
      if (!rows.length) return;
      for (const row of rows) {
        const edgeCoordinates = shellEdgeLineCoordinates(row.source, row.target);
        if (!edgeCoordinates) continue;
        const source = map.project(edgeCoordinates[0]);
        const target = map.project(edgeCoordinates[1]);
        if (!inLooseViewport(source, width, height, 120) && !inLooseViewport(target, width, height, 120)) continue;
        const color = row.relationColor || relationColor(row.relation);
        networkCtx.globalAlpha = 0.98;
        networkCtx.lineCap = 'round';
        networkCtx.beginPath();
        networkCtx.moveTo(source.x, source.y);
        networkCtx.lineTo(target.x, target.y);
        networkCtx.strokeStyle = 'rgba(2,6,23,0.86)';
        networkCtx.lineWidth = Math.max(1.8, Math.min(3.0, map.getZoom() * 0.20));
        networkCtx.stroke();
        networkCtx.beginPath();
        networkCtx.moveTo(source.x, source.y);
        networkCtx.lineTo(target.x, target.y);
        networkCtx.strokeStyle = color;
        networkCtx.lineWidth = Math.max(0.7, Math.min(1.4, map.getZoom() * 0.09));
        networkCtx.stroke();
      }
      networkCtx.globalAlpha = 1;
    }

    function drawSelectedSiteOverlay(width, height) {
      const selectedNames = new Set(selectedCellGroup());
      if (!selectedNames.size) return;
      for (const feature of cells.features) {
        const props = feature.properties || {};
        if (!selectedNames.has(props.CELL_NAME)) continue;
        const point = map.project(feature.geometry.coordinates);
        if (!inLooseViewport(point, width, height, 40)) continue;
        const isSource = props.CELL_NAME === sourceCell;
        const radius = Math.max(11, Math.min(24, map.getZoom() * (isSource ? 1.55 : 1.25)));
        networkCtx.beginPath();
        networkCtx.arc(point.x, point.y, radius, 0, Math.PI * 2);
        networkCtx.fillStyle = isSource ? 'rgba(239,68,68,0.52)' : 'rgba(245,158,11,0.42)';
        networkCtx.strokeStyle = isSource ? '#ff2d2d' : '#fbbf24';
        networkCtx.lineWidth = isSource ? 4.5 : 3.5;
        networkCtx.fill();
        networkCtx.stroke();
      }
    }

    function drawNetworkOverlay() {
      if (!networkCtx || !map) return;
      const { width, height } = resizeNetworkCanvas();
      networkCtx.clearRect(0, 0, width, height);
      networkCtx.lineJoin = 'round';
      networkCtx.lineCap = 'round';

      drawTrafficHeatmapOverlay(width, height);

      if (shellsVisible) {
        for (const feature of shells.features) {
          const props = feature.properties || {};
          if (!carrierVisibleForOverlay(props)) continue;
          const projected = projectedShellRing(feature);
          if (!projected.length) continue;
          if (!projected.some(point => inLooseViewport(point, width, height))) continue;
          const color = legendColorForMode(props);
          drawProjectedPolygon(projected, color, color, 0.18, 0.95, Math.max(0.85, Math.min(1.35, map.getZoom() * 0.09)));
        }
      }

      if (sourceCell || targets.length) {
        const sourceKey = normalizeCellName(sourceCell);
        const targetNameSet = new Set(targets.map(name => normalizeCellName(name)));
        for (const feature of shells.features) {
          const props = feature.properties || {};
          const cellKey = normalizeCellName(props.CELL_NAME);
          if (cellKey === sourceKey) {
            drawShellOverlayFeature(feature, width, height, 'rgba(239,68,68,0.62)', '#ff2d2d', 0.78, 1, Math.max(3.2, Math.min(5.8, map.getZoom() * 0.38)));
          } else if (targetNameSet.has(cellKey)) {
            drawShellOverlayFeature(feature, width, height, 'rgba(250,204,21,0.62)', '#facc15', 0.80, 1, Math.max(2.8, Math.min(5.0, map.getZoom() * 0.34)));
          }
        }
      }

      if (existingAnrFocusCell && existingAnrRows.length) {
        const focusKey = normalizeCellName(existingAnrFocusCell);
        const neighborKeySet = new Set(existingAnrVisibleRows()
          .map(row => normalizeCellName(row.source) === focusKey ? row.target : row.source)
          .map(name => normalizeCellName(name))
          .filter(Boolean));
        for (const feature of shells.features) {
          const props = feature.properties || {};
          if (!carrierVisibleForOverlay(props)) continue;
          const cellKey = normalizeCellName(props.CELL_NAME);
          if (cellKey === focusKey) {
            drawShellOverlayFeature(feature, width, height, 'rgba(239,68,68,0.68)', '#ff2d2d', 0.84, 1, Math.max(3.8, Math.min(6.6, map.getZoom() * 0.44)));
          } else if (neighborKeySet.has(cellKey)) {
            drawShellOverlayFeature(feature, width, height, 'rgba(250,204,21,0.66)', '#facc15', 0.86, 1, Math.max(3.0, Math.min(5.6, map.getZoom() * 0.38)));
          }
        }
      }

      if (worstMatchedNames.length) {
        const worstNameSet = new Set(worstMatchedNames);
        for (const feature of shells.features) {
          const props = feature.properties || {};
          if (!worstNameSet.has(props.CELL_NAME)) continue;
          const projected = projectedShellRing(feature);
          if (!projected.length) continue;
          if (!projected.some(point => inLooseViewport(point, width, height))) continue;
          drawProjectedPolygon(projected, '#ef4444', '#ff2d2d', 0.52, 1, Math.max(1.4, Math.min(2.6, map.getZoom() * 0.16)));
        }
      }

      if (dotsVisible) {
        for (const feature of cells.features) {
          const props = feature.properties || {};
          if (!carrierVisibleForOverlay(props)) continue;
          const [lon, lat] = feature.geometry.coordinates;
          const point = map.project([lon, lat]);
          if (!inLooseViewport(point, width, height, 20)) continue;
          const color = legendColorForMode(props);
          const baseRadius = Math.max(4.8, Math.min(12.5, map.getZoom() * 0.78));
          const radius = baseRadius * siteMarkerScale;
          networkCtx.beginPath();
          networkCtx.arc(point.x, point.y, radius, 0, Math.PI * 2);
          networkCtx.fillStyle = color;
          networkCtx.strokeStyle = '#e0f2fe';
          networkCtx.lineWidth = 1.5;
          networkCtx.fill();
          networkCtx.stroke();
        }
      }

      drawManualNcellOverlay(width, height);
      drawExistingAnrOverlay(width, height);
      if (!ncellVisible) drawSelectedSiteOverlay(width, height);

      if (worstMatchedNames.length) {
        const worstNameSet = new Set(worstMatchedNames);
        for (const feature of cells.features) {
          const props = feature.properties || {};
          if (!worstNameSet.has(props.CELL_NAME)) continue;
          const [lon, lat] = feature.geometry.coordinates;
          const point = map.project([lon, lat]);
          if (!inLooseViewport(point, width, height, 30)) continue;
          const radius = Math.max(9, Math.min(20, map.getZoom() * 1.25));
          networkCtx.beginPath();
          networkCtx.arc(point.x, point.y, radius, 0, Math.PI * 2);
          networkCtx.fillStyle = 'rgba(239,68,68,0.28)';
          networkCtx.strokeStyle = '#ff2d2d';
          networkCtx.lineWidth = 3;
          networkCtx.fill();
          networkCtx.stroke();
        }
      }

      if (labelsVisible) {
        if (labelMode === 'cell' || labelMode === 'both') {
          drawCarrierShellLabels(width, height);
        }
        if (labelMode === 'site' || labelMode === 'both') {
          const seenSites = new Set();
          networkCtx.font = `900 ${Math.max(10, Math.min(15, map.getZoom() * 0.9))}px Segoe UI, Arial, sans-serif`;
          networkCtx.textAlign = 'center';
          networkCtx.textBaseline = 'middle';
          for (const feature of cells.features) {
            const props = feature.properties || {};
            const label = props.SITE_NAME || '';
            if (!label || seenSites.has(label) || !carrierVisibleForOverlay(props)) continue;
            seenSites.add(label);
            const [lon, lat] = feature.geometry.coordinates;
            const point = map.project([lon, lat]);
            if (!inLooseViewport(point, width, height, 24)) continue;
            const y = point.y - Math.max(15, Math.min(32, map.getZoom() * 1.55 * siteMarkerScale / 1.8));
            networkCtx.lineWidth = 4.2;
            networkCtx.strokeStyle = 'rgba(2,6,23,0.92)';
            networkCtx.strokeText(label, point.x, y);
            networkCtx.fillStyle = '#f8fafc';
            networkCtx.fillText(label, point.x, y);
          }
        }
      }
    }

    function nearestOverlayCell(point, tolerance = 16) {
      let best = null;
      let bestDistance = tolerance;
      for (const feature of cells.features) {
        const props = feature.properties || {};
        if (!carrierVisibleForOverlay(props)) continue;
        const projected = map.project(feature.geometry.coordinates);
        const distance = Math.hypot(projected.x - point.x, projected.y - point.y);
        if (distance <= bestDistance) {
          bestDistance = distance;
          best = feature;
        }
      }
      return best;
    }

    function renderedCellFeatureAtPoint(point, tolerance = 26) {
      if (!map) return null;
      const layers = ['site-dots', 'rf-shell-fill', 'rf-shell-outline'].filter(layerId => map.getLayer(layerId));
      if (!layers.length) return null;
      const box = [
        [point.x - tolerance, point.y - tolerance],
        [point.x + tolerance, point.y + tolerance]
      ];
      const hits = map.queryRenderedFeatures(box, { layers });
      if (!hits.length) return null;
      return hits
        .map(feature => {
          const coordinate = cellCoordinateForName(feature.properties?.CELL_NAME);
          const projected = coordinate ? map.project(coordinate) : null;
          const distance = projected ? Math.hypot(projected.x - point.x, projected.y - point.y) : 9999;
          return { feature, distance };
        })
        .sort((a, b) => a.distance - b.distance)[0].feature;
    }

    function nearestOverlayFeature(point) {
      return renderedCellFeatureAtPoint(point, 28)
        || nearestOverlayCell(point, 26)
        || (shellsVisible ? nearestOverlayShell(point, 34) : null);
    }

    function openCellFromMapClick(feature, lngLat) {
      lastCellOpenAt = Date.now();
      openCellFeature(feature, lngLat);
    }

    function openCellFeature(feature, lngLat) {
      if (!feature) return;
      if (areaMode) return;
      const props = feature.properties || {};
      if (selectionMode) {
        addCell(props.CELL_NAME);
      } else {
        showExistingAnrForCell(props.CELL_NAME);
      }
      updateAnrUi(props.CELL_NAME);
      if (!popupsVisible) return;
      new maplibregl.Popup({ closeButton:true, maxWidth:'360px' })
        .setLngLat(lngLat || feature.geometry.coordinates)
        .setHTML(cellPopup(props))
        .addTo(map);
    }

    function dtModeLabel() {
      if (dtColorMode === 'kpiColor') {
        return dtPoints.features[0]?.properties?.KPI_NAME || 'KPI';
      }
      return dtColorMode.replace('Color', '').toUpperCase();
    }

    function trafficPointLabel() {
      const suffix = dtColorMode === 'kpiColor' ? 'cells' : 'samples';
      return `${dtPoints.features.length.toLocaleString()} ${suffix}`;
    }

    function measuredCoverageActive() {
      return hasMeasuredCoverageLayer && dtVisible && dtColorMode !== 'kpiColor';
    }

    function coverageLayerAvailable() {
      return Boolean(atollOverlay.available || hasMeasuredCoverageLayer);
    }

    function coverageActive() {
      return Boolean(atollVisible || measuredCoverageActive());
    }

    function trafficButtonText() {
      if (!dtPoints.features.length) return 'No Traffic';
      if (hasTrafficLayer) return dtVisible ? 'Traffic ON' : 'Traffic OFF';
      return dtVisible ? 'Measured ON' : 'Measured OFF';
    }

    function coverageButtonText() {
      if (!coverageLayerAvailable()) return 'No Coverage';
      return coverageActive() ? 'Coverage ON' : 'Coverage OFF';
    }

    function syncTrafficCoverageButtons() {
      const dtBtn = document.getElementById('dtBtn');
      const atollBtn = document.getElementById('atollBtn');
      dtBtn.textContent = trafficButtonText();
      dtBtn.classList.toggle('active', dtVisible);
      atollBtn.textContent = coverageButtonText();
      atollBtn.classList.toggle('active', coverageActive());
      document.getElementById('atollStatus').textContent = coverageLayerAvailable()
        ? (coverageActive() ? 'ON' : 'OFF')
        : 'Missing';
    }

    function updateCompareStrip() {
      const dtLabel = dtVisible
        ? `${dtModeLabel()} ${dtViewMode === 'both' ? 'heatmap + points' : dtViewMode}`
        : (hasMeasuredCoverageLayer ? 'Measured coverage OFF' : 'Traffic OFF');
      document.getElementById('stripDtLayer').textContent = selectedDtSample
        ? `PCI ${selectedDtSample.PCI || '-'} sample`
        : dtLabel;
      document.getElementById('stripAtoll').textContent = coverageLayerAvailable()
        ? (coverageActive() ? 'Coverage ON' : 'Coverage OFF')
        : 'No Coverage';
      document.getElementById('stripDtCount').textContent = selectedDtSample
        ? (dtColorMode === 'kpiColor' ? `${selectedDtSample.KPI_NAME || 'KPI'} ${selectedDtSample.KPI_VALUE ?? '-'}` : `RSRP ${selectedDtSample.RSRP ?? '-'}`)
        : trafficPointLabel();
      if (selectedDtSample) {
        const nearestText = nearestCellsSummary();
        document.getElementById('compareNote').textContent =
          dtColorMode === 'kpiColor'
            ? `Selected Traffic/KPI cell: ${selectedDtSample.servingCell || '-'} | ${selectedDtSample.KPI_NAME || 'KPI'} ${selectedDtSample.KPI_VALUE ?? '-'} | Planned PCI matches: ${selectedPciMatchCount}.${nearestText ? ' Nearest: ' + nearestText : ''}`
            : `Selected DT sample: PCI ${selectedDtSample.PCI || '-'} | RSRP ${selectedDtSample.RSRP ?? '-'} dBm | RSRQ ${selectedDtSample.RSRQ ?? '-'} dB | SINR ${selectedDtSample.SINR ?? '-'} dB | Planned PCI matches: ${selectedPciMatchCount}.${nearestText ? ' Nearest: ' + nearestText : ''}`;
      } else {
        document.getElementById('compareNote').textContent = dtVisible && coverageActive()
          ? `Compare ${dtModeLabel()} heatmap against Atoll coverage prediction.`
          : 'Traffic load uses weighted numeric values; Coverage ON shows Atoll prediction or measured RF quality when available.';
      }
    }

    function updatePanelScrollButtons() {
      const panel = document.querySelector('.panel');
      const moreBtn = document.getElementById('panelMoreBtn');
      const maxScroll = panel.scrollHeight - panel.clientHeight;
      const nearBottom = panel.scrollTop >= maxScroll - 12;
      moreBtn.textContent = nearBottom ? 'Bottom' : 'More';
      moreBtn.classList.toggle('active', nearBottom);
    }

    function applySelectedPciMatch() {
      if (!selectedDtSample || selectedDtSample.PCI === undefined || selectedDtSample.PCI === null || selectedDtSample.PCI === '') {
        selectedPciMatchCount = 0;
        const emptyFilter = combineFilters(carrierExpression(), ['==', ['get','PCI'], '__none__']);
        if (map.getLayer('pci-site-match')) map.setFilter('pci-site-match', emptyFilter);
        if (map.getLayer('pci-shell-match')) map.setFilter('pci-shell-match', emptyFilter);
        return;
      }
      const pciText = String(selectedDtSample.PCI);
      selectedPciMatchCount = cells.features.filter(feature => String(feature.properties.PCI || '') === pciText).length;
      const filter = combineFilters(carrierExpression(), ['==', ['to-string', ['get','PCI']], pciText]);
      if (map.getLayer('pci-site-match')) map.setFilter('pci-site-match', filter);
      if (map.getLayer('pci-shell-match')) map.setFilter('pci-shell-match', filter);
    }

    function applyNearestCellHighlight() {
      const filter = selectedNearestCellNames.length
        ? combineFilters(carrierExpression(), ['in', ['get', 'CELL_NAME'], ['literal', selectedNearestCellNames]])
        : combineFilters(carrierExpression(), ['==', ['get', 'CELL_NAME'], '__none__']);
      if (map.getLayer('nearest-site-candidates')) map.setFilter('nearest-site-candidates', filter);
      if (map.getLayer('nearest-shell-candidates')) map.setFilter('nearest-shell-candidates', filter);
      if (map.getSource('dt-candidate-lines')) map.getSource('dt-candidate-lines').setData(nearestCandidateLines());
    }

    function featureForCell(cellName) {
      const key = normalizeCellName(cellName);
      return shells.features.find(f => normalizeCellName(f.properties.CELL_NAME) === key);
    }

    function cellFeatureForCell(cellName) {
      const key = normalizeCellName(cellName);
      return cells.features.find(f => normalizeCellName(f.properties.CELL_NAME) === key);
    }

    function cellCoordinateForName(cellName) {
      const shellFeature = featureForCell(cellName);
      if (shellFeature) return shellTip(shellFeature);
      const cellFeature = cellFeatureForCell(cellName);
      if (cellFeature && cellFeature.geometry && cellFeature.geometry.coordinates) {
        return cellFeature.geometry.coordinates;
      }
      return null;
    }

    function shellFeatureForCell(cellName) {
      return featureForCell(cellName);
    }

    function coordinateDistanceSquared(a, b) {
      if (!a || !b) return Infinity;
      const dx = Number(a[0]) - Number(b[0]);
      const dy = Number(a[1]) - Number(b[1]);
      return dx * dx + dy * dy;
    }

    function lineSegmentIntersection(a, b, c, d) {
      const r = [b[0] - a[0], b[1] - a[1]];
      const s = [d[0] - c[0], d[1] - c[1]];
      const denominator = r[0] * s[1] - r[1] * s[0];
      if (Math.abs(denominator) < 1e-14) return null;
      const qMinusP = [c[0] - a[0], c[1] - a[1]];
      const t = (qMinusP[0] * s[1] - qMinusP[1] * s[0]) / denominator;
      const u = (qMinusP[0] * r[1] - qMinusP[1] * r[0]) / denominator;
      if (t < -1e-9 || t > 1 + 1e-9 || u < -1e-9 || u > 1 + 1e-9) return null;
      return [a[0] + t * r[0], a[1] + t * r[1], t];
    }

    function closestPointOnSegment(point, start, end) {
      const dx = end[0] - start[0];
      const dy = end[1] - start[1];
      const lengthSquared = dx * dx + dy * dy;
      if (!lengthSquared) return start;
      const t = Math.max(0, Math.min(1, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / lengthSquared));
      return [start[0] + t * dx, start[1] + t * dy];
    }

    function closestShellBoundaryPoint(shellFeature, towardCoord) {
      const ring = scaledRing(shellFeature?.geometry?.coordinates?.[0] || []);
      if (!ring || ring.length < 3 || !towardCoord) return null;
      const origin = ring[0];
      let best = null;
      let bestDistance = Infinity;
      for (let i = 1; i < ring.length - 1; i += 1) {
        const candidate = closestPointOnSegment(towardCoord, ring[i], ring[i + 1]);
        const distance = coordinateDistanceSquared(candidate, towardCoord);
        if (distance < bestDistance) {
          best = candidate;
          bestDistance = distance;
        }
      }
      return best || shellTip(shellFeature) || origin;
    }

    function shellEdgePointToward(cellName, towardCoord) {
      const shellFeature = shellFeatureForCell(cellName);
      if (!shellFeature) return cellCoordinateForName(cellName);
      // Match the old PyDeck map behaviour: ANR/NCell line anchors use the shell front tip,
      // not the site centre and not an extra marker point.
      const tip = shellTip(shellFeature);
      if (tip) return tip;
      return cellCoordinateForName(cellName);
    }

    function shellEdgeLineCoordinates(sourceName, targetName) {
      const sourceCenter = cellCoordinateForName(sourceName);
      const targetCenter = cellCoordinateForName(targetName);
      if (!sourceCenter || !targetCenter) return null;
      return [
        shellEdgePointToward(sourceName, targetCenter),
        shellEdgePointToward(targetName, sourceCenter)
      ];
    }

    function auditRowsForCell(cellName) {
      const key = normalizeCellName(cellName);
      return (anrSummary.auditRows || []).filter(row =>
        normalizeCellName(row.source) === key || normalizeCellName(row.target) === key
      );
    }

    function buildExistingAnrRows(cellName) {
      const key = normalizeCellName(cellName);
      return auditRowsForCell(cellName).map(row => {
        const sourceCoord = cellCoordinateForName(row.source);
        const targetCoord = cellCoordinateForName(row.target);
        const direction = normalizeCellName(row.source) === key ? 'Out' : 'In';
        return {
          source: row.source,
          target: row.target,
          relation: row.relation,
          issue: row.issue,
          direction,
          relationColor: relationColor(row.relation),
          sourceCoord,
          targetCoord,
          drawable: Boolean(sourceCoord && targetCoord),
        };
      });
    }

    function existingAnrVisibleRows() {
      return existingAnrRows.filter(row =>
        row.drawable
        && (ncellRelationFilter === 'all' || row.relation === ncellRelationFilter)
        && cellPassesCarrierFilter(row.source)
        && cellPassesCarrierFilter(row.target)
      );
    }

    function buildExistingAnrLines() {
      return {
        type:'FeatureCollection',
        features: existingAnrVisibleRows()
          .map((row, index) => ({
            type:'Feature',
            geometry:{ type:'LineString', coordinates:shellEdgeLineCoordinates(row.source, row.target) || [row.sourceCoord, row.targetCoord] },
            properties:{
              index,
              source:row.source,
              target:row.target,
              relation:row.relation,
              issue:row.issue,
              direction:row.direction,
              relationColor:row.relationColor,
            }
          }))
      };
    }

    function refreshExistingAnrLayers() {
      if (map?.getSource('existing-anr-lines')) {
        map.getSource('existing-anr-lines').setData(buildExistingAnrLines());
      }
      const visibleRows = existingAnrVisibleRows();
      const visible = ncellVisible && visibleRows.length > 0;
      const focusKey = normalizeCellName(existingAnrFocusCell);
      const visibleNeighborNames = [...new Set(visibleRows
        .map(row => normalizeCellName(row.source) === focusKey ? row.target : row.source)
        .filter(Boolean))];
      setLayerVisibility(['existing-anr-lines', 'existing-anr-hit', 'existing-anr-source-shell-fill', 'existing-anr-neighbor-shells-fill', 'existing-anr-source-shell', 'existing-anr-neighbor-shells'], visible);
      setLayerVisibility(['existing-anr-neighbor-sites'], false);
      const sourceShellFilter = existingAnrFocusCell ? ['match', ['upcase', ['to-string', ['get','CELL_NAME']]], [focusKey], true, false] : emptyCellNameFilter();
      const visibleNeighborKeys = visibleNeighborNames.map(name => normalizeCellName(name));
      const neighborShellFilter = visibleNeighborKeys.length ? ['match', ['upcase', ['to-string', ['get','CELL_NAME']]], visibleNeighborKeys, true, false] : emptyCellNameFilter();
      setFilterSafe('existing-anr-source-shell-fill', sourceShellFilter);
      setFilterSafe('existing-anr-neighbor-shells-fill', neighborShellFilter);
      setFilterSafe('existing-anr-source-shell', sourceShellFilter);
      setFilterSafe('existing-anr-neighbor-shells', neighborShellFilter);
      setFilterSafe('existing-anr-neighbor-sites', emptyCellNameFilter());
      applyNcellRelationFilter();
      updateExistingAnrUi();
    }

    function updateExistingAnrUi() {
      const focusEl = document.getElementById('existingAnrFocus');
      const countEl = document.getElementById('existingAnrCount');
      const listEl = document.getElementById('existingAnrList');
      const visibleRows = existingAnrVisibleRows();
      if (focusEl) focusEl.textContent = existingAnrFocusCell || '-';
      if (countEl) countEl.textContent = visibleRows.length.toLocaleString();
      if (!listEl) return;
      if (!existingAnrFocusCell) {
        listEl.textContent = 'Click a cell to show existing ANR lines.';
        return;
      }
      if (!existingAnrRows.length) {
        listEl.textContent = 'No ANR rows found for this cell.';
        return;
      }
      if (!visibleRows.length) {
        listEl.textContent = 'No drawable ANR lines for this relation filter.';
        return;
      }
      listEl.innerHTML = visibleRows.slice(0, 26).map(row => `
        <div class="link-row">
          <span class="link-target">${row.direction} ${escapeHtml(row.source)} -> ${escapeHtml(row.target)}</span>
          <span class="link-pill ${relationClass(row.relation)}">${escapeHtml(relationShortLabel(row.relation))}</span>
        </div>
      `).join('') + (visibleRows.length > 26 ? `<div class="hint mini-hint">${visibleRows.length - 26} more ANR lines on map.</div>` : '');
    }

    function showExistingAnrForCell(cellName) {
      existingAnrFocusCell = cellName;
      existingAnrRows = buildExistingAnrRows(cellName);
      const focusKey = normalizeCellName(cellName);
      existingAnrNeighborNames = [...new Set(existingAnrRows
        .filter(row => row.drawable)
        .map(row => normalizeCellName(row.source) === focusKey ? row.target : row.source)
        .filter(Boolean))];
      ncellVisible = true;
      const btn = document.getElementById('ncellBtn');
      if (btn) {
        btn.textContent = 'NCell ON';
        btn.classList.add('active');
      }
      refreshExistingAnrLayers();
      raiseShellsAboveHeatmap();
    }

    function clearExistingAnrFocus() {
      existingAnrFocusCell = null;
      existingAnrRows = [];
      existingAnrNeighborNames = [];
      refreshExistingAnrLayers();
    }

    function existingAnrBounds() {
      const coords = [];
      for (const row of existingAnrRows) {
        if (row.sourceCoord) coords.push(row.sourceCoord);
        if (row.targetCoord) coords.push(row.targetCoord);
      }
      return boundsFromCoords(coords);
    }

    function selectedCellGroup() {
      return [sourceCell, ...targets].filter(Boolean);
    }

    function linkRow(sourceName, targetName) {
      const srcFeature = featureForCell(sourceName);
      const tgtFeature = featureForCell(targetName);
      if (!srcFeature || !tgtFeature || sourceName === targetName) return null;
      const relation = selectedRelationType(srcFeature.properties, tgtFeature.properties);
      return {
        source: sourceName,
        target: targetName,
        relation,
        relationColor: relationColor(relation),
        sourceFeature: srcFeature,
        targetFeature: tgtFeature
      };
    }

    function manualLinkRows() {
      if (!sourceCell || targets.length === 0) return [];
      const group = selectedCellGroup();
      if (groupMeshMode) {
        const rows = [];
        for (let i = 0; i < group.length; i += 1) {
          for (let j = i + 1; j < group.length; j += 1) {
            const row = linkRow(group[i], group[j]);
            if (row) rows.push(row);
          }
        }
        return rows;
      }
      return targets.map(targetCell => linkRow(sourceCell, targetCell)).filter(Boolean);
    }

    function buildManualLines() {
      const features = [];
      for (const row of manualLinkRows()) {
        const edgeCoordinates = shellEdgeLineCoordinates(row.source, row.target);
        if (!edgeCoordinates) continue;
        features.push({
          type:'Feature',
          geometry:{ type:'LineString', coordinates:edgeCoordinates },
          properties:{
            source:row.source,
            target:row.target,
            relation:row.relation,
            relationColor:row.relationColor
          }
        });
      }
      return { type:'FeatureCollection', features };
    }

    function updateSelectionUI() {
      document.getElementById('sourceText').textContent = sourceCell || '-';
      const rows = manualLinkRows();
      const group = selectedCellGroup();
      document.getElementById('targetCount').textContent = targets.length;
      document.getElementById('linkCount').textContent = rows.length;
      document.getElementById('linkTypeText').textContent = selectedRelationLabel();
      document.getElementById('csvRowCount').textContent = rows.length * 2;
      document.getElementById('selectedList').innerHTML = rows.length
        ? rows.map(row => `<div class="link-row"><span class="link-target">${groupMeshMode ? row.source + ' <--> ' + row.target : row.target}</span><span class="link-pill ${relationClass(row.relation)}">${relationShortLabel(row.relation)}</span></div>`).join('')
        : 'No selected NCells yet.';
      const meshBtn = document.getElementById('meshBtn');
      if (meshBtn) {
        meshBtn.textContent = groupMeshMode ? 'Group Mesh ON' : 'Group Mesh OFF';
        meshBtn.classList.toggle('active', groupMeshMode);
      }
      const meshHint = document.getElementById('meshHint');
      if (meshHint) {
        meshHint.textContent = groupMeshMode && group.length > 1
          ? `Mesh mode: ${group.length} cells create ${rows.length} visual links and ${rows.length * 2} CSV rows${rows.length > meshLinkSoftLimit ? ' - large export, use carefully.' : '.'}`
          : 'Normal: Cell-A exports to selected targets. Group Mesh: every selected cell exports to every other selected cell.';
      }
      if (map.getSource('manual-ncells')) {
        map.getSource('manual-ncells').setData(buildManualLines());
      }
      if (sourceCell && targets.length) {
        ncellVisible = true;
        setLayerVisibility(['manual-ncell-lines', 'manual-ncell-hit'], true);
        const btn = document.getElementById('ncellBtn');
        btn.textContent = 'NCell ON';
        btn.classList.add('active');
      }
      applyNcellRelationFilter();
      updateAnrUi(sourceCell);
      renderSuggestions();
      setFilterSafe('source-shell-highlight', sourceCell ? ['==', ['get', 'CELL_NAME'], sourceCell] : ['==', ['get', 'CELL_NAME'], '']);
      setFilterSafe('target-shell-highlight', targets.length ? ['match', ['get', 'CELL_NAME'], targets, true, false] : ['==', ['get', 'CELL_NAME'], '']);
      raiseShellsAboveHeatmap();
      document.body.dataset.apSelection = JSON.stringify({ sourceCell, targets, rows: rows.length, csvRows: rows.length * 2, groupMeshMode });
      drawNetworkOverlay();
    }

    function addCell(cellName) {
      if (!sourceCell) {
        sourceCell = cellName;
        suggestRows = [];
        suggestSkippedExisting = 0;
        suggestHasRun = false;
      } else if (cellName !== sourceCell && !targets.includes(cellName)) {
        targets.push(cellName);
      }
      updateSelectionUI();
    }

    function tokenizeWorstCells(text) {
      return [...new Set(String(text || '')
        .split(/[\\s,;]+/)
        .map(value => value.trim())
        .filter(Boolean))];
    }

    function findWorstMatches(tokens) {
      const lookup = new Set(tokens.map(value => value.toUpperCase()));
      return cells.features.filter(feature => {
        const props = feature.properties || {};
        return lookup.has(String(props.CELL_NAME || '').toUpperCase())
          || lookup.has(String(props.SITE_NAME || '').toUpperCase());
      });
    }

    function emptyCellNameFilter() {
      return ['==', ['get','CELL_NAME'], '__none__'];
    }

    function emptyFeatureCollection() {
      return { type:'FeatureCollection', features:[] };
    }

    function areaLineGeojson() {
      if (areaPoints.length < 2) return emptyFeatureCollection();
      const coordinates = areaClosed && areaPoints.length >= 3
        ? [...areaPoints, areaPoints[0]]
        : areaPoints;
      return {
        type:'FeatureCollection',
        features:[{
          type:'Feature',
          geometry:{ type:'LineString', coordinates },
          properties:{ points:areaPoints.length, closed:areaClosed }
        }]
      };
    }

    function areaPolygonGeojson() {
      if (!areaClosed || areaPoints.length < 3) return emptyFeatureCollection();
      return {
        type:'FeatureCollection',
        features:[{
          type:'Feature',
          geometry:{ type:'Polygon', coordinates:[[...areaPoints, areaPoints[0]]] },
          properties:{ points:areaPoints.length }
        }]
      };
    }

    function areaCellNames() {
      return [...new Set(areaSelectedFeatures.map(feature => feature.properties?.CELL_NAME).filter(Boolean))];
    }

    function computeAreaSelection() {
      if (!areaClosed || areaPoints.length < 3 || !map) return [];
      const polygon = areaPoints.map(coordinate => map.project(coordinate));
      return cells.features.filter(feature => {
        if (!feature.geometry || !feature.geometry.coordinates) return false;
        return pointInPolygon(map.project(feature.geometry.coordinates), polygon);
      });
    }

    function areaBounds() {
      const selectedCoords = areaSelectedFeatures.map(feature => feature.geometry.coordinates);
      return boundsFromCoords(selectedCoords.length ? selectedCoords : areaPoints);
    }

    function updateAreaUi() {
      const cellNames = areaCellNames();
      const siteCount = new Set(areaSelectedFeatures.map(feature => feature.properties?.SITE_NAME).filter(Boolean)).size;
      let lteCount = 0;
      let nrCount = 0;
      let otherCount = 0;
      for (const feature of areaSelectedFeatures) {
        const tech = String(feature.properties?.Technology || '').toUpperCase();
        if (tech.includes('LTE')) lteCount += 1;
        else if (tech.includes('NR') || tech.includes('5G')) nrCount += 1;
        else otherCount += 1;
      }
      document.getElementById('areaPointCount').textContent = areaPoints.length;
      document.getElementById('areaCellCount').textContent = cellNames.length;
      document.getElementById('areaSiteCount').textContent = siteCount;
      document.getElementById('areaTechText').textContent = areaSelectedFeatures.length ? `LTE ${lteCount} | NR ${nrCount} | O ${otherCount}` : '-';
      document.getElementById('areaList').textContent = areaClosed
        ? (cellNames.length ? cellNames.slice(0, 18).join(', ') + (cellNames.length > 18 ? ', ...' : '') : 'No cells inside area.')
        : (areaPoints.length ? `${areaPoints.length} area points placed.` : 'No area selected.');
    }

    function refreshAreaSelection() {
      areaSelectedFeatures = computeAreaSelection();
      const cellNames = areaCellNames();
      if (map?.getSource('area-select-polygon')) map.getSource('area-select-polygon').setData(areaPolygonGeojson());
      if (map?.getSource('area-select-line')) map.getSource('area-select-line').setData(areaLineGeojson());
      setFilterSafe('area-selected-sites', cellNames.length ? ['match', ['get','CELL_NAME'], cellNames, true, false] : emptyCellNameFilter());
      updateAreaUi();
      document.body.dataset.apAreaSelection = JSON.stringify({
        points: areaPoints.length,
        closed: areaClosed,
        cells: cellNames.length,
        sites: new Set(areaSelectedFeatures.map(feature => feature.properties?.SITE_NAME).filter(Boolean)).size
      });
      drawNetworkOverlay();
    }

    function addAreaPoint(lngLat) {
      if (!areaMode || !lngLat) return;
      areaPoints.push([Number(lngLat.lng), Number(lngLat.lat)]);
      areaClosed = false;
      refreshAreaSelection();
    }

    function closeAreaSelection() {
      if (areaPoints.length < 3) return;
      areaClosed = true;
      refreshAreaSelection();
    }

    function undoAreaPoint() {
      if (!areaPoints.length) return;
      areaPoints.pop();
      if (areaPoints.length < 3) areaClosed = false;
      refreshAreaSelection();
    }

    function clearAreaSelection() {
      areaPoints = [];
      areaClosed = false;
      areaSelectedFeatures = [];
      refreshAreaSelection();
    }

    function fitAreaSelection() {
      const bounds = areaBounds();
      if (bounds) fitBoundsSmart(bounds, 15.5);
    }

    function downloadAreaCsv() {
      if (!areaSelectedFeatures.length) return;
      const columns = ['SITE_NAME','CELL_NAME','LATITUDE','LONGITUDE','Technology','CARRIER','VENDOR','CLUSTER_AREA','TAC','PCI'];
      let csv = `${columns.join(',')}\\n`;
      for (const feature of areaSelectedFeatures) {
        const props = feature.properties || {};
        csv += `${columns.map(column => escapeCsv(props[column])).join(',')}\\n`;
      }
      const blob = new Blob([csv], { type:'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'automationpark_maplibre_area_cells.csv';
      link.click();
      URL.revokeObjectURL(link.href);
    }

    function worstNameFilter() {
      return worstMatchedNames.length
        ? ['in', ['get','CELL_NAME'], ['literal', worstMatchedNames]]
        : emptyCellNameFilter();
    }

    function refreshWorstLayers() {
      const filter = worstNameFilter();
      if (map.getLayer('worst-shell-highlight')) map.setFilter('worst-shell-highlight', filter);
      if (map.getLayer('worst-site-highlight')) map.setFilter('worst-site-highlight', filter);
      drawNetworkOverlay();
    }

    function updateWorstUi() {
      document.getElementById('worstLoaded').textContent = worstTokens.length;
      document.getElementById('worstMatched').textContent = worstMatchedNames.length;
      document.getElementById('worstList').textContent = worstMatchedNames.length
        ? worstMatchedNames.slice(0, 18).join(', ') + (worstMatchedNames.length > 18 ? ', ...' : '')
        : (worstTokens.length ? 'No matching cells found.' : 'No worst cells loaded.');
    }

    function loadWorstCells() {
      worstTokens = tokenizeWorstCells(document.getElementById('worstInput').value);
      worstMatchedFeatures = findWorstMatches(worstTokens);
      worstMatchedNames = [...new Set(worstMatchedFeatures.map(feature => feature.properties.CELL_NAME).filter(Boolean))];
      refreshWorstLayers();
      updateWorstUi();
    }

    function clearWorstCells() {
      worstTokens = [];
      worstMatchedFeatures = [];
      worstMatchedNames = [];
      document.getElementById('worstInput').value = '';
      refreshWorstLayers();
      updateWorstUi();
    }

    function worstBounds() {
      const coords = worstMatchedFeatures.map(feature => feature.geometry.coordinates);
      return boundsFromCoords(coords);
    }

    function downloadWorstCsv() {
      if (!worstMatchedFeatures.length) return;
      const columns = ['SITE_NAME','CELL_NAME','LATITUDE','LONGITUDE','Technology','CARRIER','VENDOR','CLUSTER_AREA','TAC','PCI'];
      let csv = `${columns.join(',')}\\n`;
      for (const feature of worstMatchedFeatures) {
        const props = feature.properties || {};
        csv += `${columns.map(column => escapeCsv(props[column])).join(',')}\\n`;
      }
      const blob = new Blob([csv], { type:'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'automationpark_maplibre_worst_cells.csv';
      link.click();
      URL.revokeObjectURL(link.href);
    }

    function auditCsv() {
      const columns = ['source','target','relation','issue','isOneWay','isMissingTarget','isDuplicate','duplicateCount'];
      const rows = auditRowsForMode();
      let csv = `${columns.join(',')}\\n`;
      for (const row of rows) {
        csv += `${columns.map(column => escapeCsv(row[column])).join(',')}\\n`;
      }
      return csv;
    }

    function downloadAuditCsv() {
      const csv = auditCsv();
      if (!csv) return;
      const blob = new Blob([csv], { type:'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = sourceCell && auditSelectedOnly
        ? `automationpark_anr_audit_${sourceCell}.csv`
        : 'automationpark_anr_audit.csv';
      link.click();
      URL.revokeObjectURL(link.href);
    }

    function ncellCsv() {
      const rows = manualLinkRows();
      if (!rows.length) return '';
      let csv = 'Src_Cell,Targ_Cell,Ncell_Type\\n';
      for (const row of rows) {
        csv += `${escapeCsv(row.source)},${escapeCsv(row.target)},${escapeCsv(row.relation)}\\n${escapeCsv(row.target)},${escapeCsv(row.source)},${escapeCsv(row.relation)}\\n`;
      }
      return csv;
    }

    function downloadCsv() {
      const csv = ncellCsv();
      if (!csv) return;
      const blob = new Blob([csv], { type:'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'automationpark_maplibre_visual_ncells.csv';
      link.click();
      URL.revokeObjectURL(link.href);
    }

    async function copyCsv() {
      const csv = ncellCsv();
      if (!csv) return;
      try {
        await navigator.clipboard.writeText(csv);
        document.getElementById('selectedList').insertAdjacentHTML('afterbegin', '<div class="link-row"><span class="link-target">CSV copied to clipboard</span><span class="link-pill">OK</span></div>');
      } catch (err) {
        downloadCsv();
      }
    }

    function dataBounds() {
      const coords = cells.features
        .map(f => f.geometry.coordinates)
        .filter(([lon, lat]) => Number.isFinite(lon) && Number.isFinite(lat));
      if (!coords.length) return null;
      const median = values => {
        const sorted = [...values].sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
      };
      const medianLon = median(coords.map(([lon]) => lon));
      const medianLat = median(coords.map(([, lat]) => lat));
      const coreCoords = coords.filter(([lon, lat]) => Math.abs(lon - medianLon) <= 3 && Math.abs(lat - medianLat) <= 3);
      const boundedCoords = coreCoords.length >= Math.max(10, coords.length * 0.8) ? coreCoords : coords;
      return boundsFromCoords(boundedCoords);
    }

    function dtBounds() {
      const coords = dtPoints.features.map(f => f.geometry.coordinates);
      return boundsFromCoords(coords);
    }

    function atollBounds() {
      if (!atollOverlay.available || !atollOverlay.coordinates) return null;
      return boundsFromCoords(atollOverlay.coordinates);
    }

    function mergeBounds(boundsList) {
      const valid = boundsList.filter(Boolean);
      if (!valid.length) return null;
      let minLon = valid[0][0][0], minLat = valid[0][0][1], maxLon = valid[0][1][0], maxLat = valid[0][1][1];
      for (const bounds of valid) {
        minLon = Math.min(minLon, bounds[0][0]);
        minLat = Math.min(minLat, bounds[0][1]);
        maxLon = Math.max(maxLon, bounds[1][0]);
        maxLat = Math.max(maxLat, bounds[1][1]);
      }
      return [[minLon, minLat], [maxLon, maxLat]];
    }

    function fitBoundsSmart(bounds, maxZoom = 14.8) {
      if (!bounds) return;
      map.fitBounds(bounds, { padding: { top: 84, bottom: 76, left: 430, right: 58 }, maxZoom, duration: 450 });
    }

    function boundsFromCoords(coords) {
      if (!coords.length) return null;
      let minLon = coords[0][0], maxLon = coords[0][0], minLat = coords[0][1], maxLat = coords[0][1];
      for (const [lon, lat] of coords) {
        minLon = Math.min(minLon, lon);
        maxLon = Math.max(maxLon, lon);
        minLat = Math.min(minLat, lat);
        maxLat = Math.max(maxLat, lat);
      }
      return [[minLon, minLat], [maxLon, maxLat]];
    }

    const map = new maplibregl.Map({
      container: 'map',
      style: {
        version: 8,
        glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
        sources: {
          osm: {
            type: 'raster',
            tiles: [
              'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors'
          }
        },
        layers: [
          {
            id: 'automationpark-bg',
            type: 'background',
            paint: { 'background-color': '#050A12' }
          },
          {
            id: 'osm-muted',
            type: 'raster',
            source: 'osm',
            paint: {
              'raster-opacity': 0.26,
              'raster-saturation': -0.85,
              'raster-contrast': 0.18,
              'raster-brightness-min': 0.08,
              'raster-brightness-max': 0.72
            }
          }
        ]
      },
      center: startCenter,
      zoom: 10.4,
      attributionControl: true
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

    let mapLayersReady = false;
    let canvasOverlayReady = false;
    let mapLayerSetupAttempts = 0;

    function setupCanvasOverlay() {
      if (canvasOverlayReady) return;
      canvasOverlayReady = true;
      try {
        const bounds = dataBounds();
        if (bounds) {
          map.fitBounds(bounds, { padding: { top: 70, bottom: 70, left: 430, right: 70 }, maxZoom: 11.5, duration: 0 });
        }
        drawNetworkOverlay();
        map.on('move', drawNetworkOverlay);
        map.on('zoom', drawNetworkOverlay);
        map.on('resize', drawNetworkOverlay);
        window.addEventListener('resize', drawNetworkOverlay);
        renderLegend();
        updateCompareStrip();
        document.body.dataset.apCanvasOverlay = 'ready';
      } catch (err) {
        canvasOverlayReady = false;
        document.body.dataset.apCanvasError = err && err.stack ? err.stack : String(err);
      }
    }

    function setupMapLayers() {
      if (mapLayersReady) return;
      mapLayersReady = true;
      mapLayerSetupAttempts += 1;
      try {
        document.getElementById('cellCount').textContent = cells.features.length;
        document.getElementById('dtCount').textContent = dtPoints.features.length;
        updateAnrUi();
        updateAuditUi();
        renderSuggestions();
        updateExistingAnrUi();
        document.getElementById('dtColorMode').value = dtColorMode;
        document.getElementById('atollSize').textContent = atollOverlay.available ? `${atollOverlay.width} x ${atollOverlay.height}` : '-';
        syncTrafficCoverageButtons();
        if (!atollOverlay.available) {
          document.getElementById('atollOpacity').disabled = true;
        }
        map.addSource('shells', { type:'geojson', data:scaledShellsGeojson(), generateId:true });
        map.addSource('cells', { type:'geojson', data:cells, generateId:true });
        map.addSource('dt-points', { type:'geojson', data:dtPoints, generateId:true });
        map.addSource('manual-ncells', { type:'geojson', data:buildManualLines() });
        map.addSource('existing-anr-lines', { type:'geojson', data:buildExistingAnrLines() });
        map.addSource('dt-candidate-lines', { type:'geojson', data:nearestCandidateLines() });
        map.addSource('area-select-polygon', { type:'geojson', data:areaPolygonGeojson() });
        map.addSource('area-select-line', { type:'geojson', data:areaLineGeojson() });

        if (atollOverlay.available) {
          map.addSource('atoll-raster', {
            type: 'image',
            url: atollOverlay.url,
            coordinates: atollOverlay.coordinates
          });
          map.addLayer({
            id: 'atoll-raster-layer',
            type: 'raster',
            source: 'atoll-raster',
            layout: { visibility: 'none' },
            paint: {
              'raster-opacity': 0.62,
              'raster-fade-duration': 0
            }
          });
        }

      map.addLayer({
        id:'rf-shell-fill',
        type:'fill',
        source:'shells',
        layout:{ visibility:'visible' },
        paint:{
          'fill-color':'#22d3ee',
          'fill-opacity':['interpolate',['linear'],['zoom'],8,0.48,13,0.42,16,0.36]
        }
      });
      map.addLayer({
        id:'rf-shell-outline',
        type:'line',
        source:'shells',
        layout:{ visibility:'visible' },
        paint:{
          'line-color':'#67e8f9',
          'line-opacity':0.92,
          'line-width':['interpolate',['linear'],['zoom'],8,0.9,13,1.15,16,1.45]
        }
      });
      map.addLayer({
        id:'target-shell-highlight',
        type:'fill',
        source:'shells',
        paint:{ 'fill-color':'#f59e0b', 'fill-opacity':0.58 },
        filter:['==', ['get','CELL_NAME'], '']
      });
      map.addLayer({
        id:'source-shell-highlight',
        type:'fill',
        source:'shells',
        paint:{ 'fill-color':'#ef4444', 'fill-opacity':0.72 },
        filter:['==', ['get','CELL_NAME'], '']
      });
      map.addLayer({
        id:'area-select-fill',
        type:'fill',
        source:'area-select-polygon',
        paint:{
          'fill-color':'#14b8a6',
          'fill-opacity':0.18
        }
      });
      map.addLayer({
        id:'area-select-outline',
        type:'line',
        source:'area-select-line',
        paint:{
          'line-color':'#5eead4',
          'line-width':['interpolate',['linear'],['zoom'],8,2.2,13,3.2,16,4.6],
          'line-opacity':0.98,
          'line-dasharray':[1.2, 0.8]
        }
      });
      map.addLayer({
        id:'worst-shell-highlight',
        type:'fill',
        source:'shells',
        paint:{ 'fill-color':'#ef4444', 'fill-opacity':0.58 },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'manual-ncell-lines',
        type:'line',
        source:'manual-ncells',
        paint:{
          'line-color':['get','relationColor'],
          'line-width':['interpolate',['linear'],['zoom'],8,1.15,13,1.65,16,2.25],
          'line-opacity':0.98
        }
      });
      map.addLayer({
        id:'manual-ncell-hit',
        type:'line',
        source:'manual-ncells',
        paint:{
          'line-color':'#ffffff',
          'line-width':['interpolate',['linear'],['zoom'],8,14,13,18,16,24],
          'line-opacity':0.01
        }
      });
      map.addLayer({
        id:'existing-anr-lines',
        type:'line',
        source:'existing-anr-lines',
        layout:{ visibility:'none' },
        paint:{
          'line-color':['get','relationColor'],
          'line-width':['interpolate',['linear'],['zoom'],8,0.75,13,1.05,16,1.45],
          'line-opacity':0.90
        }
      });
      map.addLayer({
        id:'existing-anr-hit',
        type:'line',
        source:'existing-anr-lines',
        layout:{ visibility:'none' },
        paint:{
          'line-color':'#ffffff',
          'line-width':['interpolate',['linear'],['zoom'],8,16,13,22,16,28],
          'line-opacity':0.01
        }
      });
      map.addLayer({
        id:'site-dots',
        type:'circle',
        source:'cells',
        paint:{
          'circle-radius':['interpolate',['linear'],['zoom'],8,8,13,11,16,14],
          'circle-color':'#f59e0b',
          'circle-opacity':1,
          'circle-stroke-color':'#e0f2fe',
          'circle-stroke-width':['interpolate',['linear'],['zoom'],8,1.5,13,2.2,16,3]
        }
      });
      map.addLayer({
        id:'existing-anr-source-shell-fill',
        type:'fill',
        source:'shells',
        layout:{ visibility:'none' },
        paint:{
          'fill-color':'#facc15',
          'fill-opacity':0.34
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'existing-anr-neighbor-shells-fill',
        type:'fill',
        source:'shells',
        layout:{ visibility:'none' },
        paint:{
          'fill-color':'#facc15',
          'fill-opacity':0.50
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'existing-anr-source-shell',
        type:'line',
        source:'shells',
        layout:{ visibility:'none' },
        paint:{
          'line-color':'#facc15',
          'line-opacity':1,
          'line-width':['interpolate',['linear'],['zoom'],8,2.4,13,3.8,16,5.2]
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'existing-anr-neighbor-shells',
        type:'line',
        source:'shells',
        layout:{ visibility:'none' },
        paint:{
          'line-color':'#facc15',
          'line-opacity':1,
          'line-width':['interpolate',['linear'],['zoom'],8,2.8,13,4.2,16,5.8]
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'existing-anr-neighbor-sites',
        type:'circle',
        source:'cells',
        layout:{ visibility:'none' },
        paint:{
          'circle-radius':0,
          'circle-color':'rgba(0,0,0,0)',
          'circle-stroke-color':'rgba(0,0,0,0)',
          'circle-stroke-width':0,
          'circle-opacity':0
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'worst-site-highlight',
        type:'circle',
        source:'cells',
        paint:{
          'circle-radius':['interpolate',['linear'],['zoom'],8,10,13,17,16,24],
          'circle-color':'rgba(239,68,68,0.24)',
          'circle-stroke-color':'#ff2d2d',
          'circle-stroke-width':3.2,
          'circle-opacity':0.98
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'area-selected-sites',
        type:'circle',
        source:'cells',
        paint:{
          'circle-radius':['interpolate',['linear'],['zoom'],8,9,13,15,16,22],
          'circle-color':'rgba(20,184,166,0.28)',
          'circle-stroke-color':'#5eead4',
          'circle-stroke-width':3,
          'circle-opacity':0.98
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      refreshSiteMarkerStyle(false);
      map.addLayer({
        id:'cell-labels',
        type:'symbol',
        source:'cells',
        layout:{
          visibility:'none',
          'text-field':['get','CELL_NAME'],
          'text-size':['interpolate',['linear'],['zoom'],10,9,14,12],
          'text-offset':[0,1.15],
          'text-anchor':'top',
          'text-allow-overlap':false
        },
        paint:{
          'text-color':'#e0f2fe',
          'text-halo-color':'#020617',
          'text-halo-width':1.4
        }
      });
      map.addLayer({
        id:'pci-shell-match',
        type:'fill',
        source:'shells',
        paint:{
          'fill-color':'#f0abfc',
          'fill-opacity':0.38
        },
        filter:['==', ['get','PCI'], '__none__']
      });
      map.addLayer({
        id:'pci-site-match',
        type:'circle',
        source:'cells',
        paint:{
          'circle-radius':['interpolate',['linear'],['zoom'],8,7,13,13,16,19],
          'circle-color':'rgba(236,72,153,0.2)',
          'circle-stroke-color':'#f0abfc',
          'circle-stroke-width':3,
          'circle-opacity':0.98
        },
        filter:['==', ['get','PCI'], '__none__']
      });
      map.addLayer({
        id:'nearest-shell-candidates',
        type:'line',
        source:'shells',
        paint:{
          'line-color':'#22d3ee',
          'line-opacity':0.96,
          'line-width':['interpolate',['linear'],['zoom'],8,2.4,13,4.2,16,6]
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'nearest-site-candidates',
        type:'circle',
        source:'cells',
        paint:{
          'circle-radius':['interpolate',['linear'],['zoom'],8,8,13,15,16,22],
          'circle-color':'rgba(34,211,238,0.16)',
          'circle-stroke-color':'#22d3ee',
          'circle-stroke-width':3,
          'circle-opacity':0.98
        },
        filter:['==', ['get','CELL_NAME'], '__none__']
      });
      map.addLayer({
        id:'dt-candidate-lines',
        type:'line',
        source:'dt-candidate-lines',
        paint:{
          'line-color':'#22d3ee',
          'line-opacity':0.72,
          'line-width':['interpolate',['linear'],['zoom'],8,1.2,13,2.8,16,4],
          'line-dasharray':[1.2, 0.8]
        }
      });
      map.addLayer({
        id:'dt-heatmap',
        type:'heatmap',
        source:'dt-points',
        layout:{ visibility: 'none' },
        paint:{
          'heatmap-weight':['interpolate', ['linear'], ['get','kpiWeight'], 0, 0.12, 1, 1],
          'heatmap-intensity':dtHeatmapIntensityExpression(),
          'heatmap-radius':dtHeatmapRadiusExpression(),
          'heatmap-opacity':dtHeatmapOpacityExpression(),
          'heatmap-color':dtHeatmapColorRamp()
        }
      });
      setLayerVisibility(['dt-heatmap'], false);
      map.addLayer({
        id:'dt-points',
        type:'circle',
        source:'dt-points',
        layout:{ visibility: 'none' },
        paint:{
          'circle-radius':['interpolate',['linear'],['zoom'],8,3.0,13,6.5,16,9],
          'circle-color':['get','kpiColor'],
          'circle-opacity':0.86,
          'circle-stroke-color':'#020617',
          'circle-stroke-width':1.2
        }
      });
      map.addLayer({
        id:'dt-selected-ring',
        type:'circle',
        source:'dt-points',
        paint:{
          'circle-radius':['interpolate',['linear'],['zoom'],8,8,13,14,16,20],
          'circle-color':'rgba(0,0,0,0)',
          'circle-stroke-color':'#ffffff',
          'circle-stroke-width':3,
          'circle-opacity':0.98
        },
        filter:['==', ['get','index'], -1]
      });
      applyDtColorMode();
      applyCarrierFilter();
      setLayerVisibility(['site-dots'], dotsVisible);
      setLayerVisibility(['cell-labels'], labelsVisible);
      setLayerVisibility(['manual-ncell-lines', 'manual-ncell-hit', 'existing-anr-lines', 'existing-anr-hit', 'existing-anr-source-shell-fill', 'existing-anr-neighbor-shells-fill', 'existing-anr-source-shell', 'existing-anr-neighbor-shells', 'existing-anr-neighbor-sites'], ncellVisible);
      document.getElementById('dotsBtn').textContent = dotsVisible ? 'Site Marker ON' : 'Site Marker OFF';
      document.getElementById('dotsBtn').classList.toggle('active', dotsVisible);
      document.getElementById('ncellBtn').textContent = ncellVisible ? 'NCell ON' : 'NCell OFF';
      document.getElementById('ncellBtn').classList.toggle('active', ncellVisible);
      document.getElementById('carrierAllBtn').classList.toggle('active', carrierFilter === 'all');
      document.getElementById('carrierL07Btn').classList.toggle('active', carrierFilter === 'L07');
      document.getElementById('carrierL18Btn').classList.toggle('active', carrierFilter === 'L18');
      document.getElementById('carrierL21Btn').classList.toggle('active', carrierFilter === 'L2100');
      document.getElementById('carrierL23Btn').classList.toggle('active', carrierFilter === 'L2300');
      document.getElementById('carrierNR26Btn').classList.toggle('active', carrierFilter === 'NR2600');
      document.getElementById('carrierNR900Btn').classList.toggle('active', carrierFilter === 'NR900');
      document.getElementById('carrierN35Btn').classList.toggle('active', carrierFilter === 'N35');
      document.getElementById('carrierF1Btn').classList.toggle('active', carrierFilter === 'F1');
      document.getElementById('carrierF2Btn').classList.toggle('active', carrierFilter === 'F2');
      document.getElementById('carrierF3Btn').classList.toggle('active', carrierFilter === 'F3');
      document.getElementById('carrierF4Btn').classList.toggle('active', carrierFilter === 'F4');
      raiseShellsAboveHeatmap();

      const bounds = dataBounds();
      if (bounds) {
        map.fitBounds(bounds, { padding: { top: 70, bottom: 70, left: 430, right: 70 }, maxZoom: 11.5, duration: 0 });
      }
      drawNetworkOverlay();
      map.on('move', drawNetworkOverlay);
      map.on('zoom', drawNetworkOverlay);
      map.on('resize', drawNetworkOverlay);
      window.addEventListener('resize', drawNetworkOverlay);
      renderLegend();

      map.on('mouseenter', 'rf-shell-fill', clickableCursor);
      map.on('mouseleave', 'rf-shell-fill', restoreCursor);
      map.on('click', 'rf-shell-fill', (e) => {
        if (areaMode) return;
        openCellFromMapClick(e.features[0], e.lngLat);
      });
      map.on('click', 'rf-shell-outline', (e) => {
        if (areaMode) return;
        openCellFromMapClick(e.features[0], e.lngLat);
      });
      map.on('mouseenter', 'site-dots', clickableCursor);
      map.on('mouseleave', 'site-dots', restoreCursor);
      map.on('click', 'site-dots', (e) => {
        if (areaMode) return;
        openCellFromMapClick(e.features[0], e.lngLat);
      });
      map.on('click', (e) => {
        if (Date.now() - lastCellOpenAt < 120) return;
        if (areaMode) {
          addAreaPoint(e.lngLat);
          return;
        }
        if (map.getLayer('manual-ncell-hit') || map.getLayer('existing-anr-hit')) {
          const lineLayers = ['manual-ncell-hit', 'manual-ncell-lines', 'existing-anr-hit', 'existing-anr-lines'].filter(layerId => map.getLayer(layerId));
          const lineHits = map.queryRenderedFeatures(e.point, { layers:lineLayers });
          if (lineHits.length) return;
        }
        const hit = nearestOverlayFeature(e.point);
        if (!hit) return;
        openCellFromMapClick(hit, e.lngLat);
      });
      map.on('mouseenter', 'dt-points', clickableCursor);
      map.on('mouseleave', 'dt-points', restoreCursor);
      map.on('click', 'dt-points', (e) => {
        const props = e.features[0].properties;
        const point = e.features[0].geometry.coordinates;
        selectedDtSample = props;
        selectedDtPoint = point;
        selectedNearestCells = nearestCellsToPoint(point, 5);
        selectedNearestCellNames = selectedNearestCells.map(item => item.cell);
        map.setFilter('dt-selected-ring', ['==', ['get','index'], Number(props.index)]);
        applySelectedPciMatch();
        applyNearestCellHighlight();
        updateCompareStrip();
        new maplibregl.Popup({ closeButton:true, maxWidth:'320px' })
          .setLngLat(e.lngLat)
          .setHTML(dtPopup(props))
          .addTo(map);
      });
      function openNcellLinePopup(e) {
        const p = e.features[0].properties;
        new maplibregl.Popup({ closeButton:true, maxWidth:'390px' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="ap-popup-title">${escapeHtml(p.source)} &lt;--&gt; ${escapeHtml(p.target)}</div>
            <div class="ap-popup-row"><b>${escapeHtml(p.relation)}</b> NCell</div>
            ${terrainLosPopupHtml(p.source, p.target, p.relation)}
          `)
          .addTo(map);
      }
      function openExistingAnrLinePopup(e) {
        const p = e.features[0].properties;
        new maplibregl.Popup({ closeButton:true, maxWidth:'390px' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="ap-popup-title">Existing ANR NCell</div>
            <div class="ap-popup-row"><b>Source:</b> ${escapeHtml(p.source || '-')}</div>
            <div class="ap-popup-row"><b>Target:</b> ${escapeHtml(p.target || '-')}</div>
            <div class="ap-popup-row"><b>Type:</b> ${escapeHtml(p.relation || '-')}</div>
            <div class="ap-popup-row"><b>Direction:</b> ${escapeHtml(p.direction || '-')} relative to ${escapeHtml(existingAnrFocusCell || '-')}</div>
            <div class="ap-popup-row"><b>Audit:</b> ${escapeHtml(p.issue || 'OK')}</div>
            ${terrainLosPopupHtml(p.source, p.target, p.relation)}
          `)
          .addTo(map);
      }
      map.on('click', 'manual-ncell-lines', openNcellLinePopup);
      map.on('click', 'manual-ncell-hit', openNcellLinePopup);
      map.on('click', 'existing-anr-hit', openExistingAnrLinePopup);
      map.on('mouseenter', 'manual-ncell-hit', clickableCursor);
      map.on('mouseleave', 'manual-ncell-hit', restoreCursor);
      map.on('mouseenter', 'existing-anr-hit', clickableCursor);
      map.on('mouseleave', 'existing-anr-hit', restoreCursor);
      mapLayersReady = true;
      function writeLayerDebug() {
        const visibleDots = map.getLayer('site-dots') ? map.queryRenderedFeatures({ layers:['site-dots'] }).length : -1;
        const visibleShells = map.getLayer('rf-shell-fill') ? map.queryRenderedFeatures({ layers:['rf-shell-fill'] }).length : -1;
        const visibleDt = map.getLayer('dt-points') ? map.queryRenderedFeatures({ layers:['dt-points'] }).length : -1;
        document.body.dataset.apLayerDebug = JSON.stringify({
          dots: !!map.getLayer('site-dots'),
          shells: !!map.getLayer('rf-shell-fill'),
          dt: !!map.getLayer('dt-points'),
          dotVisibility: map.getLayer('site-dots') ? map.getLayoutProperty('site-dots', 'visibility') || 'visible' : 'missing',
          shellVisibility: map.getLayer('rf-shell-fill') ? map.getLayoutProperty('rf-shell-fill', 'visibility') || 'visible' : 'missing',
          dtVisibility: map.getLayer('dt-points') ? map.getLayoutProperty('dt-points', 'visibility') || 'visible' : 'missing',
          dotFilter: map.getLayer('site-dots') ? map.getFilter('site-dots') : null,
          shellFilter: map.getLayer('rf-shell-fill') ? map.getFilter('rf-shell-fill') : null,
          sourceCells: map.getSource('cells')?._data?.features?.length ?? null,
          sourceShells: map.getSource('shells')?._data?.features?.length ?? null,
          sourceDt: map.getSource('dt-points')?._data?.features?.length ?? null,
          visibleDots,
          visibleShells,
          visibleDt,
          center: map.getCenter().toArray(),
          bounds: map.getBounds().toArray(),
          zoom: map.getZoom(),
          firstCell: cells.features[0]?.geometry?.coordinates || null,
          sampleCells: cells.features.slice(0, 5).map(f => f.geometry.coordinates),
          cells: cells.features.length,
          shellsCount: shells.features.length
        });
      }
      writeLayerDebug();
      map.once('idle', writeLayerDebug);
      setTimeout(writeLayerDebug, 2500);
      updateCompareStrip();
      } catch (err) {
        mapLayersReady = false;
        document.body.dataset.apLayerError = err && err.stack ? err.stack : String(err);
        if (String(err).includes('Style is not done loading')) {
          setupCanvasOverlay();
        }
        if (mapLayerSetupAttempts < 30) {
          setTimeout(setupMapLayers, 350);
        } else {
          console.error('MapLibre layer setup failed', err);
        }
      }
    }

    map.on('load', setupMapLayers);
    map.on('style.load', setupMapLayers);
    setTimeout(setupMapLayers, 1200);

    document.getElementById('selectBtn').onclick = () => {
      selectionMode = !selectionMode;
      const btn = document.getElementById('selectBtn');
      btn.textContent = selectionMode ? 'Selection ON' : 'Selection OFF';
      btn.classList.toggle('active', selectionMode);
      if (selectionMode) {
        pointerMode = 'select';
        applyPointerMode();
      }
    };
    document.getElementById('pointerSelectBtn').onclick = () => {
      pointerMode = 'select';
      applyPointerMode();
    };
    document.getElementById('pointerHandBtn').onclick = () => {
      pointerMode = 'pan';
      applyPointerMode();
    };
    document.getElementById('shellsBtn').onclick = () => {
      shellsVisible = !shellsVisible;
      const visibility = shellsVisible ? 'visible' : 'none';
      map.setLayoutProperty('rf-shell-fill', 'visibility', visibility);
      map.setLayoutProperty('rf-shell-outline', 'visibility', visibility);
      const btn = document.getElementById('shellsBtn');
      btn.textContent = shellsVisible ? 'Shells ON' : 'Shells OFF';
      btn.classList.toggle('active', shellsVisible);
      drawNetworkOverlay();
    };
    document.getElementById('dotsBtn').onclick = () => {
      dotsVisible = !dotsVisible;
      setLayerVisibility(['site-dots'], dotsVisible);
      const btn = document.getElementById('dotsBtn');
      btn.textContent = dotsVisible ? 'Site Marker ON' : 'Site Marker OFF';
      btn.classList.toggle('active', dotsVisible);
      drawNetworkOverlay();
    };
    document.getElementById('labelsBtn').onclick = () => {
      labelsVisible = !labelsVisible;
      applyLabelMode();
      const btn = document.getElementById('labelsBtn');
      btn.textContent = labelsVisible ? 'Labels ON' : 'Labels OFF';
      btn.classList.toggle('active', labelsVisible);
    };
    document.getElementById('ncellBtn').onclick = () => {
      ncellVisible = !ncellVisible;
      setLayerVisibility(['manual-ncell-lines', 'manual-ncell-hit', 'existing-anr-lines', 'existing-anr-hit', 'existing-anr-source-shell-fill', 'existing-anr-neighbor-shells-fill', 'existing-anr-source-shell', 'existing-anr-neighbor-shells', 'existing-anr-neighbor-sites'], ncellVisible);
      const btn = document.getElementById('ncellBtn');
      btn.textContent = ncellVisible ? 'NCell ON' : 'NCell OFF';
      btn.classList.toggle('active', ncellVisible);
      drawNetworkOverlay();
    };
    document.getElementById('popupBtn').onclick = () => {
      popupsVisible = !popupsVisible;
      const btn = document.getElementById('popupBtn');
      btn.textContent = popupsVisible ? 'Info ON' : 'Info OFF';
      btn.classList.toggle('active', popupsVisible);
      if (!popupsVisible) {
        document.querySelectorAll('.maplibregl-popup').forEach(popup => popup.remove());
      }
    };
    document.getElementById('shellSize').oninput = (event) => {
      shellScale = Number(event.target.value) / 100;
      document.getElementById('shellSizeText').textContent = `Shell radius: ${event.target.value}%`;
      refreshShellGeometry();
    };
    document.getElementById('shellWidth').oninput = (event) => {
      shellWidthScale = Number(event.target.value) / 100;
      document.getElementById('shellWidthText').textContent = `Shell width: ${event.target.value}%`;
      refreshShellGeometry();
    };
    document.getElementById('siteMarkerSize').oninput = (event) => {
      siteMarkerScale = Number(event.target.value) / 100;
      document.getElementById('siteMarkerSizeText').textContent = `Site marker: ${event.target.value}%`;
      refreshSiteMarkerStyle();
    };
    document.getElementById('labelMode').onchange = (event) => {
      labelMode = event.target.value;
      applyLabelMode();
    };
    document.getElementById('dtBtn').onclick = () => {
      if (!dtPoints.features.length) return;
      dtVisible = !dtVisible;
      applyDtViewMode();
      raiseShellsAboveHeatmap();
      syncTrafficCoverageButtons();
      updateCompareStrip();
      renderLegend();
    };
    document.getElementById('dtFitBtn').onclick = () => {
      fitBoundsSmart(dtBounds(), 15.5);
    };
    document.getElementById('dtColorMode').onchange = (event) => {
      dtColorMode = event.target.value;
      applyDtColorMode();
      syncTrafficCoverageButtons();
      updateCompareStrip();
    };
    document.getElementById('dtViewMode').onchange = (event) => {
      dtViewMode = event.target.value;
      applyDtViewMode();
      updateCompareStrip();
      renderLegend();
    };
    document.getElementById('heatRadius').oninput = (event) => {
      heatRadiusScale = Number(event.target.value);
      document.getElementById('heatRadiusValue').textContent = `${event.target.value}px`;
      applyDtHeatTuning();
    };
    document.getElementById('heatIntensity').oninput = (event) => {
      heatIntensityScale = Number(event.target.value);
      document.getElementById('heatIntensityValue').textContent = `${Number(event.target.value).toFixed(1)}x`;
      applyDtHeatTuning();
    };
    document.getElementById('heatOpacity').oninput = (event) => {
      heatOpacityScale = Number(event.target.value) / 100;
      document.getElementById('heatOpacityValue').textContent = `${event.target.value}%`;
      applyDtHeatTuning();
    };
    document.getElementById('atollBtn').onclick = () => {
      if (!coverageLayerAvailable()) return;
      const nextVisible = !coverageActive();
      if (hasMeasuredCoverageLayer) {
        dtVisible = nextVisible;
        if (dtVisible && dtColorMode === 'kpiColor') {
          dtColorMode = 'rsrpColor';
          document.getElementById('dtColorMode').value = dtColorMode;
          applyDtColorMode();
        } else {
          applyDtViewMode();
        }
      }
      if (atollOverlay.available && map.getLayer('atoll-raster-layer')) {
        atollVisible = nextVisible;
        setLayerVisibility(['atoll-raster-layer'], atollVisible);
      }
      syncTrafficCoverageButtons();
      updateCompareStrip();
      renderLegend();
    };
    document.getElementById('atollFitBtn').onclick = () => {
      if (!atollOverlay.available) return;
      fitBoundsSmart(atollBounds(), 14.8);
    };
    document.getElementById('atollOpacity').oninput = (event) => {
      if (!map.getLayer('atoll-raster-layer')) return;
      map.setPaintProperty('atoll-raster-layer', 'raster-opacity', Number(event.target.value) / 100);
      document.getElementById('atollOpacityValue').textContent = `${event.target.value}%`;
    };
    document.getElementById('colorMode').onchange = (event) => {
      colorMode = event.target.value;
      applyColorMode();
    };
    function setNcellRelationMode(mode) {
      ncellRelationFilter = mode;
      document.getElementById('ncellAllBtn').classList.toggle('active', mode === 'all');
      document.getElementById('ncellIntraBtn').classList.toggle('active', mode === 'IntraFreq');
      document.getElementById('ncellInterBtn').classList.toggle('active', mode === 'InterFreq');
      document.getElementById('ncellIratBtn').classList.toggle('active', mode === 'IRAT');
      applyNcellRelationFilter();
      updateExistingAnrUi();
    }
    document.getElementById('ncellAllBtn').onclick = () => setNcellRelationMode('all');
    document.getElementById('ncellIntraBtn').onclick = () => setNcellRelationMode('IntraFreq');
    document.getElementById('ncellInterBtn').onclick = () => setNcellRelationMode('InterFreq');
    document.getElementById('ncellIratBtn').onclick = () => setNcellRelationMode('IRAT');
    document.getElementById('auditIssuesBtn').onclick = () => setAuditMode('issues');
    document.getElementById('auditOneWayBtn').onclick = () => setAuditMode('oneWay');
    document.getElementById('auditMissingBtn').onclick = () => setAuditMode('missing');
    document.getElementById('auditDupBtn').onclick = () => setAuditMode('duplicate');
    document.getElementById('auditSelectedBtn').onclick = () => {
      auditSelectedOnly = !auditSelectedOnly;
      updateAuditUi();
    };
    document.getElementById('auditExportBtn').onclick = downloadAuditCsv;
    document.getElementById('existingAnrClearBtn').onclick = clearExistingAnrFocus;
    document.getElementById('existingAnrFitBtn').onclick = () => fitBoundsSmart(existingAnrBounds(), 15.5);
    document.getElementById('suggestBtn').onclick = runSuggestions;
    document.getElementById('suggestAddBtn').onclick = () => addTopSuggestions(5);
    function setLinkRelationMode(mode) {
      linkRelationMode = mode;
      document.getElementById('linkAutoBtn').classList.toggle('active', mode === 'auto');
      document.getElementById('linkIntraBtn').classList.toggle('active', mode === 'IntraFreq');
      document.getElementById('linkInterBtn').classList.toggle('active', mode === 'InterFreq');
      document.getElementById('linkIratBtn').classList.toggle('active', mode === 'IRAT');
      updateSelectionUI();
    }
    document.getElementById('linkAutoBtn').onclick = () => setLinkRelationMode('auto');
    document.getElementById('linkIntraBtn').onclick = () => setLinkRelationMode('IntraFreq');
    document.getElementById('linkInterBtn').onclick = () => setLinkRelationMode('InterFreq');
    document.getElementById('linkIratBtn').onclick = () => setLinkRelationMode('IRAT');
    function setCarrierMode(mode) {
      carrierFilter = mode;
      document.getElementById('carrierAllBtn').classList.toggle('active', mode === 'all');
      document.getElementById('carrierL07Btn').classList.toggle('active', mode === 'L07');
      document.getElementById('carrierL18Btn').classList.toggle('active', mode === 'L18');
      document.getElementById('carrierL21Btn').classList.toggle('active', mode === 'L2100');
      document.getElementById('carrierL23Btn').classList.toggle('active', mode === 'L2300');
      document.getElementById('carrierNR26Btn').classList.toggle('active', mode === 'NR2600');
      document.getElementById('carrierNR900Btn').classList.toggle('active', mode === 'NR900');
      document.getElementById('carrierN35Btn').classList.toggle('active', mode === 'N35');
      document.getElementById('carrierF1Btn').classList.toggle('active', mode === 'F1');
      document.getElementById('carrierF2Btn').classList.toggle('active', mode === 'F2');
      document.getElementById('carrierF3Btn').classList.toggle('active', mode === 'F3');
      document.getElementById('carrierF4Btn').classList.toggle('active', mode === 'F4');
      applyCarrierFilter();
    }
    document.getElementById('carrierAllBtn').onclick = () => setCarrierMode('all');
    document.getElementById('carrierL07Btn').onclick = () => setCarrierMode('L07');
    document.getElementById('carrierL18Btn').onclick = () => setCarrierMode('L18');
    document.getElementById('carrierL21Btn').onclick = () => setCarrierMode('L2100');
    document.getElementById('carrierL23Btn').onclick = () => setCarrierMode('L2300');
    document.getElementById('carrierNR26Btn').onclick = () => setCarrierMode('NR2600');
    document.getElementById('carrierNR900Btn').onclick = () => setCarrierMode('NR900');
    document.getElementById('carrierN35Btn').onclick = () => setCarrierMode('N35');
    document.getElementById('carrierF1Btn').onclick = () => setCarrierMode('F1');
    document.getElementById('carrierF2Btn').onclick = () => setCarrierMode('F2');
    document.getElementById('carrierF3Btn').onclick = () => setCarrierMode('F3');
    document.getElementById('carrierF4Btn').onclick = () => setCarrierMode('F4');
    document.getElementById('worstLoadBtn').onclick = loadWorstCells;
    document.getElementById('worstClearBtn').onclick = clearWorstCells;
    document.getElementById('worstFitBtn').onclick = () => fitBoundsSmart(worstBounds(), 15.5);
    document.getElementById('worstDownloadBtn').onclick = downloadWorstCsv;
    document.getElementById('areaBtn').onclick = () => {
      areaMode = !areaMode;
      const btn = document.getElementById('areaBtn');
      btn.textContent = areaMode ? 'Area ON' : 'Area OFF';
      btn.classList.toggle('active', areaMode);
      if (areaMode) {
        selectionMode = false;
        const selectBtn = document.getElementById('selectBtn');
        selectBtn.textContent = 'Selection OFF';
        selectBtn.classList.remove('active');
        pointerMode = 'select';
      } else {
        pointerMode = 'pan';
      }
      applyPointerMode();
    };
    document.getElementById('areaCloseBtn').onclick = closeAreaSelection;
    document.getElementById('areaUndoBtn').onclick = undoAreaPoint;
    document.getElementById('areaClearBtn').onclick = clearAreaSelection;
    document.getElementById('areaFitBtn').onclick = fitAreaSelection;
    document.getElementById('areaDownloadBtn').onclick = downloadAreaCsv;
    document.getElementById('clearBtn').onclick = () => {
      sourceCell = null;
      targets = [];
      suggestRows = [];
      suggestSkippedExisting = 0;
      suggestHasRun = false;
      updateSelectionUI();
    };
    document.getElementById('downloadBtn').onclick = downloadCsv;
    document.getElementById('copyBtn').onclick = copyCsv;
    document.getElementById('meshBtn').onclick = () => {
      groupMeshMode = !groupMeshMode;
      updateSelectionUI();
    };
    document.getElementById('homeBtn').onclick = () => map.flyTo({ center:startCenter, zoom:10.4, speed:1.2 });
    document.getElementById('fitBtn').onclick = () => {
      fitBoundsSmart(dataBounds(), 11.5);
    };
    document.getElementById('cleanMapBtn').onclick = () => {
      labelsVisible = false;
      ncellVisible = false;
      shellsVisible = true;
      dotsVisible = false;
      legendVisible = true;
      carrierFilter = 'all';
      dtVisible = false;
      atollVisible = false;
      shellScale = 0.10;
      shellWidthScale = 0.65;
      siteMarkerScale = 0.8;
      document.getElementById('shellSize').value = 10;
      document.getElementById('shellWidth').value = 65;
      document.getElementById('siteMarkerSize').value = 80;
      document.getElementById('shellSizeText').textContent = 'Shell radius: 10%';
      document.getElementById('shellWidthText').textContent = 'Shell width: 65%';
      document.getElementById('siteMarkerSizeText').textContent = 'Site marker: 80%';
      refreshShellGeometry(false);
      refreshSiteMarkerStyle(false);
      setLayerVisibility(['rf-shell-fill', 'rf-shell-outline'], true);
      setLayerVisibility(['site-dots', 'dt-heatmap', 'dt-points', 'atoll-raster-layer'], false);
      clearExistingAnrFocus();
      setLayerVisibility(['cell-labels', 'manual-ncell-lines', 'manual-ncell-hit', 'existing-anr-lines', 'existing-anr-hit', 'existing-anr-source-shell-fill', 'existing-anr-neighbor-shells-fill', 'existing-anr-source-shell', 'existing-anr-neighbor-shells', 'existing-anr-neighbor-sites'], false);
      applyCarrierFilter();
      applyDtViewMode();
      document.getElementById('dotsBtn').textContent = 'Site Marker OFF';
      document.getElementById('shellsBtn').textContent = 'Shells ON';
      document.getElementById('labelsBtn').textContent = 'Labels OFF';
      document.getElementById('ncellBtn').textContent = 'NCell OFF';
      document.getElementById('dotsBtn').classList.remove('active');
      document.getElementById('shellsBtn').classList.add('active');
      document.getElementById('labelsBtn').classList.remove('active');
      document.getElementById('ncellBtn').classList.remove('active');
      document.getElementById('carrierAllBtn').classList.add('active');
      document.getElementById('carrierL07Btn').classList.remove('active');
      document.getElementById('carrierL18Btn').classList.remove('active');
      document.getElementById('carrierL21Btn').classList.remove('active');
      document.getElementById('carrierL23Btn').classList.remove('active');
      document.getElementById('carrierNR26Btn').classList.remove('active');
      document.getElementById('carrierNR900Btn').classList.remove('active');
      document.getElementById('carrierN35Btn').classList.remove('active');
      document.getElementById('carrierF1Btn').classList.remove('active');
      document.getElementById('carrierF2Btn').classList.remove('active');
      document.getElementById('carrierF3Btn').classList.remove('active');
      document.getElementById('carrierF4Btn').classList.remove('active');
      syncTrafficCoverageButtons();
      drawNetworkOverlay();
      renderLegend();
      updateCompareStrip();
    };
    document.getElementById('compareFitBtn').onclick = () => {
      const bounds = mergeBounds([dtBounds(), atollBounds()]);
      fitBoundsSmart(bounds, 14.8);
      if (hasMeasuredCoverageLayer && !dtVisible) {
        dtVisible = true;
        if (dtColorMode === 'kpiColor') {
          dtColorMode = 'rsrpColor';
          document.getElementById('dtColorMode').value = dtColorMode;
          applyDtColorMode();
        } else {
          applyDtViewMode();
        }
      }
      if (atollOverlay.available && !atollVisible && map.getLayer('atoll-raster-layer')) {
        atollVisible = true;
        setLayerVisibility(['atoll-raster-layer'], true);
      }
      syncTrafficCoverageButtons();
      updateCompareStrip();
      renderLegend();
    };
    document.getElementById('clearViewBtn').onclick = () => {
      selectedDtSample = null;
      selectedDtPoint = null;
      selectedNearestCells = [];
      selectedNearestCellNames = [];
      applySelectedPciMatch();
      applyNearestCellHighlight();
      if (map.getLayer('dt-selected-ring')) {
        map.setFilter('dt-selected-ring', ['==', ['get','index'], -1]);
      }
      shellsVisible = true;
      labelsVisible = false;
      ncellVisible = false;
      dtVisible = false;
      atollVisible = false;
      clearExistingAnrFocus();
      setLayerVisibility(['rf-shell-fill', 'rf-shell-outline'], true);
      setLayerVisibility(['dt-heatmap', 'dt-points', 'atoll-raster-layer', 'cell-labels', 'manual-ncell-lines', 'manual-ncell-hit', 'existing-anr-lines', 'existing-anr-hit', 'existing-anr-source-shell-fill', 'existing-anr-neighbor-shells-fill', 'existing-anr-source-shell', 'existing-anr-neighbor-shells', 'existing-anr-neighbor-sites'], false);
      document.getElementById('shellsBtn').textContent = 'Shells ON';
      document.getElementById('labelsBtn').textContent = 'Labels OFF';
      document.getElementById('ncellBtn').textContent = 'NCell OFF';
      document.getElementById('shellsBtn').classList.add('active');
      document.getElementById('labelsBtn').classList.remove('active');
      document.getElementById('ncellBtn').classList.remove('active');
      syncTrafficCoverageButtons();
      drawNetworkOverlay();
      renderLegend();
      updateCompareStrip();
    };
    document.getElementById('searchBtn').onclick = () => {
      const q = document.getElementById('searchBox').value.trim().toUpperCase();
      if (!q) return;
      const found = cells.features.find(f => {
        const p = f.properties;
        return String(p.CELL_NAME || '').toUpperCase().includes(q)
          || String(p.SITE_NAME || '').toUpperCase().includes(q)
          || String(p.PCI || '').toUpperCase() === q
          || String(p.TAC || '').toUpperCase() === q;
      });
      if (found) {
        map.flyTo({ center:found.geometry.coordinates, zoom:14.2, speed:1.1 });
      }
    };
    document.getElementById('panelTopBtn').onclick = () => {
      document.querySelector('.panel').scrollTo({ top:0, behavior:'smooth' });
    };
    document.getElementById('panelMoreBtn').onclick = () => {
      const panel = document.querySelector('.panel');
      const maxScroll = panel.scrollHeight - panel.clientHeight;
      const nextTop = Math.min(panel.scrollTop + Math.max(220, panel.clientHeight * 0.65), maxScroll);
      panel.scrollTo({ top:nextTop, behavior:'smooth' });
    };
    document.querySelector('.panel').addEventListener('scroll', updatePanelScrollButtons);
    applyPointerMode();
    updatePanelScrollButtons();
  </script>
</body>
</html>
""".replace("__CELLS__", cells_json).replace("__SHELLS__", shells_json).replace("__DT_POINTS__", dt_json).replace("__ANR_SUMMARY__", anr_json).replace("__ATOLL_OVERLAY__", atoll_json).replace("__CENTER_LON__", str(center_lon)).replace("__CENTER_LAT__", str(center_lat)).replace("__BRAND_WORDMARK__", brand_wordmark_url).replace("__BRAND_MARK__", brand_mark_url)


app_css()

df = load_cells()
nbr_df = load_neighbors()
anr_summary = build_anr_summary(nbr_df, df["CELL_NAME"].astype(str))
cells_geojson, shells_geojson = build_geojson(df)
center_lat = float(df["LATITUDE"].mean())
center_lon = float(df["LONGITUDE"].mean())
hero_wordmark_url = image_data_uri(str(BRAND_WORDMARK_FILE))

top_logo_col, info_col = st.columns([1, 2.1], gap="medium")
with top_logo_col:
    st.markdown(
        f"""
<div class="ap-hero">
  <img class="ap-hero-logo" src="{hero_wordmark_url}" alt="automationpark.tech" />
</div>
""",
        unsafe_allow_html=True,
    )
    uploaded_dt_file = st.file_uploader(
        "Upload DT / Traffic CSV/TXT/XLSX",
        type=["csv", "txt", "xlsx", "xls"],
        help="Expected columns include Latitude, Longitude, LTE_UE_PCI, LTE_UE_RSRP, LTE_UE_RSRQ, LTE_UE_SINR. CSV/TXT delimiter is auto-detected.",
    )

st.markdown(
    f"""
<div class="ap-kpi-grid">
  <div class="ap-kpi-card sites"><span>Total Sites</span><strong>{df['SITE_NAME'].nunique():,}</strong></div>
  <div class="ap-kpi-card cells"><span>Total Cells</span><strong>{len(df):,}</strong></div>
  <div class="ap-kpi-card lte"><span>LTE Cells</span><strong>{len(df[df['Technology'].astype(str).str.upper().eq('LTE')]):,}</strong></div>
  <div class="ap-kpi-card nr"><span>5G Cells</span><strong>{len(df[df['Technology'].astype(str).str.upper().str.contains('5G|NR', regex=True, na=False)]):,}</strong></div>
  <div class="ap-kpi-card vendors"><span>Vendors</span><strong>{df['VENDOR'].nunique():,}</strong></div>
  <div class="ap-kpi-card clusters"><span>Clusters</span><strong>{df['CLUSTER_AREA'].nunique():,}</strong></div>
</div>
""",
    unsafe_allow_html=True,
)


traffic_load_start = time.perf_counter()
with info_col:
    st.markdown('<div class="ap-status-spacer"></div>', unsafe_allow_html=True)
    load_progress = st.progress(
        8,
        text=(
            f"Uploading/processing {uploaded_dt_file.name}..."
            if uploaded_dt_file is not None
            else "Loading default Traffic.csv..."
        ),
    )

load_progress.progress(28, text="Reading traffic/KPI table...")
dt_df = load_dt_dataframe(uploaded_dt_file, load_default=uploaded_dt_file is None)
load_progress.progress(62, text="Joining cells and building heatmap features...")
dt_geojson, dt_summary = build_dt_geojson(dt_df, df)
load_progress.progress(84, text="Preparing coverage overlay...")
atoll_overlay = build_atoll_raster_overlay(
    ATOLL_RASTER_FILE.stat().st_mtime_ns if ATOLL_RASTER_FILE.exists() else None,
    ATOLL_WORLD_FILE.stat().st_mtime_ns if ATOLL_WORLD_FILE.exists() else None,
)
traffic_load_elapsed = time.perf_counter() - traffic_load_start
load_progress.progress(100, text=f"Traffic/Coverage ready in {traffic_load_elapsed:.1f}s")

with info_col:
    if dt_summary.get("error"):
        st.warning(dt_summary["error"])
    elif dt_geojson["features"]:
        if dt_summary.get("mode") == "cell_kpi":
            st.success(
                "KPI layer loaded: "
                f"{len(dt_geojson['features']):,} joined cells | "
                f"Counter: {dt_summary.get('kpi_col')}"
            )
            st.caption("KPI/traffic files can use CELL_NAME plus one numeric counter column.")
        else:
            st.success(
                "DT loaded: "
                f"{len(dt_geojson['features']):,} samples | "
                f"PCI: {dt_summary.get('pci_col')} | "
                f"RSRP: {dt_summary.get('rsrp_col')} | "
                f"RSRQ: {dt_summary.get('rsrq_col')} | "
                f"SINR: {dt_summary.get('sinr_col')}"
            )
            st.caption("DT formats supported: CSV, TXT, XLSX/XLS.")
    else:
        st.info("No Traffic/KPI or DT layer loaded yet.")

components.html(
    map_html(cells_geojson, shells_geojson, dt_geojson, anr_summary, atoll_overlay, center_lon, center_lat),
    height=900,
    scrolling=False,
)
