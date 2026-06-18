import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import math
import re
import gc
import time
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

    color: white;

    border: 1px solid rgba(59,130,246,0.25);

    border-radius: 16px;

    height: 48px;

    font-size: 15px;

    font-weight: 800;

    letter-spacing: 0.4px;

    box-shadow:
        0 0 10px rgba(59,130,246,0.10);

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

#@st.cache_data
#def get_one_way_neighbors(nbr_df):

    #pairs = set(
        #zip(
            #3nbr_df["source_sector"],
            #nbr_df["target_sector"]
        #)
    #)

    #one_way = []

    #for source, target in pairs:

        #if (target, source) not in pairs:

            #one_way.append(
                #(source, target)
            #)

    #return pd.DataFrame(
        #one_way,
        #columns=[
            #"source_sector",
            #"target_sector"
        #]

    #)


#one_way_df = get_one_way_neighbors(nbr_df)

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
🚨 SPECIAL SITES
</div>
""", unsafe_allow_html=True)

show_hospitals = st.sidebar.checkbox(
    "🏥 Hospitals",
    value=False
)

show_police = st.sidebar.checkbox(
    "🚔 Police",
    value=False
)

show_fire = st.sidebar.checkbox(
    "🚒 Fire Stations",
    value=False
)

show_events = st.sidebar.checkbox(
    "🎪 Special Events",
    value=False
)

show_roaming = st.sidebar.checkbox(
    "🤝 National Roaming",
    value=False
)

show_stores = st.sidebar.checkbox(
    "🏪 Operator Stores",
    value=False
)

show_hubs = st.sidebar.checkbox(
    "📡 Hub Sites",
    value=False
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

            line_width_min_pixels=1,

            stroked=True,

            filled=True,

            pickable=True

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

        # ======================================
        # ADD LINE
        # ======================================

        ncell_lines.append({
            "path": [
                [src_lon, src_lat],
                [tgt_lon, tgt_lat],
            ],
            "color": line_color,
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
                id="ncell-lines",
                get_path="path",
                get_color="color",
                width_scale=1,
                width_min_pixels=2,
                pickable=False,
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
    st.button("🛠 Export To Google Earth", use_container_width=True)


with menu2:
    st.button("📡 COVERAGE LAYERS & DT LOG", use_container_width=True)

with menu3:
    st.button("🔗 ANR & AUTO NCell LIST Generatore", use_container_width=True)

with menu4:
    st.button("📊 REPORTS ➤ Go TO Dashboards", use_container_width=True)

with menu5:
    st.button("👤 ADMIN & Login", use_container_width=True)



# ====================================================
# MENU 2
# ====================================================

m2_1, gap1, m2_2, gap2, m2_3, gap3, m2_4 = st.columns(
    [3,0.2,4,0.2,3,0.2,3]
)

# --------------------------------
# QUICK FIND
# --------------------------------
with m2_1:

    st.markdown("""
    <div class="m2-card">
        🎯 QUICK FIND
    </div>
    """, unsafe_allow_html=True)

    target_site = st.text_input(
        "",
        placeholder="Site / Cell"
    )

# --------------------------------
# GLOBAL SEARCH
# --------------------------------
with m2_2:

    st.markdown("""
    <div class="m2-card">
        🌍 GLOBAL SEARCH
    </div>
    """, unsafe_allow_html=True)

    st.text_input(
        "",
        placeholder="PCI / TAC / Vendor / Address"
    )

# --------------------------------
# NAVIGATION
# --------------------------------
with m2_3:

    st.markdown("""
    <div class="m2-card">
        🧭 NAVIGATION TOOLS
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.button("➕", key="zoom_in")

    with c2:
        st.button("➖", key="zoom_out")

    with c3:
        st.button("🎯", key="focus_btn")

    with c4:
        st.button("⌂", key="home_btn")

# --------------------------------
# MAP TOOLS
# --------------------------------
with m2_4:

    st.markdown("""
    <div class="m2-card">
        🛠 MAP TOOLS
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.button("📏", key="measure_btn")

    with c2:
        st.button("📍", key="marker_btn")

    with c3:
        st.button("🛰", key="satellite_btn")

    with c4:
        st.button("⚙", key="settings_btn")

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

card1, card2, card3, card4, card5, card6 = st.columns(6)

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

st.markdown(
    "<div style='height:20px;'></div>",
    unsafe_allow_html=True
)

#=====================================
# 2. Render chart
#=========================================
st.pydeck_chart(
    pdk.Deck(
        map_style=pdk.map_styles.DARK,
        initial_view_state=pdk.ViewState(
            latitude=st.session_state.focus_lat,
            longitude=st.session_state.focus_lon,
            zoom=st.session_state.zoom_level
        ),
        layers=layers,
        tooltip={"text": "{CELL_NAME}"}
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

    cell_name = selected_row["CELL_NAME"]

    outgoing_count = len(
        nbr_df[
            nbr_df["source_sector"] == cell_name
        ]
    )

    incoming_count = len(
        nbr_df[
            nbr_df["target_sector"] == cell_name
        ]
    )

    OneWay_Ncell = abs(
        outgoing_count - incoming_count
    )

    valid_cells = set(
        df["CELL_NAME"].astype(str)
    )

    Missing_Ncell = len(
        nbr_df[
            (nbr_df["source_sector"] == cell_name)
            &
            (~nbr_df["target_sector"]
                .astype(str)
                .isin(valid_cells))
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
