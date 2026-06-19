import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import math
import re
import gc
import time
from xml.sax.saxutils import escape
from core.ncell_engine import create_bidirectional_neighbors
from core.ncell_engine import (
    create_bidirectional_neighbors,
    detect_one_way_neighbors
)
start_time = time.time()
st.set_page_config(layout="wide", page_title="AutomationPark GeoAI V6")
# Force the browser to lower the render intensity
st.markdown("""
<style>
    /* Prevent the browser from trying to redraw the map too fast */
    canvas {
        image-rendering: -webkit-optimize-contrast;
        cursor: crosshair !important;
    }
</style>
""", unsafe_allow_html=True)
# ==========================================
# GLOBAL CSS
# ==========================================
st.markdown("""
<style>

/* Force the map container to be static and remove transitions */
.deck-canvas {
    transition: none !important;
    filter: none !important;
    opacity: 1 !important;
}

/* If you have blur on cards, disable it during map interaction */
.geo-card {
    backdrop-filter: none !important;
    transition: none !important;
}

.geo-card {

    background:#111827;

    border:1px solid rgba(59,130,246,0.15);

    border-left:5px solid #10B981;

    border-radius:14px;

    padding:14px;

    min-height:160px;

    box-shadow:none;
}
/* =====================================================
   MAIN PAGE
===================================================== */

[data-testid="stAppViewContainer"] {
    background: #0F172A !important;
}

.main {
    background: #0F172A !important;
}

.block-container {
    background: #0F172A !important;
    padding-top: 1rem !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* =====================================================
   SIDEBAR
===================================================== */

section[data-testid="stSidebar"] {
    background: rgba(17,24,39,0.96);
    border-right: 1px solid #374151;
}

section[data-testid="stSidebar"] {
    color: white !important;
    font-family: Inter, Segoe UI, sans-serif !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #60A5FA !important;
    font-weight: 700;
}

/* STREAMLIT PAGE NAVIGATION */

[data-testid="stSidebarNav"] span {
    color: white !important;
    opacity: 1 !important;
}

[data-testid="stSidebarNav"] a {
    color: white !important;
    opacity: 1 !important;
}

[data-testid="stSidebarNav"] li {
    color: white !important;
    opacity: 1 !important;
}
section[data-testid="stSidebar"] {
    background: rgba(17,24,39,0.96);
    border-right: 1px solid #374151;
    color: white !important;
}
/* Sidebar controls */

section[data-testid="stSidebar"] label {
    color: white !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] span {
    color: white !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] p {
    color: white !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] div {
    color: white !important;
}

section[data-testid="stSidebar"] label {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #9CA3AF !important;
    letter-spacing: 0.3px;
}

.sidebar-header {
    font-size: 11px;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 12px;
    margin-bottom: 8px;
}

/* Sidebar spacing */

section[data-testid="stSidebar"] .stMarkdown {
    margin-bottom: 0.2rem !important;
}

section[data-testid="stSidebar"] h3 {
    margin-top: 0.4rem !important;
    margin-bottom: 0.3rem !important;
}

hr {
    margin-top: 0.4rem !important;
    margin-bottom: 0.4rem !important;
}

/* =====================================================
   NAV BUTTONS
===================================================== */

.ap-nav-btn {
    background: transparent;
    color: white;
    font-size: 16px;
    font-weight: 700;
    text-align: center;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid transparent;
}

.ap-nav-active {
    background: linear-gradient(
        90deg,
        rgba(29,78,216,0.65),
        rgba(37,99,235,0.30)
    );
    border: 1px solid rgba(96,165,250,0.50);
    box-shadow: 0 0 15px rgba(37,99,235,0.35);
}

/* =====================================================
   SECTIONS
===================================================== */

.ap-sidebar-section {
    background: linear-gradient(
        135deg,
        rgba(16,185,129,0.18),
        rgba(5,150,105,0.08)
    );
    border-left:4px solid #10B981;
    border-radius:12px;
    padding:12px;
    margin-top:12px;
    margin-bottom:10px;
    color:white;
    font-size:15px;
    font-weight:700;
}

.ap-section-title {
    color: #60A5FA;
    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

/* =====================================================
   MULTISELECT
===================================================== */

.stMultiSelect [data-baseweb="tag"]{
    background:#1D4ED8 !important;
    color:white !important;
}

.stMultiSelect div[data-baseweb="select"]{
    background: rgba(16,24,40,0.95) !important;
    border: 1px solid rgba(59,130,246,0.30) !important;
    border-radius: 12px !important;
}

.stMultiSelect span{
    border-radius:8px !important;
}

.stMultiSelect{
    margin-bottom:10px;
}

/* =====================================================
   CHECKBOX
===================================================== */

.stCheckbox div[data-baseweb="checkbox"] svg {
    fill: #3B82F6 !important;
}

.stCheckbox div[data-baseweb="checkbox"] {
    border-color: #3B82F6 !important;
}

.stCheckbox label {
    color: white !important;
    font-weight: 500 !important;
}

/* =====================================================
   TEXT INPUT
===================================================== */

div[data-testid="stTextInput"] input {
    height:40px !important;
    padding-top:0px !important;
    padding-bottom:0px !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #94a3b8;
}

/* =====================================================
   WORST CELL BOX
===================================================== */

div[data-testid="stTextArea"] {
    background: rgba(15, 23, 42, 0.88) !important;
    border: 1px solid rgba(239, 68, 68, 0.38) !important;
    border-radius: 14px !important;
    padding: 10px 10px 12px 10px !important;
    margin-top: 0px !important;
    margin-bottom: 8px !important;
    box-shadow: 0 0 18px rgba(239, 68, 68, 0.10) !important;
}

div[data-testid="stTextArea"] textarea {
    background: rgba(2, 6, 23, 0.92) !important;
    border: 1px solid rgba(148, 163, 184, 0.28) !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: Consolas, monospace !important;
}

div[data-testid="stTextArea"] textarea:focus {
    border-color: #EF4444 !important;
    box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.20) !important;
}

div[data-testid="stTextArea"] textarea::placeholder {
    color: #94a3b8 !important;
}

div[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #F5B84B, #F97316) !important;
    color: #061015 !important;
    border: 1px solid rgba(245, 184, 75, 0.88) !important;
    border-radius: 10px !important;
    font-weight: 900 !important;
    min-height: 44px !important;
    box-shadow: 0 0 18px rgba(245, 184, 75, 0.24) !important;
}

div[data-testid="stDownloadButton"] button * {
    color: #061015 !important;
    font-weight: 900 !important;
}

/* =====================================================
   ANR MINI CARD
===================================================== */

.anr-mini-card{
    background:#16213e;
    border-left:4px solid #22c55e;
    border-radius:10px;
    padding:10px;
    margin-bottom:8px;
    text-align:center;
}

.anr-mini-label{
    color:#94a3b8;
    font-size:11px;
    font-weight:500;
    text-transform:uppercase;
}

.anr-mini-value{
    color:white;
    font-size:22px;
    font-weight:700;
    margin-top:4px;
}

/* =====================================================
   GEO CARDS
===================================================== */

.geo-card {
    background: linear-gradient(
        180deg,
        rgba(12,22,45,0.95),
        rgba(8,15,35,0.95)
    );
    border: 1px solid rgba(59,130,246,0.20);
    border-left: 5px solid #10B981;
    border-radius: 14px;
    padding: 14px;
    min-height: 160px;
    box-shadow: 0 0 12px rgba(59,130,246,0.08);
    transition: all 0.25s ease;
}

.geo-label {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.75);
}

.geo-value {
    font-size: 40px;
    font-weight: 800;
    color: white;
    margin-top: 12px;
    line-height: 1;
}

/* =====================================================
   INFO PANEL
===================================================== */

.info-panel {
    position: fixed;
    top: 425px;
    right: 80px;
    width: 350px;
    height:67vh;
    background: rgba(17,24,39,0.70);
    backdrop-filter: blur(10px);
    border-left: 1px solid #374151;
    padding: 15px;
    z-index: 9999;
    color: white;
    overflow-y: auto;
}

.info-title {
    font-size: 24px;
    font-weight: 700;
    color: #60A5FA;
}

.info-section {
    font-size: 20px;
    font-weight: 700;
    color: #FBBF24;
}

.info-value {
    font-size: 17px;
    font-weight: 700;
    color: white;
}

/* =====================================================
   BUTTON GLOW
===================================================== */

/* =====================================================
   BUTTONS
===================================================== */

div.stButton > button {

    background: linear-gradient(
        180deg,
        rgba(10,25,55,1),
        rgba(5,15,35,1)
    );

    color: white !important;

    border: 1px solid rgba(59,130,246,0.25);

    border-radius: 16px;

    height: 48px;

    font-size: 15px;

    font-weight: 800;

    letter-spacing: 0.4px;

    box-shadow:
        0 0 10px rgba(59,130,246,0.10);

}

div.stButton > button * {
    color: white !important;
    opacity: 1 !important;
}

div.stButton > button:hover {

    border: 1px solid #3B82F6;

    box-shadow:
        0 0 15px rgba(59,130,246,0.35);

}
div[data-testid="stTextInput"] input {

    background: linear-gradient(
        180deg,
        rgba(15,23,42,0.95),
        rgba(10,15,30,0.95)
    ) !important;

    color:white !important;

    border:1px solid rgba(59,130,246,0.25) !important;

    box-shadow:
        0 0 10px rgba(59,130,246,0.10);

}

.ap-tool-divider {
    height: 2px;
    border-radius: 999px;
    margin: 12px 0 22px 0;
    background: linear-gradient(90deg, #22D3D8, rgba(59,130,246,0.45), transparent);
    box-shadow: 0 0 18px rgba(34,211,216,0.25);
}

.ap-tool-title {
    color: #F8FAFC !important;
    font-size: 24px;
    font-weight: 900;
    letter-spacing: 0.2px;
    margin: 8px 0 12px 0;
}

.ap-tool-copy {
    color: #D9F7FF !important;
    font-size: 15px;
    line-height: 1.55;
    opacity: 1 !important;
}

.ap-tool-note {
    color: #A7F3D0 !important;
    font-size: 14px;
    line-height: 1.45;
    opacity: 1 !important;
}

.m2-card {
    color: #E0F2FE !important;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin: 4px 0 8px 0;
    padding: 6px 9px;
    border-left: 3px solid #22D3D8;
    border-radius: 8px;
    background: linear-gradient(90deg, rgba(34,211,216,0.12), rgba(59,130,246,0.04));
    opacity: 1 !important;
}

.m2-card * {
    color: #E0F2FE !important;
    opacity: 1 !important;
}

.m2-status {
    color: #A7F3D0 !important;
    font-size: 12px;
    font-weight: 700;
    margin-top: 6px;
    min-height: 16px;
}

.nav-tool-pad {
    height: 8px;
}

.map-tool-status {
    color: #BAE6FD !important;
    font-size: 12px;
    font-weight: 800;
    margin-top: 8px;
    padding: 7px 9px;
    min-height: 28px;
    border-radius: 8px;
    background: rgba(13,40,76,0.42);
    border: 1px solid rgba(34,211,216,0.18);
}

.ap-selection-card {
    background: rgba(15,23,42,0.88);
    border: 1px solid rgba(245,184,75,0.32);
    border-left: 4px solid #F5B84B;
    border-radius: 12px;
    padding: 12px;
    margin-top: 14px;
    margin-bottom: 12px;
    font-size: 12px;
    line-height: 1.45;
    color: #E5E7EB;
}

.ap-selection-card b {
    color: #F8FAFC !important;
    font-size: 13px;
}

.ap-selection-status {
    border-radius: 999px;
    padding: 8px 10px;
    margin: 10px 0 12px 0;
    font-size: 11px;
    font-weight: 900;
    text-align: center;
    letter-spacing: 0.2px;
}

section[data-testid="stSidebar"] {
    box-shadow: inset -1px 0 0 rgba(34,211,216,0.10);
}

section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.35rem !important;
}

section[data-testid="stSidebar"] .sidebar-header {
    background: linear-gradient(90deg, rgba(34,211,216,0.12), rgba(59,130,246,0.04));
    border-left: 3px solid #22D3D8;
    border-radius: 8px;
    padding: 7px 9px;
    color: #E0F2FE !important;
    font-weight: 900 !important;
}

section[data-testid="stSidebar"] div.stButton > button {
    min-height: 38px !important;
    height: 38px !important;
    border-radius: 10px !important;
    font-size: 12px !important;
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #BAE6FD !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(34,211,216,0.16) !important;
}

[data-testid="stAlert"] {
    background: rgba(13,40,76,0.90) !important;
    border: 1px solid rgba(34,211,216,0.28) !important;
    border-radius: 10px !important;
}

[data-testid="stAlert"] *,
[data-testid="stMetric"] *,
[data-testid="stFileUploader"] *,
[data-testid="stDownloadButton"] * {
    color: #F8FAFC !important;
    opacity: 1 !important;
}

[data-testid="stFileUploader"] section {
    background: linear-gradient(180deg, rgba(10,25,55,0.98), rgba(5,15,35,0.98)) !important;
    border: 1px solid rgba(34,211,216,0.35) !important;
    border-radius: 12px !important;
    color: #F8FAFC !important;
}

[data-testid="stFileUploader"] section div,
[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small {
    color: #D9F7FF !important;
    opacity: 1 !important;
}

[data-testid="stFileUploader"] button,
[data-testid="stLinkButton"] a,
a[data-testid="stLinkButton"] {
    background: linear-gradient(180deg, rgba(10,25,55,1), rgba(5,15,35,1)) !important;
    color: #F8FAFC !important;
    border: 1px solid rgba(34,211,216,0.42) !important;
    border-radius: 12px !important;
    font-weight: 900 !important;
    box-shadow: 0 0 14px rgba(34,211,216,0.12) !important;
}

[data-testid="stFileUploader"] button *,
[data-testid="stLinkButton"] a *,
a[data-testid="stLinkButton"] * {
    color: #F8FAFC !important;
    opacity: 1 !important;
}

[data-testid="stFileUploader"] button:hover,
[data-testid="stLinkButton"] a:hover,
a[data-testid="stLinkButton"]:hover {
    border-color: #22D3D8 !important;
    box-shadow: 0 0 20px rgba(34,211,216,0.25) !important;
}

[data-testid="stMetricValue"] {
    color: #F8FAFC !important;
}

[data-testid="stMetricLabel"] {
    color: #BAE6FD !important;
}

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] p {
    color: #F8FAFC !important;
    opacity: 1 !important;
}
/* FORCE DARK MULTISELECT */

[data-baseweb="select"] {

    background: rgba(15,23,42,0.95) !important;

}

[data-baseweb="select"] * {

    background: transparent !important;

    color: white !important;

}

</style>
""", unsafe_allow_html=True)
# --- 1. DATA & NEIGHBOR ENGINE ---
@st.cache_data
def get_data():
    df = pd.read_csv(r"datasets/CCCCell-Site.csv")
    nbr_df = pd.read_csv(r"datasets/Neighbors-OK.csv")

    # Ensure mandatory columns exist
    df = df.dropna(subset=['LATITUDE', 'LONGITUDE', 'AZIMUTH'])

    # Safe CARRIER handling: if not present, create it from Technology
    if 'CARRIER' not in df.columns:
        df['CARRIER'] = df['Technology'] if 'Technology' in df.columns else 'Unknown'
    # Safe BEAMWIDTH handling
    if 'BEAMWIDTH' not in df.columns:
        df['BEAMWIDTH'] = 65
    return df, nbr_df

# Call data engine immediately
df, nbr_df = get_data()

# Initialize session state
if "focus_lat" not in st.session_state:
    st.session_state.focus_lat = df['LATITUDE'].mean()
if "focus_lon" not in st.session_state:
    st.session_state.focus_lon = df['LONGITUDE'].mean()
if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = 12
if "worst_cell_text" not in st.session_state:
    st.session_state.worst_cell_text = ""
if "worst_cell_input" not in st.session_state:
    st.session_state.worst_cell_input = st.session_state.worst_cell_text
if "selected_cells" not in st.session_state:
    st.session_state.selected_cells = []
if "selection_mode" not in st.session_state:
    st.session_state.selection_mode = False
if "ncell_source_cell" not in st.session_state:
    st.session_state.ncell_source_cell = None
if "active_top_tool" not in st.session_state:
    st.session_state.active_top_tool = None
if "top_search_cells" not in st.session_state:
    st.session_state.top_search_cells = []
if "map_style_mode" not in st.session_state:
    st.session_state.map_style_mode = "dark"
if "map_tool_message" not in st.session_state:
    st.session_state.map_tool_message = ""
if "coverage_kpi_column" not in st.session_state:
    st.session_state.coverage_kpi_column = None
if "coverage_display_mode" not in st.session_state:
    st.session_state.coverage_display_mode = "Heatmap + cell shells"
if "coverage_heatmap_radius" not in st.session_state:
    st.session_state.coverage_heatmap_radius = 42
if "coverage_heatmap_intensity" not in st.session_state:
    st.session_state.coverage_heatmap_intensity = 1.2
if "coverage_reverse_scale" not in st.session_state:
    st.session_state.coverage_reverse_scale = False
if "selected_ncell_link" not in st.session_state:
    st.session_state.selected_ncell_link = None
if "los_select_mode" not in st.session_state:
    st.session_state.los_select_mode = False
if "map_pins" not in st.session_state:
    st.session_state.map_pins = []
if "show_predicted_coverage" not in st.session_state:
    st.session_state.show_predicted_coverage = False
if "predicted_coverage_cell" not in st.session_state:
    st.session_state.predicted_coverage_cell = None


def clear_worst_cells():
    st.session_state.worst_cell_text = ""
    st.session_state.worst_cell_input = ""


def add_selected_cell(cell_name):
    if not cell_name:
        return

    cell_name = str(cell_name).strip()

    if st.session_state.ncell_source_cell is None:
        st.session_state.ncell_source_cell = cell_name
        return

    if cell_name == st.session_state.ncell_source_cell:
        return

    if cell_name and cell_name not in st.session_state.selected_cells:
        st.session_state.selected_cells.append(cell_name)


def remove_selected_cell(cell_name):
    st.session_state.selected_cells = [
        cell for cell in st.session_state.selected_cells
        if cell != cell_name
    ]


def clear_selected_cells():
    st.session_state.selected_cells = []
    st.session_state.ncell_source_cell = None


def get_relation_type(source_cell, target_cell, cell_df):
    lookup_df = cell_df.set_index(cell_df["CELL_NAME"].astype(str))

    if source_cell not in lookup_df.index or target_cell not in lookup_df.index:
        return "Unknown"

    source = lookup_df.loc[source_cell]
    target = lookup_df.loc[target_cell]

    source_tech = str(source.get("Technology", "")).upper()
    target_tech = str(target.get("Technology", "")).upper()
    source_carrier = str(source.get("CARRIER", "")).upper()
    target_carrier = str(target.get("CARRIER", "")).upper()

    if source_tech != target_tech:
        return "IRAT"
    if source_carrier != target_carrier:
        return "InterFreq"
    return "IntraFreq"


def build_ncell_export(source_cell, target_cells, cell_df, bidirectional=True):
    rows = []

    if not source_cell:
        return pd.DataFrame(columns=["Src_Cell", "Targ_Cell", "Ncell_Type"])

    for target_cell in target_cells:
        if not target_cell or target_cell == source_cell:
            continue

        relation_type = get_relation_type(source_cell, target_cell, cell_df)
        rows.append({
            "Src_Cell": source_cell,
            "Targ_Cell": target_cell,
            "Ncell_Type": relation_type
        })

        if bidirectional:
            rows.append({
                "Src_Cell": target_cell,
                "Targ_Cell": source_cell,
                "Ncell_Type": relation_type
            })

    return pd.DataFrame(rows).drop_duplicates()


def set_active_top_tool(tool_name):
    st.session_state.active_top_tool = (
        None if st.session_state.active_top_tool == tool_name else tool_name
    )


def toggle_los_select_mode():
    st.session_state.los_select_mode = not st.session_state.get("los_select_mode", False)
    st.session_state.map_tool_message = (
        "LOS Line Select Mode ON: pointer mode active and hidden line hitboxes are wider."
        if st.session_state.los_select_mode
        else "LOS Line Select Mode OFF."
    )


def toggle_map_style_mode():
    st.session_state.map_style_mode = (
        "satellite" if st.session_state.map_style_mode == "dark" else "dark"
    )
    st.session_state.map_tool_message = f"Base map: {st.session_state.map_style_mode.title()}"


def toggle_predicted_coverage():
    clicked_cell = st.session_state.get("last_clicked_cell")

    if clicked_cell:
        if (
            st.session_state.get("show_predicted_coverage")
            and st.session_state.get("predicted_coverage_cell") == clicked_cell
        ):
            st.session_state.show_predicted_coverage = False
            st.session_state.map_tool_message = "Predicted antenna coverage OFF."
        else:
            st.session_state.predicted_coverage_cell = clicked_cell
            st.session_state.show_predicted_coverage = True
            st.session_state.map_tool_message = f"Predicted antenna coverage ON for {clicked_cell}."
    else:
        st.session_state.map_tool_message = "Click a cell shell first, then press Cover to show predicted antenna coverage."


def clear_predicted_coverage():
    st.session_state.show_predicted_coverage = False
    st.session_state.predicted_coverage_cell = None
    st.session_state.map_tool_message = "Predicted coverage cleared."


def clear_engineering_pins():
    st.session_state.map_pins = []
    st.session_state.map_tool_message = "Engineering pins cleared."


def find_cells(cell_df, query, columns):
    query = str(query or "").strip()
    if not query:
        return cell_df.iloc[0:0].copy()

    mask = pd.Series(False, index=cell_df.index)

    for column in columns:
        if column not in cell_df.columns:
            continue
        mask = mask | cell_df[column].astype(str).str.contains(
            query,
            case=False,
            na=False,
            regex=False
        )

    return cell_df[mask].copy()


def focus_on_rows(rows, zoom_level=15):
    if rows is None or rows.empty:
        return False

    st.session_state.focus_lat = rows["LATITUDE"].mean()
    st.session_state.focus_lon = rows["LONGITUDE"].mean()
    st.session_state.zoom_level = zoom_level

    first_row = rows.iloc[0]
    st.session_state.last_clicked_site = first_row.get("SITE_NAME")
    st.session_state.last_clicked_cell = first_row.get("CELL_NAME")
    return True


def build_cell_kml(cell_df, name="AutomationPark Selected Cells"):
    placemarks = []

    for _, row in cell_df.iterrows():
        cell_name = escape(str(row.get("CELL_NAME", "Cell")))
        site_name = escape(str(row.get("SITE_NAME", "")))
        lon = row.get("LONGITUDE")
        lat = row.get("LATITUDE")

        if pd.isna(lat) or pd.isna(lon):
            continue

        placemarks.append(f"""
    <Placemark>
      <name>{cell_name}</name>
      <description>{site_name}</description>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{escape(str(name))}</name>
    {''.join(placemarks)}
  </Document>
</kml>"""


def build_ncell_kml(source_cell, target_cells, cell_df):
    cell_lookup = cell_df.set_index(cell_df["CELL_NAME"].astype(str))
    placemarks = []

    if not source_cell or source_cell not in cell_lookup.index:
        return build_cell_kml(pd.DataFrame(), "AutomationPark NCell Links")

    source = cell_lookup.loc[source_cell]

    for target_cell in target_cells:
        if target_cell not in cell_lookup.index:
            continue

        target = cell_lookup.loc[target_cell]
        relation_type = get_relation_type(source_cell, target_cell, cell_df)
        line_name = escape(f"{source_cell} to {target_cell}")
        line_description = escape(f"{relation_type} NCell")
        placemarks.append(f"""
    <Placemark>
      <name>{line_name}</name>
      <description>{line_description}</description>
      <LineString>
        <tessellate>1</tessellate>
        <coordinates>
          {source['LONGITUDE']},{source['LATITUDE']},0
          {target['LONGITUDE']},{target['LATITUDE']},0
        </coordinates>
      </LineString>
    </Placemark>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>AutomationPark Visual NCell Links</name>
    {''.join(placemarks)}
  </Document>
</kml>"""


def parse_cell_list(raw_text):
    if not raw_text:
        return []

    tokens = re.split(r"[\s,;]+", str(raw_text).strip())
    cells = []
    seen = set()

    for token in tokens:
        cell_name = token.strip()
        if not cell_name:
            continue

        key = cell_name.upper()
        if key not in seen:
            seen.add(key)
            cells.append(cell_name)

    return cells


def get_numeric_columns(input_df):
    numeric_columns = []

    for column in input_df.columns:
        values = pd.to_numeric(input_df[column], errors="coerce")
        if values.notna().sum() > 0:
            numeric_columns.append(column)

    return numeric_columns


def build_kpi_map_df(upload_df, network_df, kpi_column):
    if upload_df is None or upload_df.empty or not kpi_column:
        return pd.DataFrame()

    kpi_df = upload_df.copy()
    kpi_df["KPI_VALUE"] = pd.to_numeric(kpi_df[kpi_column], errors="coerce")
    kpi_df = kpi_df.dropna(subset=["KPI_VALUE"])

    if kpi_df.empty:
        return pd.DataFrame()

    cell_column = next(
        (
            col for col in kpi_df.columns
            if str(col).strip().upper() in {"CELL_NAME", "CELL", "CELL_ID", "CELLNAME", "CELL ID"}
        ),
        None
    )

    lat_column = next(
        (
            col for col in kpi_df.columns
            if str(col).strip().upper() in {"LATITUDE", "LAT", "Y"}
        ),
        None
    )
    lon_column = next(
        (
            col for col in kpi_df.columns
            if str(col).strip().upper() in {"LONGITUDE", "LON", "LONG", "X"}
        ),
        None
    )

    if cell_column:
        network_lookup = network_df.drop_duplicates(subset=["CELL_NAME"]).copy()
        result_df = kpi_df.merge(
            network_lookup[
                [
                    "CELL_NAME", "SITE_NAME", "LATITUDE", "LONGITUDE",
                    "Technology", "CARRIER", "VENDOR", "TAC", "CLUSTER_AREA"
                ]
            ],
            left_on=cell_column,
            right_on="CELL_NAME",
            how="inner"
        )
    elif lat_column and lon_column:
        result_df = kpi_df.copy()
        result_df["LATITUDE"] = pd.to_numeric(result_df[lat_column], errors="coerce")
        result_df["LONGITUDE"] = pd.to_numeric(result_df[lon_column], errors="coerce")
        if "CELL_NAME" not in result_df.columns:
            result_df["CELL_NAME"] = "DriveTest"
        if "SITE_NAME" not in result_df.columns:
            result_df["SITE_NAME"] = "DriveTest"
    else:
        return pd.DataFrame()

    result_df = result_df.dropna(subset=["LATITUDE", "LONGITUDE", "KPI_VALUE"]).copy()
    result_df["KPI_ABS_WEIGHT"] = result_df["KPI_VALUE"].abs()
    result_df["KPI_TOOLTIP"] = (
        result_df.get("CELL_NAME", pd.Series(["KPI"] * len(result_df))).astype(str)
        + "<br>"
        + str(kpi_column)
        + ": "
        + result_df["KPI_VALUE"].round(2).astype(str)
    )

    return result_df


def kpi_color(value, min_value, max_value, reverse=False):
    if pd.isna(value):
        return [148, 163, 184, 80]

    if max_value == min_value:
        ratio = 1
    else:
        ratio = (value - min_value) / (max_value - min_value)

    ratio = max(0, min(1, ratio))
    if reverse:
        ratio = 1 - ratio

    if ratio < 0.33:
        return [16, 185, 129, 95]
    if ratio < 0.66:
        return [245, 158, 11, 105]
    return [239, 68, 68, 120]


def haversine_km(lat1, lon1, lat2, lon2):
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def bearing_deg(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = (
        math.cos(lat1_rad) * math.sin(lat2_rad)
        - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    )
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def build_link_profile(source_cell, target_cell, relation_type, cell_df):
    if not source_cell or not target_cell:
        return None

    lookup_df = cell_df.drop_duplicates(subset=["CELL_NAME"]).set_index(
        cell_df.drop_duplicates(subset=["CELL_NAME"])["CELL_NAME"].astype(str)
    )

    if source_cell not in lookup_df.index or target_cell not in lookup_df.index:
        return None

    source = lookup_df.loc[source_cell]
    target = lookup_df.loc[target_cell]
    src_lat = float(source["LATITUDE"])
    src_lon = float(source["LONGITUDE"])
    tgt_lat = float(target["LATITUDE"])
    tgt_lon = float(target["LONGITUDE"])
    distance = haversine_km(src_lat, src_lon, tgt_lat, tgt_lon)
    bearing = bearing_deg(src_lat, src_lon, tgt_lat, tgt_lon)

    samples = []
    for index in range(21):
        ratio = index / 20
        pseudo_terrain = 18 + 10 * math.sin(ratio * math.pi) + 4 * math.sin(ratio * math.pi * 3)
        los_height = 45 + (35 - 45) * ratio
        samples.append({
            "distance_km": distance * ratio,
            "terrain_m": round(pseudo_terrain, 1),
            "los_m": round(los_height, 1),
        })

    clearance_values = [
        sample["los_m"] - sample["terrain_m"]
        for sample in samples
    ]
    min_clearance = min(clearance_values)

    if min_clearance < 0:
        los_status = "Blocked"
        los_status_color = "#EF4444"
    elif min_clearance < 8:
        los_status = "Near obstruction"
        los_status_color = "#F59E0B"
    else:
        los_status = "Clear LOS"
        los_status_color = "#10B981"

    return {
        "source": source_cell,
        "target": target_cell,
        "relation_type": relation_type or get_relation_type(source_cell, target_cell, cell_df),
        "source_site": source.get("SITE_NAME", "-"),
        "target_site": target.get("SITE_NAME", "-"),
        "source_lat": src_lat,
        "source_lon": src_lon,
        "target_lat": tgt_lat,
        "target_lon": tgt_lon,
        "distance_km": distance,
        "bearing_deg": bearing,
        "min_clearance_m": min_clearance,
        "los_status": los_status,
        "los_status_color": los_status_color,
        "samples": samples,
    }


def build_predicted_coverage(cell_row, display_shell_row=None):
    lat = float(cell_row["LATITUDE"])
    lon = float(cell_row["LONGITUDE"])
    azimuth = float(cell_row.get("AZIMUTH", 0))
    if display_shell_row is not None:
        azimuth = float(display_shell_row.get("AZIMUTH", azimuth))
    beamwidth = float(cell_row.get("BEAMWIDTH", 65))
    height = float(cell_row.get("HEIGHT", 15))
    tilt = float(cell_row.get("M_TILT", 0))
    pmax = float(cell_row.get("PMAX", 46))
    cell_radius = float(cell_row.get("CELLRADIUS", 2500))
    antenna = str(cell_row.get("ANTENNA", "Unknown antenna"))

    band_text = " ".join([
        str(cell_row.get("CELL_NAME", "")),
        str(cell_row.get("CARRIER", "")),
        antenna,
    ]).upper()

    if any(token in band_text for token in ["N35", "3500"]):
        band_radius_km = 1.25
        band_label = "NR3500 / high-band"
    elif any(token in band_text for token in ["NR23", "L23", "2300"]):
        band_radius_km = 1.8
        band_label = "2300 MHz"
    elif any(token in band_text for token in ["L21", "2100"]):
        band_radius_km = 2.1
        band_label = "2100 MHz"
    elif any(token in band_text for token in ["L18", "1800"]):
        band_radius_km = 2.8
        band_label = "1800 MHz"
    elif any(token in band_text for token in ["L07", "NR07", "0700", "700"]):
        band_radius_km = 4.8
        band_label = "700 MHz / low-band"
    else:
        band_radius_km = 2.5
        band_label = "generic band"

    data_radius_km = max(0.6, min(cell_radius / 1000, 8.0))
    radius_km = min(data_radius_km, band_radius_km)
    power_factor = max(0.75, min((pmax - 36) / 12, 1.35))
    height_factor = max(0.75, min(height / 25, 1.35))
    tilt_factor = max(0.55, 1 - max(tilt, 0) / 18)
    outer_radius_km = max(0.5, min(radius_km * power_factor * height_factor * tilt_factor, band_radius_km))

    rings = [
        (outer_radius_km * 1.00, [16, 185, 129, 34], "Outer predicted coverage"),
        (outer_radius_km * 0.66, [34, 211, 238, 58], "Mid predicted coverage"),
        (outer_radius_km * 0.34, [245, 184, 75, 82], "Strong predicted coverage"),
    ]

    coverage_rows = []
    for radius, color, label in rings:
        points = [[lon, lat]]
        for angle in np.linspace(azimuth - beamwidth / 2, azimuth + beamwidth / 2, 34):
            point_lat = lat + (radius / 111.0) * math.cos(math.radians(angle))
            point_lon = lon + (radius / (111.0 * math.cos(math.radians(lat)))) * math.sin(math.radians(angle))
            points.append([point_lon, point_lat])
        points.append([lon, lat])

        coverage_rows.append({
            "polygon": points,
            "fill_color": color,
            "line_color": color[:3],
            "CELL_NAME": str(cell_row.get("CELL_NAME", "")),
            "SITE_NAME": str(cell_row.get("SITE_NAME", "")),
            "tooltip_text": (
                f"{label}<br>"
                f"Cell: {cell_row.get('CELL_NAME', '')}<br>"
                f"Antenna: {antenna}<br>"
                f"Azimuth: {azimuth:.0f} deg | Beamwidth: {beamwidth:.0f} deg<br>"
                f"Band model: {band_label} | Radius: {outer_radius_km:.2f} km<br>"
                f"Height: {height:.1f} m | Tilt: {tilt:.1f} deg | PMAX: {pmax:.1f} dBm"
            )
        })

    return pd.DataFrame(coverage_rows)

@st.cache_data(show_spinner=False)
def build_shell_cache(df):

    shell_polygons = []

    for _, row in df.iterrows():

        lat = row["LATITUDE"]
        lon = row["LONGITUDE"]
        cell_name = str(row["CELL_NAME"])

        if "-A" in cell_name:
            az = 0
        elif "-B" in cell_name:
            az = 120
        elif "-C" in cell_name:
            az = 240
        else:
            az = row["AZIMUTH"]

        if "L07" in cell_name:
            radius = 0.0020
            fill_color = [0,255,120,00]
            line_color = [0,255,120]

        elif "L18" in cell_name:
            radius = 0.0016
            fill_color = [255,180,0,00]
            line_color = [255,180,0]

        elif "N35" in cell_name:
            radius = 0.0012
            fill_color = [255,255,255,00]
            line_color = [255,255,255]

        else:
            continue

        left_angle = az - 21
        right_angle = az + 21

        left_lat = lat + radius * np.cos(np.radians(left_angle))
        left_lon = lon + radius * np.sin(np.radians(left_angle))

        right_lat = lat + radius * np.cos(np.radians(right_angle))
        right_lon = lon + radius * np.sin(np.radians(right_angle))

        center_lat = lat + radius * np.cos(np.radians(az))
        center_lon = lon + radius * np.sin(np.radians(az))

        polygon = [

                [lon, lat],

                [left_lon, left_lat],

                [center_lon, center_lat],

                [right_lon, right_lat]

            ]
        # =====================================
        # ACTIVE CELL HIGHLIGHT
        # =====================================



        shell_polygons.append({

            "CELL_NAME": cell_name,

            "AZIMUTH": az,

            "TIP_LAT": center_lat,

            "TIP_LON": center_lon,

            "polygon": polygon,

            "fill_color": fill_color,

            "line_color": line_color

        })
    return pd.DataFrame(shell_polygons)
# ==========================================
# ONE-WAY NCELL DETECTION
# ==========================================

@st.cache_data(show_spinner=False)
def get_one_way_neighbors(neighbor_df):
    clean_df = neighbor_df[["source_sector", "target_sector"]].dropna().copy()
    clean_df["source_sector"] = clean_df["source_sector"].astype(str).str.strip()
    clean_df["target_sector"] = clean_df["target_sector"].astype(str).str.strip()

    pairs = set(zip(clean_df["source_sector"], clean_df["target_sector"]))
    one_way = [
        {"source_sector": source, "target_sector": target}
        for source, target in pairs
        if (target, source) not in pairs
    ]

    return pd.DataFrame(one_way, columns=["source_sector", "target_sector"])


@st.cache_data(show_spinner=False)
def get_missing_ncell_targets(neighbor_df, valid_cell_names):
    valid_cells = {str(cell).strip() for cell in valid_cell_names}
    clean_df = neighbor_df[["source_sector", "target_sector"]].dropna().copy()
    clean_df["source_sector"] = clean_df["source_sector"].astype(str).str.strip()
    clean_df["target_sector"] = clean_df["target_sector"].astype(str).str.strip()

    missing_df = clean_df[
        ~clean_df["target_sector"].isin(valid_cells)
    ].copy()

    return missing_df.drop_duplicates()


one_way_df = get_one_way_neighbors(nbr_df)
missing_ncell_df = get_missing_ncell_targets(
    nbr_df,
    df["CELL_NAME"].astype(str)
)

# ==========================================
# MISSING NCELL DETECTION
# ==========================================

#missing_neighbors = []

#all_cells = set(
    #df["CELL_NAME"]
#)

#cells_with_neighbors = set(
    #nbr_df["source_sector"]
#)

#for cell in all_cells:

    #if cell not in cells_with_neighbors:

        #missing_neighbors.append(cell)

#    {
        #"CELL_NAME": missing_neighbors
    #}
#)
# ==========================================
# SPECIAL SITES DATA
# ==========================================

special_sites_df = pd.DataFrame([

{
    "TYPE":"Hospital",
    "NAME":"Auckland Hospital",
    "LAT":-36.859,
    "LON":174.768
},

{
    "TYPE":"Police",
    "NAME":"Auckland Police",
    "LAT":-36.852,
    "LON":174.763
},

{
    "TYPE":"Event",
    "NAME":"Eden Park",
    "LAT":-36.874,
    "LON":174.744
},

{
    "TYPE":"Roaming",
    "NAME":"National Roaming Site",
    "LAT":-36.847,
    "LON":174.782
},

{
    "TYPE":"Store",
    "NAME":"OPT Store CBD",
    "LAT":-36.848,
    "LON":174.765
},

{
    "TYPE":"Hub",
    "NAME":"Core Hub",
    "LAT":-36.845,
    "LON":174.772
}

])
# ==================================
# TECHNOLOGY LAYERS
# ==================================

st.sidebar.markdown(
    """
    <div style="
        background: linear-gradient(
            135deg,
            rgba(16,185,129,0.20),
            rgba(5,150,105,0.10)
        );
        border-left: 4px solid #10B981;
        border-radius: 12px;
        padding: 12px;
        margin-top: 10px;
        margin-bottom: 10px;
        color: white;
        font-weight: 700;
        font-size: 16px;
    ">
        🟢 TECHNOLOGY LAYERS
    </div>
    """,
    unsafe_allow_html=True
        )

show_L07 = st.sidebar.checkbox(
    "L07 Layer",
    value=False,
    key="tech_l07"
)

show_L18 = st.sidebar.checkbox(
    "L18 Layer",
    value=False,
    key="tech_l18"
)

show_N35 = st.sidebar.checkbox(
    "N35 Layer",
    value=False,
    key="tech_n35"
)

show_L21 = st.sidebar.checkbox(
    "L21 Layer",
    value=False,
    key="tech_l21"
)

show_NR23 = st.sidebar.checkbox(
    "NR23 Layer",
    value=False,
    key="tech_nr23"
)

show_NR07 = st.sidebar.checkbox(
    "NR07 Layer",
    value=False,
    key="tech_nr07"
)
# =====================================================
# ANR Type
# =====================================================
# ==================================
# NCELL TYPES
# ==================================

st.sidebar.markdown("""
<div style="
background: linear-gradient(
135deg,
rgba(16,185,129,0.25),
rgba(5,150,105,0.15)
);
border-left: 4px solid #10B981;
border-radius: 12px;
padding: 12px;
margin-top: 15px;
margin-bottom: 10px;
font-weight: 600;
color: white;
">
🟢 NCELL TYPES
</div>
""", unsafe_allow_html=True)

show_intrafreq = st.sidebar.checkbox(
    "IntraFreq",
    value=False,
    key="ncell_intra"
)

show_interfreq = st.sidebar.checkbox(
    "InterFreq",
    value=False,
    key="ncell_inter"
)

show_irat = st.sidebar.checkbox(
    "IRAT",
    value=False,
    key="ncell_irat"
)

show_ncells = st.sidebar.checkbox(
    "NCell Relations",
    value=False,
    key="ncell_relations"
)

st.sidebar.markdown(f"""
<div style="
background:rgba(15,23,42,0.88);
border:1px solid rgba(168,85,247,0.32);
border-left:4px solid #A855F7;
border-radius:12px;
padding:10px;
margin-top:10px;
font-size:13px;
color:white;
">
<b>ANR Audit</b><br>
One-way relations: {len(one_way_df)}<br>
Missing targets: {len(missing_ncell_df)}
</div>
""", unsafe_allow_html=True)
#-----------------------------------------
##### Map Layer
#------------------------------------------
st.sidebar.markdown("""
<div style="
background: linear-gradient(
135deg,
rgba(16,185,129,0.25),
rgba(5,150,105,0.15)
);
border-left: 4px solid #10B981;
border-radius: 12px;
padding: 12px;
margin-top: 15px;
margin-bottom: 10px;
font-weight: 600;
color: white;
">
🟢 Map Layer
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
show_sites = st.sidebar.checkbox(
    "Site Markers",
    value=True
)
show_shells = st.sidebar.checkbox(
    "RF Shells",
    value=False
)
show_site_labels = st.sidebar.checkbox(
    "Site Labels",
    value=False
)

show_cell_labels = st.sidebar.checkbox(
    "Cell Labels",
    value=False
)

# ==================================
# SITE MARKER COLOR MODE
# ==================================

color_mode = st.sidebar.selectbox(
    "Color Mode",
    [
        "None",
        "Technology",
        "TAC",
        "Cluster",
        "Vendor"
    ],
    index=1
)

# ==========================================
# SPECIAL SITES
# ==========================================

st.sidebar.markdown("""
<div style="
background: linear-gradient(
135deg,
rgba(16,185,129,0.25),
rgba(5,150,105,0.15)
);
border-left: 4px solid #10B981;
border-radius: 12px;
padding: 12px;
margin-top: 15px;
margin-bottom: 10px;
font-weight: 600;
color: white;
">
SPECIAL SITES
</div>
""", unsafe_allow_html=True)

show_hospitals = st.sidebar.checkbox(
    "Hospitals",
    value=False
)

show_police = st.sidebar.checkbox(
    "Police",
    value=False
)

show_fire = st.sidebar.checkbox(
    "Fire Stations",
    value=False
)

show_events = st.sidebar.checkbox(
    "Special Events",
    value=False
)

show_roaming = st.sidebar.checkbox(
    "National Roaming",
    value=False
)

show_stores = st.sidebar.checkbox(
    "Operator Stores",
    value=False
)

show_hubs = st.sidebar.checkbox(
    "Hub Sites",
    value=False
)

# ---------------------------------
# TECHNOLOGY
# ---------------------------------
tech_list = df["Technology"].unique().tolist()

# =====================================================
# TECHNOLOGY FILTER
# =====================================================

st.sidebar.markdown(
    """
    <div class="sidebar-header">
    📡 TECHNOLOGY
    </div>
    """,
    unsafe_allow_html=True
)

tech_options = sorted(
    df["Technology"]
    .dropna()
    .astype(str)
    .unique()
)

selected_tech = st.sidebar.multiselect(
    "",
    tech_options,
    default=tech_options,
    key="technology_filter"
)
# =====================================================
# VENDOR FILTER
# =====================================================

st.sidebar.markdown("""
<div class="sidebar-header">
🏭 VENDOR
</div>
""", unsafe_allow_html=True)

vendor_options = sorted(
    df["VENDOR"]
    .dropna()
    .astype(str)
    .unique()
)

selected_vendors = st.sidebar.multiselect(
    "",
    vendor_options,
    default=vendor_options,
    key="vendor_filter"
)

# =====================================================
# OPERATOR FILTER
# =====================================================

st.sidebar.markdown("""
<div class="sidebar-header">
📶 OPERATOR
</div>
""", unsafe_allow_html=True)

operator_options = sorted(
    df["Operator"]
    .dropna()
    .astype(str)
    .unique()
)

selected_operators = st.sidebar.multiselect(
    "",
    operator_options,
    default=operator_options,
    key="operator_filter"
)

# =====================================================
# MIMO FILTER
# =====================================================

st.sidebar.markdown("""
<div class="sidebar-header">
📡 MIMO
</div>
""", unsafe_allow_html=True)

mimo_options = sorted(
    df["TXRX_MODE"]
    .dropna()
    .astype(str)
    .unique()
)

selected_mimo = st.sidebar.multiselect(
    "",
    mimo_options,
    default=mimo_options,
    key="mimo_filter"
)

# =====================================================
# TAC FILTER
# =====================================================

st.sidebar.markdown("""
<div class="sidebar-header">
🌐 TAC
</div>
""", unsafe_allow_html=True)

tac_options = sorted(
    df["TAC"]
    .dropna()
    .astype(str)
    .unique()
)

selected_tac = st.sidebar.multiselect(
    "",
    tac_options,
    default=tac_options,
    key="tac_filter"
)

# =====================================================
# CLUSTER FILTER
# =====================================================

st.sidebar.markdown("""
<div class="sidebar-header">
📍 CLUSTER
</div>
""", unsafe_allow_html=True)

cluster_options = sorted(
    df["CLUSTER_AREA"]
    .dropna()
    .astype(str)
    .unique()
)

selected_cluster = st.sidebar.multiselect(
    "",
    cluster_options,
    default=cluster_options,
    key="cluster_filter"
)
# ==========================================
# ACTIVE CELL ENGINE (UPDATED)
# ==========================================
active_site = st.session_state.get(
    "last_clicked_site",
    None
)

active_cell = st.session_state.get(
    "last_clicked_cell",
    None
)
# ==========================================
# FOCUS / RESET
# ==========================================
st.sidebar.markdown(
    "<div style='margin-top:40px'></div>",
    unsafe_allow_html=True
)
target_site = st.sidebar.text_input(
    "🔍 Quick Find",
    placeholder="Site or Cell Name..."
)

col1, col2 = st.sidebar.columns(2)

with col1:

    if st.button(
        "🎯 Focus",
        use_container_width=True
    ):

        match = df[
            (
                df["SITE_NAME"].astype(str).str.contains(
                    target_site,
                    case=False,
                    na=False
                )
            )
            |
            (
                df["CELL_NAME"].astype(str).str.contains(
                    target_site,
                    case=False,
                    na=False
                )
            )
        ]

        if not match.empty:

            st.session_state.focus_lat = match.iloc[0]["LATITUDE"]
            st.session_state.focus_lon = match.iloc[0]["LONGITUDE"]
            st.session_state.zoom_level = 16

            st.rerun()

with col2:

    if st.button(
        "🔄 Reset",
        use_container_width=True
    ):

        st.session_state.focus_lat = df["LATITUDE"].mean()
        st.session_state.focus_lon = df["LONGITUDE"].mean()
        st.session_state.zoom_level = 12

        st.rerun()

st.sidebar.markdown("""
<div style="
background: linear-gradient(
135deg,
rgba(239,68,68,0.28),
rgba(127,29,29,0.16)
);
border-left: 4px solid #EF4444;
border-top: 1px solid rgba(239,68,68,0.38);
border-right: 1px solid rgba(239,68,68,0.24);
border-bottom: 1px solid rgba(239,68,68,0.24);
border-radius: 12px;
padding: 12px;
margin-top: 16px;
margin-bottom: 10px;
font-weight: 700;
color: white;
box-shadow: 0 0 18px rgba(239,68,68,0.10);
">
WORST CELL ANALYSIS
</div>
""", unsafe_allow_html=True)

worst_cell_text = st.sidebar.text_area(
    "Paste Worst Cell IDs",
    placeholder="S115-L07-1-A\nS115-L07-2-B\nS259-L07-3-C",
    height=130,
    key="worst_cell_input"
)

st.session_state.worst_cell_text = worst_cell_text
worst_cell_names = parse_cell_list(worst_cell_text)
worst_cell_keys = {cell.upper() for cell in worst_cell_names}

worst_match_df = df[
    df["CELL_NAME"].astype(str).str.upper().isin(worst_cell_keys)
].copy()

st.sidebar.caption(
    f"Loaded: {len(worst_cell_names)} | Matched: {len(worst_match_df)}"
)

wc_col1, wc_col2 = st.sidebar.columns(2)

with wc_col1:
    if st.button("Center Worst", use_container_width=True):
        if not worst_match_df.empty:
            st.session_state.focus_lat = worst_match_df["LATITUDE"].mean()
            st.session_state.focus_lon = worst_match_df["LONGITUDE"].mean()
            st.session_state.zoom_level = 13
            st.rerun()

with wc_col2:
    st.button(
        "Clear Worst",
        use_container_width=True,
        on_click=clear_worst_cells
    )

export_columns = [
    "SITE_NAME",
    "CELL_NAME",
    "LATITUDE",
    "LONGITUDE",
    "Technology",
    "CARRIER",
    "VENDOR",
    "CLUSTER_AREA",
    "TAC",
    "PCI",
]
available_export_columns = [
    col for col in export_columns if col in worst_match_df.columns
]

if not worst_match_df.empty and available_export_columns:
    worst_export_csv = (
        worst_match_df[available_export_columns]
        .sort_values("CELL_NAME")
        .to_csv(index=False)
    )
    st.sidebar.download_button(
        "Download Worst CSV",
        data=worst_export_csv,
        file_name="automationpark_worst_cells.csv",
        mime="text/csv",
        use_container_width=True
    )
# --- 3. FILTERING & LAYERS ---
df_filtered = df[
    (df["Technology"].astype(str).isin(selected_tech))
    &
    (df["VENDOR"].astype(str).isin(selected_vendors))
    &
    (df["Operator"].astype(str).isin(selected_operators))
    &
    (df["TXRX_MODE"].astype(str).isin(selected_mimo))
    &
    (df["TAC"].astype(str).isin(selected_tac))
    &
    (df["CLUSTER_AREA"].astype(str).isin(selected_cluster))
]

if worst_cell_names and not worst_match_df.empty:
    df_filtered = (
        pd.concat([df_filtered, worst_match_df], ignore_index=False)
        .drop_duplicates(subset=["CELL_NAME"])
    )

selected_cell_keys = {
    str(cell).strip().upper()
    for cell in st.session_state.selected_cells
}

selected_cells_df = df[
    df["CELL_NAME"].astype(str).str.upper().isin(selected_cell_keys)
].copy()

if st.session_state.selected_cells and not selected_cells_df.empty:
    df_filtered = (
        pd.concat([df_filtered, selected_cells_df], ignore_index=False)
        .drop_duplicates(subset=["CELL_NAME"])
    )

# ==================================
# FREQUENCY FILTER
# ==================================

freq_mask = pd.Series(
    False,
    index=df_filtered.index
)

if show_L07:
    freq_mask |= (
        df_filtered["CELL_NAME"]
        .str.contains(
            "L07",
            na=False
        )
    )

if show_L18:
    freq_mask |= (
        df_filtered["CELL_NAME"]
        .str.contains(
            "L18",
            na=False
        )
    )

if show_L21:
    freq_mask |= (
        df_filtered["CELL_NAME"]
        .str.contains(
            "L21",
            na=False
        )
    )

if show_NR07:
    freq_mask |= (
        df_filtered["CELL_NAME"]
        .str.contains(
            "NR07",
            na=False
        )
    )

if show_NR23:
    freq_mask |= (
        df_filtered["CELL_NAME"]
        .str.contains(
            "NR23",
            na=False
        )
    )

if show_N35:
    freq_mask |= (
        df_filtered["CELL_NAME"]
        .str.contains(
            "N35",
            na=False
        )
    )

# ==================================
# APPLY FREQUENCY FILTER
# ==================================

df_filtered = df_filtered[
    freq_mask
]

coverage_map_df = pd.DataFrame()
coverage_shell_values = {}

if (
    "coverage_dt_df" in st.session_state
    and st.session_state.coverage_kpi_column
):
    coverage_map_df = build_kpi_map_df(
        st.session_state.coverage_dt_df,
        df,
        st.session_state.coverage_kpi_column
    )

    if not coverage_map_df.empty:
        visible_cell_keys = {
            str(cell).upper()
            for cell in df_filtered["CELL_NAME"].astype(str)
        }
        coverage_map_df = coverage_map_df[
            coverage_map_df["CELL_NAME"].astype(str).str.upper().isin(visible_cell_keys)
        ].copy()

        coverage_shell_values = (
            coverage_map_df
            .groupby(coverage_map_df["CELL_NAME"].astype(str).str.upper())["KPI_VALUE"]
            .mean()
            .to_dict()
        )

# ==================================
# ACTIVE SELECTIONS
# ==================================

active_cell = st.session_state.get(
    "last_clicked_cell",
    None
)
# ==================================
# ACTIVE CELL LOOKUP
# ==================================

selected_row = None

if active_cell:

    match = df_filtered[
        df_filtered["CELL_NAME"].astype(str)
        ==
        str(active_cell)
    ]

    if not match.empty:

        selected_row = match.iloc[0]

current_clicked_cell = None
if selected_row is not None:
    current_clicked_cell = str(selected_row["CELL_NAME"]).strip()

st.sidebar.markdown("""
<div class="ap-selection-card">
<b>GIS Selection Toolbox</b><br>
Turn mode ON. First click sets Cell-A, next clicks add target NCells.
</div>
""", unsafe_allow_html=True)

st.session_state.selection_mode = st.sidebar.toggle(
    "Selection Mode",
    value=st.session_state.selection_mode,
    help="When ON, every clicked RF shell is added to the selected cell list."
)

selection_status_color = "#39D98A" if st.session_state.selection_mode else "#94A3B8"
selection_status_text = "ACTIVE - click cells to collect" if st.session_state.selection_mode else "OFF - map click focuses"
st.sidebar.markdown(f"""
<div class="ap-selection-status" style="
border:1px solid {selection_status_color};
color:{selection_status_color};
">
{selection_status_text}
</div>
""", unsafe_allow_html=True)

sel_col1, sel_col2 = st.sidebar.columns(2)

with sel_col1:
    st.button(
        "Add Current",
        use_container_width=True,
        disabled=current_clicked_cell is None,
        on_click=add_selected_cell,
        args=(current_clicked_cell,)
    )

with sel_col2:
    st.button(
        "Clear Selected",
        use_container_width=True,
        on_click=clear_selected_cells
    )

selected_cell_keys = {
    str(cell).strip().upper()
    for cell in st.session_state.selected_cells
}

selected_cells_df = df[
    df["CELL_NAME"].astype(str).str.upper().isin(selected_cell_keys)
].copy()

st.sidebar.caption(
    f"Source: {st.session_state.ncell_source_cell or '-'} | Targets: {len(selected_cells_df)}"
)

if st.session_state.selected_cells:
    selected_preview = ", ".join(st.session_state.selected_cells[:8])
    if len(st.session_state.selected_cells) > 8:
        selected_preview += ", ..."
    st.sidebar.caption(selected_preview)

ncell_export_df = build_ncell_export(
    st.session_state.ncell_source_cell,
    st.session_state.selected_cells,
    df,
    bidirectional=True
)

if not ncell_export_df.empty:
    ncell_export_csv = ncell_export_df.to_csv(index=False)

    st.sidebar.markdown("""
<div style="
background:linear-gradient(135deg, rgba(245,184,75,0.20), rgba(120,53,15,0.10));
border:1px solid rgba(245,184,75,0.42);
border-left:4px solid #F5B84B;
border-radius:12px;
padding:10px;
margin-top:10px;
margin-bottom:8px;
font-size:13px;
color:white;
">
<b>Export Ready</b><br>
NCell relation list is ready for CSV export.
</div>
""", unsafe_allow_html=True)

    st.sidebar.download_button(
        "Download NCell CSV",
        data=ncell_export_csv,
        file_name="automationpark_visual_ncells.csv",
        mime="text/csv",
        use_container_width=True
    )

# ==================================
# ACTIVE SITE LOOKUP
# ==================================

selected_site_row = None

if active_site:

    site_match = df_filtered[
        df_filtered["SITE_NAME"].astype(str)
        ==
        str(active_site)
    ]

    if not site_match.empty:

        selected_site_row = site_match.iloc[0]
# ==================================
# MAP LAYERS
# ==================================

layers = []

if (
    not coverage_map_df.empty
    and st.session_state.get("coverage_display_mode") in {"Heatmap + cell shells", "Heatmap only"}
):
    heatmap_df = coverage_map_df.copy()
    heatmap_df["HEATMAP_WEIGHT"] = heatmap_df["KPI_ABS_WEIGHT"].clip(lower=0)

    layers.append(
        pdk.Layer(
            "HeatmapLayer",
            heatmap_df,
            id="coverage-kpi-heatmap",
            get_position="[LONGITUDE, LATITUDE]",
            get_weight="HEATMAP_WEIGHT",
            radius_pixels=st.session_state.get("coverage_heatmap_radius", 42),
            intensity=st.session_state.get("coverage_heatmap_intensity", 1.2),
            threshold=0.05,
            aggregation="SUM",
            color_range=[
                [16, 185, 129, 35],
                [34, 211, 238, 80],
                [59, 130, 246, 120],
                [245, 158, 11, 160],
                [239, 68, 68, 220],
            ],
            pickable=True,
        )
    )

# =====================================================
# LABEL POSITION ENGINE
# =====================================================

label_df = df_filtered.copy()
label_df["LABEL_DISTANCE"] = 0.0023

label_df.loc[
    label_df["CELL_NAME"].str.contains("L07", na=False),
    "LABEL_DISTANCE"
] = 0.0024

label_df.loc[
    label_df["CELL_NAME"].str.contains("L18", na=False),
    "LABEL_DISTANCE"
] = 0.0019

label_df.loc[
    label_df["CELL_NAME"].str.contains("N35", na=False),
    "LABEL_DISTANCE"
] = 0.0014

label_df["LABEL_LAT"] = (
    label_df["LATITUDE"]
    + label_df["LABEL_DISTANCE"]
    * np.cos(
        np.radians(label_df["AZIMUTH"])
    )
)

label_df["LABEL_LON"] = (
    label_df["LONGITUDE"]
    + label_df["LABEL_DISTANCE"]
    * np.sin(
        np.radians(label_df["AZIMUTH"])
    )
)
shell_df = pd.DataFrame()
shell_lookup = {}

# =====================================================
# RF SHELLS V6.1
# =====================================================

if show_shells and not df_filtered.empty:

    shell_df = build_shell_cache(df_filtered)

    shell_df["line_width"] = 1

    shell_display_mode = st.session_state.get("coverage_display_mode", "")

    if (
        coverage_shell_values
        and shell_display_mode in {"Heatmap + cell shells", "Cell shells only"}
        and not shell_df.empty
    ):
        kpi_values = list(coverage_shell_values.values())
        kpi_min = min(kpi_values)
        kpi_max = max(kpi_values)
        reverse_scale = st.session_state.get("coverage_reverse_scale", False)

        for shell_index, shell_row in shell_df.iterrows():
            cell_key = str(shell_row["CELL_NAME"]).upper()
            if cell_key not in coverage_shell_values:
                continue

            kpi_value = coverage_shell_values[cell_key]
            color = kpi_color(kpi_value, kpi_min, kpi_max, reverse=reverse_scale)
            shell_df.at[shell_index, "fill_color"] = color
            shell_df.at[shell_index, "line_color"] = color[:3]
            shell_df.at[shell_index, "line_width"] = 4

    top_search_cell_keys = {
        str(cell).strip().upper()
        for cell in st.session_state.get("top_search_cells", [])
        if str(cell).strip()
    }

    if top_search_cell_keys and not shell_df.empty:
        top_search_mask = shell_df["CELL_NAME"].astype(str).str.upper().isin(top_search_cell_keys)
        shell_df.loc[top_search_mask, "fill_color"] = shell_df.loc[top_search_mask, "fill_color"].apply(
            lambda _: [34, 211, 238, 85]
        )
        shell_df.loc[top_search_mask, "line_color"] = shell_df.loc[top_search_mask, "line_color"].apply(
            lambda _: [34, 211, 238]
        )
        shell_df.loc[top_search_mask, "line_width"] = 4

    if selected_cell_keys and not shell_df.empty:
        selected_mask = shell_df["CELL_NAME"].astype(str).str.upper().isin(selected_cell_keys)
        shell_df.loc[selected_mask, "fill_color"] = shell_df.loc[selected_mask, "fill_color"].apply(
            lambda _: [245, 184, 75, 80]
        )
        shell_df.loc[selected_mask, "line_color"] = shell_df.loc[selected_mask, "line_color"].apply(
            lambda _: [245, 184, 75]
        )
        shell_df.loc[selected_mask, "line_width"] = 4

    if st.session_state.ncell_source_cell and not shell_df.empty:
        source_mask = (
            shell_df["CELL_NAME"].astype(str).str.upper()
            ==
            str(st.session_state.ncell_source_cell).upper()
        )
        shell_df.loc[source_mask, "fill_color"] = shell_df.loc[source_mask, "fill_color"].apply(
            lambda _: [255, 0, 0, 105]
        )
        shell_df.loc[source_mask, "line_color"] = shell_df.loc[source_mask, "line_color"].apply(
            lambda _: [255, 0, 0]
        )
        shell_df.loc[source_mask, "line_width"] = 5

    if worst_cell_keys and not shell_df.empty:
        worst_mask = shell_df["CELL_NAME"].astype(str).str.upper().isin(worst_cell_keys)
        shell_df.loc[worst_mask, "fill_color"] = shell_df.loc[worst_mask, "fill_color"].apply(
            lambda _: [255, 0, 0, 90]
        )
        shell_df.loc[worst_mask, "line_color"] = shell_df.loc[worst_mask, "line_color"].apply(
            lambda _: [255, 0, 0]
        )
        shell_df.loc[worst_mask, "line_width"] = 4

    shell_df["tooltip_text"] = shell_df["CELL_NAME"].astype(str)

    shell_render_df = shell_df[
[
    "CELL_NAME",
    "polygon",
    "line_color"

    ]
    ].copy()

    shell_lookup = {}

    for _, row in shell_df.iterrows():

        shell_lookup[
            str(row["CELL_NAME"])
        ] = row

    layers.append(

        pdk.Layer(

            "PolygonLayer",

            shell_df,

            id="rf-shells",  # <--- Ensure this is unique

            get_polygon="polygon",

            get_fill_color="fill_color",

            get_line_color="line_color",

            get_line_width="line_width",

            line_width_min_pixels=1,

            stroked=True,

            filled=True,

            pickable=True

        )

    )

# =====================================================
# SELECTED CELL PREDICTED COVERAGE V1
# =====================================================

if st.session_state.get("show_predicted_coverage") and st.session_state.get("predicted_coverage_cell"):
    predicted_match = df[
        df["CELL_NAME"].astype(str).str.upper()
        ==
        str(st.session_state.predicted_coverage_cell).upper()
    ]

    if not predicted_match.empty:
        predicted_shell_row = shell_lookup.get(str(st.session_state.predicted_coverage_cell))
        predicted_coverage_df = build_predicted_coverage(
            predicted_match.iloc[0],
            predicted_shell_row
        )

        if not predicted_coverage_df.empty:
            layers.append(
                pdk.Layer(
                    "PolygonLayer",
                    predicted_coverage_df,
                    id="predicted-coverage-fan",
                    get_polygon="polygon",
                    get_fill_color="fill_color",
                    get_line_color="line_color",
                    get_line_width=2,
                    line_width_min_pixels=2,
                    stroked=True,
                    filled=True,
                    pickable=True,
                )
            )

    visual_ncell_lines = []
    source_cell = st.session_state.ncell_source_cell

    if source_cell and source_cell in shell_lookup:
        src = shell_lookup[source_cell]

        for target_cell in st.session_state.selected_cells:
            if target_cell not in shell_lookup:
                continue

            tgt = shell_lookup[target_cell]
            relation_type = get_relation_type(source_cell, target_cell, df)
            selected_link = st.session_state.get("selected_ncell_link") or {}
            is_selected_link = (
                selected_link.get("source") == source_cell
                and selected_link.get("target") == target_cell
            )
            visual_ncell_lines.append({
                "path": [
                    [src["TIP_LON"], src["TIP_LAT"]],
                    [tgt["TIP_LON"], tgt["TIP_LAT"]],
                ],
                "color": [255, 40, 40] if not is_selected_link else [245, 184, 75],
                "hit_color": [0, 0, 0],
                "line_width": 5 if is_selected_link else 2,
                "source": source_cell,
                "target": target_cell,
                "relation_type": relation_type,
                "tooltip_text": f"{source_cell} <--> {target_cell} {relation_type} NCell",
            })

    if visual_ncell_lines:
        visual_ncell_df = pd.DataFrame(visual_ncell_lines)
        layers.append(
            pdk.Layer(
                "PathLayer",
                visual_ncell_df,
                id="visual-ncell-builder-hitbox",
                get_path="path",
                get_color="hit_color",
                opacity=0,
                width_scale=1,
                width_min_pixels=18 if st.session_state.get("los_select_mode") else 10,
                pickable=st.session_state.get("los_select_mode"),
            )
        )
        layers.append(
            pdk.Layer(
                "PathLayer",
                visual_ncell_df,
                id="visual-ncell-builder-lines",
                get_path="path",
                get_color="color",
                get_width="line_width",
                width_scale=1,
                width_min_pixels=2,
                pickable=True,
            )
        )
# ===================================================
# SITE MARKERS
# ===================================================

# ===================================================
# SITE MARKERS COLOR ENGINE
# ===================================================

site_df = (
    df_filtered
    .drop_duplicates(subset=["SITE_NAME"])
    .copy()
)

site_df["R"] = 120
site_df["G"] = 120
site_df["B"] = 120

# ==================================
# CLUSTER MODE
# ==================================

if color_mode == "Cluster":

    colors = {

        "CLUST-1":[0,255,0],
        "CLUST-2":[0,120,255],
        "CLUST-3":[255,180,0],
        "CLUST-4":[255,0,255]

    }

    for value, color in colors.items():

        site_df.loc[
            site_df["CLUSTER_AREA"].astype(str) == value,
            ["R","G","B"]
        ] = color

# ==================================
# TAC MODE
# ==================================

elif color_mode == "TAC":

    colors = {

        "1000":[0,255,0],
        "2000":[0,120,255],
        "3000":[255,180,0],
        "4000":[255,0,255]

    }

    for value, color in colors.items():

        site_df.loc[
            site_df["TAC"].astype(str) == value,
            ["R","G","B"]
        ] = color

# ==================================
# VENDOR MODE
# ==================================

elif color_mode == "Vendor":

    colors = {

        "VEND-1":[0,255,0],
        "VEND-2":[0,120,255],
        "VEND-3":[255,180,0],
        "VEND-4":[255,0,255]

    }

    for value, color in colors.items():

        site_df.loc[
            site_df["VENDOR"].astype(str) == value,
            ["R","G","B"]
        ] = color

# ==================================
# MIMO MODE
# ==================================
elif color_mode == "MIMO":

    colors = {

        "2T2R":[255,0,255],
        "4T2R":[0,255,0],
        "4T4R":[0,120,255]

    }

    for value, color in colors.items():

        site_df.loc[
            site_df["TXRX_MODE"].astype(str) == value,
            ["R","G","B"]
        ] = color


# ==================================
# TECHNOLOGY MODE
# ==================================
elif color_mode == "Technology":

    colors = {

        "4G":[0,255,0],
        "5G":[255,0,255],
        "LTE":[0,120,255]

    }

    for value, color in colors.items():

        site_df.loc[
            site_df["Technology"].astype(str) == value,
            ["R","G","B"]
        ] = color
# 3. NOW check the checkbox before adding the layer

# ===================================================
# SITE MARKERS
# ===================================================

if show_sites:

    layers.append(

        pdk.Layer(

            "ScatterplotLayer",

            site_df,

            id="site-markers",

            get_position=["LONGITUDE", "LATITUDE"],

            get_radius=300,

            get_fill_color=["R", "G", "B"],

            pickable=True,

            opacity=0.3

        )

    )
# =====================================================
# SITE LABELS
# =====================================================

if show_site_labels and not site_df.empty:
    layers.append(
        pdk.Layer(
            "TextLayer",
            data=site_df,
            id="site-labels",
            get_position=["LONGITUDE", "LATITUDE"],
            get_text="SITE_NAME",
            get_size=16,
            get_color=[255, 255, 255],
            get_angle=0,
            pickable=False,
        )
    )
# =====================================================
# SPECIAL SITES LAYERS
# =====================================================

if show_hospitals:

    hospital_df = special_sites_df[
        special_sites_df["TYPE"] == "Hospital"
    ]

    layers.append(

        pdk.Layer(

            "ScatterplotLayer",

            hospital_df,

            get_position='[LON, LAT]',

            get_fill_color=[255,0,0],

            get_radius=45,

            pickable=True

        )

    )

if show_police:

    police_df = special_sites_df[
        special_sites_df["TYPE"] == "Police"
    ]

    layers.append(

        pdk.Layer(

            "ScatterplotLayer",

            police_df,

            get_position='[LON, LAT]',

            get_fill_color=[0,120,255],

            get_radius=45,

            pickable=True

        )

    )

if show_events:

    event_df = special_sites_df[
        special_sites_df["TYPE"] == "Event"
    ]

    layers.append(

        pdk.Layer(

            "ScatterplotLayer",

            event_df,

            get_position='[LON, LAT]',

            get_fill_color=[255,165,0],

            get_radius=45,

            pickable=True

        )

    )

if show_roaming:

    roaming_df = special_sites_df[
        special_sites_df["TYPE"] == "Roaming"
    ]

    layers.append(

        pdk.Layer(

            "ScatterplotLayer",

            roaming_df,

            get_position='[LON, LAT]',

            get_fill_color=[255,0,255],

            get_radius=45,

            pickable=True

        )

    )

if st.session_state.get("map_pins"):
    pins_df = pd.DataFrame(st.session_state.map_pins).drop_duplicates(subset=["NAME", "LAT", "LON"])

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            pins_df,
            id="engineering-pins",
            get_position="[LON, LAT]",
            get_fill_color=[245, 184, 75],
            get_line_color=[255, 255, 255],
            get_radius=85,
            stroked=True,
            line_width_min_pixels=2,
            pickable=True,
        )
    )

    layers.append(
        pdk.Layer(
            "TextLayer",
            pins_df,
            id="engineering-pin-labels",
            get_position="[LON, LAT]",
            get_text="NAME",
            get_size=13,
            get_color=[255, 255, 255],
            get_pixel_offset=[0, -18],
            pickable=False,
        )
    )
# =====================================================
# CELL LABELS
# =====================================================

if show_cell_labels:

    label_df = df_filtered.copy()

    label_df.loc[
        label_df["CELL_NAME"].str.contains("-A", na=False),
        "AZIMUTH"
    ] = 0

    label_df.loc[
        label_df["CELL_NAME"].str.contains("-B", na=False),
        "AZIMUTH"
    ] = 120

    label_df.loc[
        label_df["CELL_NAME"].str.contains("-C", na=False),
        "AZIMUTH"
    ] = 240

    label_df["LABEL_DISTANCE"] = 0.0023

    label_df.loc[
        label_df["CELL_NAME"].str.contains("L07", na=False),
        "LABEL_DISTANCE"
    ] = 0.0018

    label_df.loc[
        label_df["CELL_NAME"].str.contains("L18", na=False),
        "LABEL_DISTANCE"
    ] = 0.0014

    label_df.loc[
        label_df["CELL_NAME"].str.contains("N35", na=False),
        "LABEL_DISTANCE"
    ] = 0.0008

    label_df["LABEL_LAT"] = (
        label_df["LATITUDE"]
        + label_df["LABEL_DISTANCE"]
        * np.cos(np.radians(label_df["AZIMUTH"]))
    )

    label_df["LABEL_LON"] = (
        label_df["LONGITUDE"]
        + label_df["LABEL_DISTANCE"]
        * np.sin(np.radians(label_df["AZIMUTH"]))
    )

    # =====================================
    # LABEL TEXT
    # =====================================

    label_df["LABEL_TEXT"] = (
        label_df["CELL_NAME"]
        .str.extract(
            r"(L07|L18|L21|N35|NR07|NR23)",
            expand=False
        )
    )

    label_df["LABEL_TEXT"] = (
        label_df["LABEL_TEXT"]
        .replace({
            "L07": "700",
            "L18": "1800",
            "L21": "2100",
            "N35": "3500",
            "NR07": "700",
            "NR23": "2300"
        })
    )

    layers.append(

        pdk.Layer(

            "TextLayer",

            label_df,

            get_position=[
                "LABEL_LON",
                "LABEL_LAT"
            ],

            get_text="LABEL_TEXT",

            get_size=15,

            get_color=[
                0,
                255,
                255
            ],

            get_angle=0

        )

    )
# =====================================================
# NCELL TIP POINTS
# =====================================================

tip_df = df_filtered.copy()

tip_df["TIP_LAT"] = (
    tip_df["LATITUDE"]
    + 0.0025
    * np.cos(
        np.radians(
            tip_df["AZIMUTH"]
        )
    )
)

tip_df["TIP_LON"] = (
    tip_df["LONGITUDE"]
    + 0.0025
    * np.sin(
        np.radians(
            tip_df["AZIMUTH"]
        )
    )
)
lookup = shell_lookup
ncell_lines = []
nbr_df_filtered = pd.DataFrame()
# ==========================================
# NCELL DISPLAY LIMIT
# ==========================================

max_ncells = st.sidebar.slider(
    "Max NCell Display",
    min_value=5,
    max_value=300,
    value=25,
    step=1
)
# ==========================================
# SELECTED CELL FILTER
# ==========================================

if active_cell == "None":
    nbr_df_filtered = pd.DataFrame()

else:
    nbr_df_filtered = nbr_df[
        (
            nbr_df["source_sector"] == active_cell
        )
        |
        (
            nbr_df["target_sector"] == active_cell
        )
    ].copy()

    nbr_df_filtered = nbr_df_filtered.head(max_ncells)

    # ==========================================
    # ANR STATISTICS
    # ==========================================

    if active_cell != "All":
        incoming_count = len(
            nbr_df_filtered[
                nbr_df_filtered["target_sector"] == active_cell
            ]
        )

        outgoing_count = len(
            nbr_df_filtered[
                nbr_df_filtered["source_sector"] == active_cell
            ]
        )

    # ==========================================
    # NCELL LINE CREATION
    # ==========================================

    allowed_relations = []

    if show_intrafreq:
        allowed_relations.append("IntraFreq")

    if show_interfreq:
        allowed_relations.append("InterFreq")

    if show_irat:
        allowed_relations.append("IRAT")

    if allowed_relations:
        nbr_df_filtered = nbr_df_filtered[
            nbr_df_filtered["relation_type"].astype(str).isin(allowed_relations)
        ]
    else:
        nbr_df_filtered = nbr_df_filtered.iloc[0:0]

    for _, nbr in nbr_df_filtered.iterrows():
        relation = str(nbr["relation_type"])

        source = str(nbr["source_sector"])
        target = str(nbr["target_sector"])

        if (
            source not in lookup
            or target not in lookup
        ):
            continue

        src = lookup[source]
        tgt = lookup[target]

        src_lat = src["TIP_LAT"]
        src_lon = src["TIP_LON"]

        tgt_lat = tgt["TIP_LAT"]
        tgt_lon = tgt["TIP_LON"]

        # ======================================
        # LINE COLOR
        # ======================================

        if relation == "IntraFreq":
            line_color = [0, 255, 0]

        elif relation == "InterFreq":
            line_color = [255, 255, 0]

        elif relation == "IRAT":
            line_color = [255, 0, 255]

        else:
            line_color = [0, 255, 255]

        selected_link = st.session_state.get("selected_ncell_link") or {}
        is_selected_link = (
            selected_link.get("source") == source
            and selected_link.get("target") == target
        )

        if is_selected_link:
            line_color = [245, 184, 75]

        # ======================================
        # ADD LINE
        # ======================================

        ncell_lines.append({
            "path": [
                [src_lon, src_lat],
                [tgt_lon, tgt_lat],
            ],
            "color": line_color,
            "hit_color": [0, 0, 0],
            "line_width": 5 if is_selected_link else 2,
            "source": source,
            "target": target,
            "relation_type": relation,
            "tooltip_text": f"{source} <--> {target} {relation} NCell",
        })

    # ==========================================
    # DRAW LINES
    # ==========================================

    if show_ncells and len(ncell_lines) > 0:
        ncell_df = pd.DataFrame(ncell_lines)

        layers.append(
            pdk.Layer(
                "PathLayer",
                ncell_df,
                id="ncell-line-hitbox",
                get_path="path",
                get_color="hit_color",
                opacity=0,
                width_scale=1,
                width_min_pixels=18 if st.session_state.get("los_select_mode") else 10,
                pickable=st.session_state.get("los_select_mode"),
            )
        )

        layers.append(
            pdk.Layer(
                "PathLayer",
                ncell_df,
                id="ncell-lines",
                get_path="path",
                get_color="color",
                get_width="line_width",
                width_scale=1,
                width_min_pixels=2,
                pickable=True,
            )
        )

# =====================================================
# RENDER ENGINE (CALLBACK APPROACH)
# =====================================================

def on_map_click():

    event = st.session_state.get("map_key")

    if not event:
        return

    # ==========================================
    # CELL CLICK
    # ==========================================

    try:

        if "rf-shells" in event["selection"]["objects"]:

            obj = event["selection"]["objects"]["rf-shells"][0]

            st.session_state.last_clicked_cell = obj["CELL_NAME"]
            if st.session_state.get("show_predicted_coverage", False):
                st.session_state.predicted_coverage_cell = obj["CELL_NAME"]
            if st.session_state.get("selection_mode", False):
                add_selected_cell(obj["CELL_NAME"])

    except Exception:
        pass

    # ==========================================
    # NCELL / LOS LINE CLICK
    # ==========================================

    try:
        selected_objects = event["selection"]["objects"]
        line_obj = None

        if "ncell-line-hitbox" in selected_objects and selected_objects["ncell-line-hitbox"]:
            line_obj = selected_objects["ncell-line-hitbox"][0]
        elif "ncell-lines" in selected_objects and selected_objects["ncell-lines"]:
            line_obj = selected_objects["ncell-lines"][0]
        elif (
            "visual-ncell-builder-hitbox" in selected_objects
            and selected_objects["visual-ncell-builder-hitbox"]
        ):
            line_obj = selected_objects["visual-ncell-builder-hitbox"][0]
        elif (
            "visual-ncell-builder-lines" in selected_objects
            and selected_objects["visual-ncell-builder-lines"]
        ):
            line_obj = selected_objects["visual-ncell-builder-lines"][0]

        if line_obj:
            st.session_state.selected_ncell_link = build_link_profile(
                str(line_obj.get("source", "")),
                str(line_obj.get("target", "")),
                str(line_obj.get("relation_type", "")),
                df
            )
            st.session_state.active_top_tool = "terrain_los"

    except Exception:
        pass

    # ==========================================
    # SITE CLICK
    # ==========================================

    try:

        if "site-markers" in event["selection"]["objects"]:

            obj = event["selection"]["objects"]["site-markers"][0]

            st.session_state.last_clicked_site = obj["SITE_NAME"]

    except Exception:
        pass

#===================================================
###Menu 1
#====================================================
menu1, menu2, menu3, menu4, menu5 = st.columns(5)

with menu1:
    st.button(
        "Export To Google Earth",
        use_container_width=True,
        on_click=set_active_top_tool,
        args=("google_earth",)
    )

with menu2:
    st.button(
        "Coverage Layers & DT Log",
        use_container_width=True,
        on_click=set_active_top_tool,
        args=("coverage_dt",)
    )

with menu3:
    st.button(
        "ANR & AUTO NCell LIST Generator",
        use_container_width=True,
        on_click=set_active_top_tool,
        args=("anr_builder",)
    )

with menu4:
    st.button(
        "Reports > Go To Dashboards",
        use_container_width=True,
        on_click=set_active_top_tool,
        args=("reports",)
    )

with menu5:
    st.button(
        "ADMIN & Login",
        use_container_width=True,
        on_click=set_active_top_tool,
        args=("admin",)
    )

active_top_tool = st.session_state.get("active_top_tool")

if active_top_tool:
    st.markdown('<div class="ap-tool-divider"></div>', unsafe_allow_html=True)

    if active_top_tool == "google_earth":
        st.markdown('<div class="ap-tool-title">Google Earth Export</div>', unsafe_allow_html=True)

        export_keys = list(st.session_state.selected_cells)
        if st.session_state.ncell_source_cell:
            export_keys = [st.session_state.ncell_source_cell] + export_keys

        export_key_set = {
            str(cell).strip().upper()
            for cell in export_keys
            if str(cell).strip()
        }
        google_earth_cells_df = df[
            df["CELL_NAME"].astype(str).str.upper().isin(export_key_set)
        ].drop_duplicates(subset=["CELL_NAME"]).copy()

        ge1, ge2, ge3 = st.columns([1, 1, 2])

        with ge1:
            if not google_earth_cells_df.empty:
                st.download_button(
                    "Download Selected Cells KML",
                    data=build_cell_kml(google_earth_cells_df),
                    file_name="automationpark_selected_cells.kml",
                    mime="application/vnd.google-earth.kml+xml",
                    use_container_width=True
                )
            else:
                st.info("Select cells first to export them to Google Earth.")

        with ge2:
            if st.session_state.ncell_source_cell and st.session_state.selected_cells:
                st.download_button(
                    "Download NCell Links KML",
                    data=build_ncell_kml(
                        st.session_state.ncell_source_cell,
                        st.session_state.selected_cells,
                        df
                    ),
                    file_name="automationpark_ncell_links.kml",
                    mime="application/vnd.google-earth.kml+xml",
                    use_container_width=True
                )
            else:
                st.info("Build visual NCell links first to export line KML.")

        with ge3:
            st.markdown(
                '<div class="ap-tool-note">Next stage: import edited Google Earth KML back into GeoMap and convert it to cell/link CSV.</div>',
                unsafe_allow_html=True
            )

    elif active_top_tool == "coverage_dt":
        st.markdown('<div class="ap-tool-title">Coverage Layers & Drive Test Log</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="ap-tool-copy">Upload KPI, coverage, throughput, traffic, VoLTE, RSRP, RSRQ, SINR, or drive-test CSV to render map layers.</div>',
            unsafe_allow_html=True
        )

        uploaded_coverage_file = st.file_uploader(
            "Upload coverage / KPI / drive-test CSV",
            type=["csv"],
            key="coverage_dt_upload"
        )

        if uploaded_coverage_file is not None:
            try:
                coverage_dt_df = pd.read_csv(uploaded_coverage_file)
                st.session_state.coverage_dt_df = coverage_dt_df
                st.success(
                    f"Loaded {len(coverage_dt_df):,} rows and {len(coverage_dt_df.columns):,} columns."
                )
                st.dataframe(coverage_dt_df.head(10), use_container_width=True)
                st.caption("Detected columns: " + ", ".join(map(str, coverage_dt_df.columns[:18])))
                st.rerun()
            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")
        elif "coverage_dt_df" in st.session_state:
            coverage_dt_df = st.session_state.coverage_dt_df
            st.success(
                f"CSV still loaded in session: {len(coverage_dt_df):,} rows."
            )
            st.dataframe(coverage_dt_df.head(5), use_container_width=True)

        if "coverage_dt_df" in st.session_state and not st.session_state.coverage_dt_df.empty:
            coverage_dt_df = st.session_state.coverage_dt_df
            numeric_kpi_columns = get_numeric_columns(coverage_dt_df)

            if numeric_kpi_columns:
                if st.session_state.coverage_kpi_column not in numeric_kpi_columns:
                    st.session_state.coverage_kpi_column = numeric_kpi_columns[0]

                kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns([2, 2, 1, 1])

                with kpi_col1:
                    st.selectbox(
                        "KPI / Counter",
                        numeric_kpi_columns,
                        index=numeric_kpi_columns.index(st.session_state.coverage_kpi_column),
                        key="coverage_kpi_column"
                    )

                with kpi_col2:
                    st.selectbox(
                        "Display",
                        ["Heatmap + cell shells", "Heatmap only", "Cell shells only"],
                        key="coverage_display_mode"
                    )

                with kpi_col3:
                    st.slider(
                        "Radius",
                        min_value=10,
                        max_value=120,
                        key="coverage_heatmap_radius"
                    )

                with kpi_col4:
                    st.slider(
                        "Intensity",
                        min_value=0.2,
                        max_value=5.0,
                        step=0.1,
                        key="coverage_heatmap_intensity"
                    )

                st.checkbox(
                    "Reverse scale: low KPI is worse",
                    key="coverage_reverse_scale"
                )

                preview_kpi_map_df = build_kpi_map_df(
                    coverage_dt_df,
                    df,
                    st.session_state.coverage_kpi_column
                )

                if preview_kpi_map_df.empty:
                    st.warning(
                        "CSV loaded, but GeoMap could not match rows. Use CELL_NAME/CELL_ID or LATITUDE/LONGITUDE columns."
                    )
                else:
                    st.success(
                        f"Ready to render {len(preview_kpi_map_df):,} KPI points/cells on the map."
                    )
                    st.dataframe(
                        preview_kpi_map_df[
                            ["CELL_NAME", "SITE_NAME", "LATITUDE", "LONGITUDE", "KPI_VALUE"]
                        ].head(10),
                        use_container_width=True
                    )
            else:
                st.warning("CSV loaded, but no numeric KPI/counter columns were detected.")

    elif active_top_tool == "anr_builder":
        st.markdown('<div class="ap-tool-title">ANR & NCell Builder</div>', unsafe_allow_html=True)
        anr1, anr2, anr3 = st.columns(3)

        with anr1:
            st.metric("Source Cell-A", st.session_state.ncell_source_cell or "-")
        with anr2:
            st.metric("Selected Targets", len(st.session_state.selected_cells))
        with anr3:
            st.metric("Export Rows", len(ncell_export_df))

        if not ncell_export_df.empty:
            st.download_button(
                "Download Visual NCell CSV",
                data=ncell_export_df.to_csv(index=False),
                file_name="automationpark_visual_ncells.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.dataframe(ncell_export_df.head(20), use_container_width=True)
        else:
            st.info("Turn Selection Mode ON, click Cell-A, then click target cells to build NCell relations.")

    elif active_top_tool == "terrain_los":
        los_title_col, los_close_col = st.columns([5, 1])
        with los_title_col:
            st.markdown('<div class="ap-tool-title">Terrain / LOS Profile</div>', unsafe_allow_html=True)
        with los_close_col:
            if st.button("Close LOS", use_container_width=True, key="close_los_profile"):
                st.session_state.selected_ncell_link = None
                st.session_state.active_top_tool = None
                st.rerun()

        selected_link = st.session_state.get("selected_ncell_link")

        if selected_link:
            los1, los2, los3, los4, los5 = st.columns(5)

            with los1:
                st.metric("Link", f"{selected_link['source']} -> {selected_link['target']}")
            with los2:
                st.metric("NCell Type", selected_link["relation_type"])
            with los3:
                st.metric("Distance", f"{selected_link['distance_km']:.2f} km")
            with los4:
                st.metric("Bearing", f"{selected_link['bearing_deg']:.0f} deg")
            with los5:
                st.metric("Clearance", f"{selected_link['min_clearance_m']:.1f} m")

            st.markdown(f"""
            <div style="
            background:rgba(13,40,76,0.72);
            border:1px solid rgba(34,211,216,0.28);
            border-radius:12px;
            padding:12px 14px;
            margin:8px 0 12px 0;
            color:#F8FAFC;
            ">
                <b>{selected_link['source']}</b> ({selected_link['source_site']})
                &nbsp; &lt;--&gt; &nbsp;
                <b>{selected_link['target']}</b> ({selected_link['target_site']})
                <br>
                Source: {selected_link['source_lat']:.6f}, {selected_link['source_lon']:.6f}
                &nbsp; | &nbsp;
                Target: {selected_link['target_lat']:.6f}, {selected_link['target_lon']:.6f}
                <br>
                <span style="color:{selected_link['los_status_color']};font-weight:900;">
                    {selected_link['los_status']}
                </span>
                &nbsp; - &nbsp; Bearing is calculated from source cell toward target cell.
            </div>
            """, unsafe_allow_html=True)

            profile_df = pd.DataFrame(selected_link["samples"]).set_index("distance_km")
            st.line_chart(profile_df[["terrain_m", "los_m"]], use_container_width=True)
            st.caption(
                "V1 profile: terrain is simulated until real DEM/elevation data is connected. LOS line and distance/bearing are calculated from the selected cells."
            )
        else:
            st.info("Click an NCell line on the map to open the LOS profile.")

    elif active_top_tool == "reports":
        st.markdown('<div class="ap-tool-title">Reports & Dashboards</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="ap-tool-copy">Dashboard launch point for GeoAI reporting pages.</div>',
            unsafe_allow_html=True
        )
        if hasattr(st, "link_button"):
            st.link_button(
                "Open Streamlit Dashboard",
                "http://localhost:8501/Dashboard",
                use_container_width=True
            )
        else:
            st.markdown("[Open Streamlit Dashboard](http://localhost:8501/Dashboard)")

    elif active_top_tool == "admin":
        st.markdown('<div class="ap-tool-title">Admin & Login</div>', unsafe_allow_html=True)
        st.info("Admin/login shell is reserved for Stage 3 user roles, publishing controls, and protected workflows.")


# ====================================================
# MENU 2
# ====================================================

m2_1, gap1, m2_2, gap2, m2_3, gap3, m2_4 = st.columns(
    [3.2,0.25,4.2,0.25,3.2,0.25,3.8]
)

# --------------------------------
# QUICK FIND
# --------------------------------
with m2_1:

    st.markdown("""
    <div class="m2-card">
        Quick Find
    </div>
    """, unsafe_allow_html=True)

    top_quick_query = st.text_input(
        "",
        placeholder="Site / Cell",
        key="top_quick_find_query"
    )

    quick_match_df = find_cells(
        df_filtered,
        top_quick_query,
        ["SITE_NAME", "CELL_NAME"]
    )

    if top_quick_query.strip():
        if not quick_match_df.empty:
            focus_on_rows(quick_match_df.head(1), zoom_level=16)
            st.session_state.top_search_cells = quick_match_df["CELL_NAME"].astype(str).head(80).tolist()
            st.markdown(
                f'<div class="m2-status">{len(quick_match_df):,} match(es). Focused first cell.</div>',
                unsafe_allow_html=True
            )
        else:
            st.session_state.top_search_cells = []
            st.markdown('<div class="m2-status">No matching site or cell.</div>', unsafe_allow_html=True)

# --------------------------------
# GLOBAL SEARCH
# --------------------------------
with m2_2:

    st.markdown("""
    <div class="m2-card">
        Global Search
    </div>
    """, unsafe_allow_html=True)

    global_query = st.text_input(
        "",
        placeholder="PCI / TAC / Vendor / Address",
        key="top_global_search_query"
    )

    global_search_columns = [
        "CELL_NAME", "SITE_NAME", "PCI", "TAC", "VENDOR", "Technology",
        "CARRIER", "CLUSTER_AREA", "OPERATOR", "ADDRESS", "CITY", "REGION"
    ]
    global_match_df = find_cells(df_filtered, global_query, global_search_columns)

    if global_query.strip():
        if not global_match_df.empty:
            focus_on_rows(global_match_df, zoom_level=13 if len(global_match_df) > 1 else 16)
            st.session_state.top_search_cells = global_match_df["CELL_NAME"].astype(str).head(160).tolist()
            st.markdown(
                f'<div class="m2-status">{len(global_match_df):,} result(s). Map centered on results.</div>',
                unsafe_allow_html=True
            )
        else:
            st.session_state.top_search_cells = []
            st.markdown('<div class="m2-status">No global results.</div>', unsafe_allow_html=True)

# --------------------------------
# NAVIGATION
# --------------------------------
with m2_3:

    st.markdown("""
    <div class="m2-card">
        Navigation
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-tool-pad"></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("+", key="zoom_in"):
            st.session_state.zoom_level = min(st.session_state.zoom_level + 1, 20)

    with c2:
        if st.button("-", key="zoom_out"):
            st.session_state.zoom_level = max(st.session_state.zoom_level - 1, 3)

    with c3:
        if st.button("Focus", key="focus_btn"):
            focused = False
            if st.session_state.get("last_clicked_cell"):
                focus_df = df[
                    df["CELL_NAME"].astype(str).str.upper()
                    ==
                    str(st.session_state.last_clicked_cell).upper()
                ]
                focused = focus_on_rows(focus_df.head(1), zoom_level=16)
            elif st.session_state.get("last_clicked_site"):
                focus_df = df[
                    df["SITE_NAME"].astype(str).str.upper()
                    ==
                    str(st.session_state.last_clicked_site).upper()
                ]
                focused = focus_on_rows(focus_df, zoom_level=15)

            if not focused and st.session_state.get("top_search_cells"):
                focus_df = df[
                    df["CELL_NAME"].astype(str).str.upper().isin(
                        {str(cell).upper() for cell in st.session_state.top_search_cells}
                    )
                ]
                focus_on_rows(focus_df, zoom_level=13)

    with c4:
        if st.button("Home", key="home_btn"):
            st.session_state.focus_lat = df["LATITUDE"].mean()
            st.session_state.focus_lon = df["LONGITUDE"].mean()
            st.session_state.zoom_level = 12
            st.session_state.top_search_cells = []

# --------------------------------
# MAP TOOLS
# --------------------------------
with m2_4:

    st.markdown("""
    <div class="m2-card">
        Map Tools
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-tool-pad"></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        los_label = "LOS ON" if st.session_state.get("los_select_mode") else "LOS"
        st.button(
            los_label,
            key="measure_btn",
            on_click=toggle_los_select_mode
        )

    with c2:
        if st.button("Pin", key="marker_btn"):
            pin_added = False
            if st.session_state.get("last_clicked_cell"):
                pin_row = df[
                    df["CELL_NAME"].astype(str).str.upper()
                    ==
                    str(st.session_state.last_clicked_cell).upper()
                ]
                if not pin_row.empty:
                    row = pin_row.iloc[0]
                    st.session_state.map_pins.append({
                        "NAME": str(row["CELL_NAME"]),
                        "LAT": float(row["LATITUDE"]),
                        "LON": float(row["LONGITUDE"]),
                    })
                    pin_added = True
            elif st.session_state.get("last_clicked_site"):
                pin_row = df[
                    df["SITE_NAME"].astype(str).str.upper()
                    ==
                    str(st.session_state.last_clicked_site).upper()
                ]
                if not pin_row.empty:
                    row = pin_row.iloc[0]
                    st.session_state.map_pins.append({
                        "NAME": str(row["SITE_NAME"]),
                        "LAT": float(row["LATITUDE"]),
                        "LON": float(row["LONGITUDE"]),
                    })
                    pin_added = True

            st.session_state.map_tool_message = (
                "Engineering pin added to the selected cell/site."
                if pin_added
                else "Select a cell or site first, then press Pin."
            )

    with c3:
        base_label = "Dark" if st.session_state.get("map_style_mode") == "satellite" else "Sat"
        st.button(
            base_label,
            key="satellite_btn",
            on_click=toggle_map_style_mode
        )

    with c4:
        coverage_button_label = "Cover ON" if st.session_state.get("show_predicted_coverage") else "Cover"
        st.button(
            coverage_button_label,
            key="settings_btn",
            on_click=toggle_predicted_coverage
        )

    if st.session_state.get("map_tool_message"):
        st.markdown(
            f'<div class="map-tool-status">{st.session_state.map_tool_message}</div>',
            unsafe_allow_html=True
        )

    clear_col1, clear_col2 = st.columns(2)
    with clear_col1:
        st.button(
            "Clear Cov",
            key="clear_cover_btn",
            use_container_width=True,
            on_click=clear_predicted_coverage
        )
    with clear_col2:
        st.button(
            "Clear Pin",
            key="clear_pins_btn",
            use_container_width=True,
            on_click=clear_engineering_pins
        )
# =====================================================
# KPI CARDS
# =====================================================
st.markdown(
    '</div>',
    unsafe_allow_html=True
)
if False:

    card1, card2, card3, card4, card5, card6 = st.columns(6)

    with card1:
        st.markdown(f"""
        <div class="geo-card geo-card-sites">
            <div class="geo-label">TOTAL SITEs</div>
            <div class="geo-value">{df_filtered['SITE_NAME'].nunique()}</div>
        </div>
        """, unsafe_allow_html=True)

    with card2:
        st.markdown(f"""
        <div class="geo-card geo-card-cells">
            <div class="geo-label">TOTAL CELLs</div>
            <div class="geo-value">{len(df_filtered)}</div>
        </div>
        """, unsafe_allow_html=True)

    with card3:
        st.markdown(f"""
        <div class="geo-card geo-card-anr">
            <div class="geo-label">TOTAL nCell</div>
            <div class="geo-value">{len(nbr_df)}</div>
        </div>
        """, unsafe_allow_html=True)

    with card4:
        st.markdown(f"""
        <div class="geo-card geo-card-LTE">
            <div class="geo-label">LTE SITEs</div>
            <div class="geo-value">
                {(df_filtered['Technology']=='LTE').sum()}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with card5:
        st.markdown(f"""
        <div class="geo-card geo-card-5G">
            <div class="geo-label">5G SITEs</div>
            <div class="geo-value">
                {(df_filtered['Technology']=='5G').sum()}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with card6:
        st.markdown(f"""
        <div class="geo-card geo-card-sites">
            <div class="geo-label">VENDOR</div>
            <div class="geo-value">
                {df_filtered['VENDOR'].nunique()}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        "<div style='height:50px;'></div>",
        unsafe_allow_html=True
    )

# =====================================================
# KPI CARDS
# =====================================================

card1, card2, card3, card4, card5, card6, card7 = st.columns(7)

with card1:
    st.markdown(f"""
    <div class="geo-card" style="
    background:linear-gradient(
    135deg,
    rgba(16,185,129,0.35),
    rgba(5,150,105,0.15)
    );">
        <div class="geo-label">TOTAL SITES</div>
        <div class="geo-value">{df_filtered['SITE_NAME'].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

with card2:
    st.markdown(f"""
    <div class="geo-card" style="
    background:linear-gradient(
    135deg,
    rgba(59,130,246,0.35),
    rgba(37,99,235,0.15)
    );">
        <div class="geo-label">TOTAL CELLS</div>
        <div class="geo-value">{len(df_filtered)}</div>
    </div>
    """, unsafe_allow_html=True)

with card3:
    st.markdown(f"""
    <div class="geo-card" style="
    background:linear-gradient(
    135deg,
    rgba(168,85,247,0.35),
    rgba(126,34,206,0.15)
    );">
        <div class="geo-label">NCELLS</div>
        <div class="geo-value">{len(nbr_df)}</div>
    </div>
    """, unsafe_allow_html=True)

with card4:
    st.markdown(f"""
    <div class="geo-card" style="
    background:linear-gradient(
    135deg,
    rgba(245,158,11,0.35),
    rgba(217,119,6,0.15)
    );">
        <div class="geo-label">LTE SITES</div>
        <div class="geo-value">
            {(df_filtered['Technology'].astype(str).str.upper() == 'LTE').sum()}
        </div>
    </div>
    """, unsafe_allow_html=True)

with card5:
    st.markdown(f"""
    <div class="geo-card" style="
    background:linear-gradient(
    135deg,
    rgba(236,72,153,0.35),
    rgba(190,24,93,0.15)
    );">
        <div class="geo-label">5G SITES</div>
        <div class="geo-value">
            {(df_filtered['Technology'].astype(str).str.upper() == '5G').sum()}
        </div>
    </div>
    """, unsafe_allow_html=True)

with card6:
    st.markdown(f"""
    <div class="geo-card" style="
    background:linear-gradient(
    135deg,
    rgba(34,211,238,0.35),
    rgba(8,145,178,0.15)
    );">
        <div class="geo-label">VENDORS</div>
        <div class="geo-value">
            {df_filtered['VENDOR'].nunique()}
        </div>
    </div>
    """, unsafe_allow_html=True)

with card7:
    st.markdown(f"""
    <div class="geo-card" style="
    background:linear-gradient(
    135deg,
    rgba(239,68,68,0.42),
    rgba(127,29,29,0.20)
    );
    border-left:5px solid #EF4444;">
        <div class="geo-label">WORST MATCHED</div>
        <div class="geo-value">
            {len(worst_match_df)}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    "<div style='height:20px;'></div>",
    unsafe_allow_html=True
)

if not coverage_map_df.empty:
    st.markdown(f"""
    <div style="
    background:linear-gradient(135deg, rgba(34,211,216,0.18), rgba(15,23,42,0.82));
    border:1px solid rgba(34,211,216,0.34);
    border-left:5px solid #22D3D8;
    border-radius:12px;
    padding:12px 14px;
    margin-bottom:14px;
    color:#F8FAFC;
    ">
        <b>Coverage/KPI Layer Active</b><br>
        Counter: {st.session_state.coverage_kpi_column} |
        Rows rendered: {len(coverage_map_df):,} |
        Min: {coverage_map_df["KPI_VALUE"].min():.2f} |
        Avg: {coverage_map_df["KPI_VALUE"].mean():.2f} |
        Max: {coverage_map_df["KPI_VALUE"].max():.2f}
    </div>
    """, unsafe_allow_html=True)

if st.session_state.get("show_predicted_coverage") and st.session_state.get("predicted_coverage_cell"):
    predicted_info_df = df[
        df["CELL_NAME"].astype(str).str.upper()
        ==
        str(st.session_state.predicted_coverage_cell).upper()
    ]
    if not predicted_info_df.empty:
        info = predicted_info_df.iloc[0]
        st.markdown(f"""
        <div style="
        background:linear-gradient(135deg, rgba(245,184,75,0.18), rgba(15,23,42,0.82));
        border:1px solid rgba(245,184,75,0.34);
        border-left:5px solid #F5B84B;
        border-radius:12px;
        padding:12px 14px;
        margin-bottom:14px;
        color:#F8FAFC;
        ">
            <b>Predicted Coverage Active</b><br>
            Cell: {info.get("CELL_NAME", "-")} |
            Antenna: {info.get("ANTENNA", "-")} |
            Azimuth: {info.get("AZIMUTH", "-")} deg |
            Beamwidth: {info.get("BEAMWIDTH", 65)} deg |
            Height: {info.get("HEIGHT", "-")} m |
            Tilt: {info.get("M_TILT", "-")} deg |
            PMAX: {info.get("PMAX", "-")} dBm
            <br>
            <span style="color:#A7F3D0;">
                V1 antenna-aware approximation using real cell fields. Full RF propagation/pattern/clutter/terrain model comes next.
            </span>
        </div>
        """, unsafe_allow_html=True)

#=====================================
# 2. Render chart
#=========================================
st.pydeck_chart(
    pdk.Deck(
        map_style=(
            pdk.map_styles.SATELLITE
            if st.session_state.get("map_style_mode") == "satellite"
            else pdk.map_styles.DARK
        ),
        initial_view_state=pdk.ViewState(
            latitude=st.session_state.focus_lat,
            longitude=st.session_state.focus_lon,
            zoom=st.session_state.zoom_level
        ),
        layers=layers,
        tooltip={
            "html": "<b>{tooltip_text}</b><br/><span>{CELL_NAME}</span>",
            "style": {
                "backgroundColor": "#071016",
                "color": "#EEF8FB",
                "border": "1px solid #22D3D8",
                "borderRadius": "8px",
                "padding": "8px"
            }
        }
    ),
    width="stretch",
    height=480,
    key="map_key",
    on_select=on_map_click
)
#========================================================
st.sidebar.markdown("---")

st.sidebar.markdown(
f"""
<div style="
background: rgba(20,30,48,0.85);
border-left: 4px solid #3B82F6;
border-radius: 12px;
padding: 10px;
font-size: 13px;
color: white;
">

⚡ <b>GeoAI Performance</b><br/>

Load Time: {round(time.time() - start_time, 2)} sec<br/>

Layers: {len(layers)}<br/>

Cells: {len(df_filtered)}

</div>
""",
unsafe_allow_html=True
)
st.markdown(
    "<div style='margin-top:-80px'></div>",
    unsafe_allow_html=True
)
# ==========================================
# SAFE VARIABLES
# ==========================================

site_name = "-"
cell_name = "-"
technology = "-"
operator = "-"
carrier = "-"
pci = "-"
azimuth = "-"
height = "-"
rsrp = "-"
sinr = "-"
traffic = "-"
utilization = "-"

site_lat = "-"
site_lon = "-"
pmax = "-"
rspower = "-"
txrx_mode = "-"

tac = "-"
enodebid = "-"
eci = "-"
rsi = "-"
dl_bw = "-"
vendor = "-"
cluster_area = "-"
actstatus = "-"

if selected_site_row is not None:

    site_name = selected_site_row["SITE_NAME"]

    site_lat = selected_site_row["LATITUDE"]

    site_lon = selected_site_row["LONGITUDE"]

if selected_row is not None:

    vendor = selected_row.get("VENDOR", "-")

    cluster_area = selected_row.get("CLUSTER_AREA", "-")

    cell_name = selected_row["CELL_NAME"]

    site_name = selected_row["SITE_NAME"]

    technology = selected_row["Technology"]

    operator = selected_row["Operator"]

    carrier = selected_row["CARRIER"]

    pci = selected_row.get("PCI", "-")

    azimuth = selected_row["AZIMUTH"]

    height = selected_row.get("HEIGHT", "-")

    rsrp = selected_row.get("rsrp", "-")

    sinr = selected_row.get("sinr", "-")

    traffic = selected_row.get("traffic", "-")

    utilization = selected_row.get("utilization", "-")

    pmax = selected_row.get("PMAX", "-")

    rspower = selected_row.get("RSPOWER", "-")

    txrx_mode = selected_row.get("TXRX_MODE", "-")

    tac = selected_row.get("TAC", "-")

    enodebid = selected_row.get("ENODEBID", "-")

    eci = selected_row.get("ECI", "-")

    rsi = selected_row.get("RSI", "-")

    dl_bw = selected_row.get("DL BW", "-")

    actstatus = selected_row.get("ACTSTATUS", "-")

if "incoming_count" not in locals():
    incoming_count = 0

if "outgoing_count" not in locals():
    outgoing_count = 0
    # <<< ADD HERE >>>

Missing_Ncell = 0
OneWay_Ncell = 0
# ==========================================
# ANR COUNTS
# ==========================================

incoming_count = 0
outgoing_count = 0
Missing_Ncell = 0
OneWay_Ncell = 0

if selected_row is not None:

    cell_name = str(selected_row["CELL_NAME"]).strip()

    outgoing_count = len(
        nbr_df[
            nbr_df["source_sector"].astype(str).str.strip() == cell_name
        ]
    )

    incoming_count = len(
        nbr_df[
            nbr_df["target_sector"].astype(str).str.strip() == cell_name
        ]
    )

    OneWay_Ncell = len(
        one_way_df[
            (one_way_df["source_sector"].astype(str).str.strip() == cell_name)
            |
            (one_way_df["target_sector"].astype(str).str.strip() == cell_name)
        ]
    )

    Missing_Ncell = len(
        missing_ncell_df[
            missing_ncell_df["source_sector"].astype(str).str.strip() == cell_name
        ]
    )

# ==========================================
# INFO CARDS
# ==========================================

#with info3:

    #st.markdown(...)
# ==========================================
# SITE / CELL INFO
# ==========================================

info1, info2, info3, info4, info5, info6 = st.columns(6)

with info1:

    st.markdown(f"""
    <div style="
        background:rgba(15,23,42,0.85);
        border:1px solid rgba(59,130,246,0.25);
        border-left:4px solid #60A5FA;
        border-radius:12px;
        padding:2px;
        height:220px;
        color:white;
    ">

    <h3 style="color:#60A5FA;margin-top:0px;margin-bottom:5px;">SITE.INFO</h3>

    <b>Site:</b> {site_name}<br>
    <b>Latitude:</b> {site_lat}<br>
    <b>Longitude:</b> {site_lon}<br>
    <b>Vendor:</b> {vendor}<br>
    <b>Cluster:</b> {cluster_area}

    </div>
    """, unsafe_allow_html=True)

with info2:

    st.markdown(f"""
    <div style="
        background:rgba(15,23,42,0.85);
        border:1px solid rgba(59,130,246,0.25);
        border-left:4px solid #3B82F6;
        border-radius:12px;
        padding:2px;
        height:220px;
        color:white;
    ">
    <h3 style="color:#3B82F6;margin-top:0px;margin-bottom:5px;">CELL.INFO</h3>


    <b>Cell:</b> {cell_name}<br>
    <b>Technology:</b> {technology}<br>
    <b>Operator:</b> {operator}<br>
    <b>Carrier:</b> {carrier}<br>
    <b>PCI:</b> {pci}

    </div>
    """, unsafe_allow_html=True)
with info3:

    st.markdown(f"""
    <div style="
        background:rgba(15,23,42,0.85);
        border:1px solid rgba(168,85,247,0.25);
        border-left:4px solid #A855F7;
        border-radius:12px;
        padding:2px;
        height:220px;
        color:white;
    ">

    <h3 style="color:#A855F7;margin-top:0px;margin-bottom:5px;">ANR INFO</h3>


    <b>Incoming:</b> {incoming_count}<br>
    <b>Outgoing:</b> {outgoing_count}<br>
    <b>PCI:</b> {pci}<br>
    <b>Missing Ncell:</b> {Missing_Ncell}<br>
    <b>One-Way Ncell:</b> {OneWay_Ncell}<br>

    </div>
    """, unsafe_allow_html=True)
with info4:

    st.markdown(f"""
    <div style="
        background:rgba(15,23,42,0.85);
        border:1px solid rgba(16,185,129,0.25);
        border-left:4px solid #10B981;
        border-radius:12px;
        padding:2px;
        height:220px;
        color:white;
    ">


    <h3 style="color:#10B981;margin-top:0px;margin-bottom:5px;">RF INFO</h3>
    <b>Azimuth:</b> {azimuth}<br>
    <b>Height:</b> {height}<br>
    <b>PMAX:</b> {pmax}<br>
    <b>RS Power:</b> {rspower}<br>
    <b>TXRX:</b> {txrx_mode}

    </div>
    """, unsafe_allow_html=True)

with info5:

    st.markdown(f"""
    <div style="
        background:rgba(15,23,42,0.85);
        border:1px solid rgba(245,158,11,0.25);
        border-left:4px solid #F59E0B;
        border-radius:12px;
        padding:2px;
        height:220px;
        color:white;
    ">


    <h3 style="color:#F59E0B;margin-top:0px;margin-bottom:5px;">NW.INFO</h3>
    <b>TAC:</b> {tac}<br>
    <b>eNB ID:</b> {enodebid}<br>
    <b>ECI:</b> {eci}<br>
    <b>RSI:</b> {rsi}<br>
    <b>DL BW:</b> {dl_bw}

    </div>
    """, unsafe_allow_html=True)

with info6:

    st.markdown(f"""
    <div style="
        background:rgba(15,23,42,0.85);
        border:1px solid rgba(236,72,153,0.25);
        border-left:4px solid #EC4899;
        border-radius:12px;
        padding:2px;
        height:220px;
        color:white;
    ">


    <h3 style="color:#EC4899;margin-top:0px;margin-bottom:5px;">OPS INFO</h3>
    <b>Traffic:</b> {traffic}<br>
    <b>Utilization:</b> {utilization}<br>
    <b>RSRP:</b> {rsrp}<br>
    <b>SINR:</b> {sinr}<br>
    <b>Status:</b> {actstatus}

    </div>
    """, unsafe_allow_html=True)
