"""Level UP — AI-assisted employee trajectory & career management (demo prototype).

Run:  streamlit run app.py
All data is fictional (see seed.py).
"""
import html
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import engine
import report
import seed

st.set_page_config(page_title="Level UP", page_icon=":material/trending_up:", layout="wide", initial_sidebar_state="expanded")

if not engine.DB_PATH.exists():
    seed.build()

# ---------------------------------------------------------------------------
# Design tokens — emerald & silver
# ---------------------------------------------------------------------------
EMERALD, EMERALD_BRIGHT, EMERALD_DEEP = "#2fb57a", "#5fd6a0", "#0f5132"
SILVER, SILVER_DIM = "#c7d0cb", "#8fa39a"
INK, INK2, MUTED, GRID = "#e7efea", "#a9bdb2", "#6f877b", "rgba(199,208,203,0.08)"
GOLD, BLUE, RED = "#d4b25f", "#4aa3df", "#e46a6a"
PRACTICE_COLORS = {"Strategy": EMERALD_BRIGHT, "HR Consulting": SILVER, "Finance & Transactions": BLUE,
                   "Operations": GOLD}
HR_NAME = "Ibrahima Camara"
HR_ACTOR = f"{HR_NAME} (HR Business Partner)"
RISK_STYLE = {"High": ("rgba(228,106,106,0.14)", "#ff9b93", "▲"), "Medium": ("rgba(212,178,95,0.14)", "#e8cb84", "◆"),
              "Low": ("rgba(47,181,122,0.14)", "#7fe3b4", "●")}
# 9-box cell styling: (background, border, accent text) — intensity of green tracks the cell's value
BOX_STYLE = {
    "Star": ("linear-gradient(150deg, rgba(60,207,142,0.30), rgba(15,81,50,0.35))", "rgba(95,214,160,0.55)", "#9ff0c9"),
    "High Potential": ("linear-gradient(150deg, rgba(47,181,122,0.18), rgba(15,81,50,0.22))", "rgba(95,214,160,0.30)", "#7fe3b4"),
    "High Performer": ("linear-gradient(150deg, rgba(47,181,122,0.18), rgba(15,81,50,0.22))", "rgba(95,214,160,0.30)", "#7fe3b4"),
    "Core Player": ("linear-gradient(150deg, rgba(199,208,203,0.08), rgba(199,208,203,0.03))", "rgba(199,208,203,0.18)", "#dfe7e2"),
    "Rough Diamond": ("linear-gradient(150deg, rgba(212,178,95,0.14), rgba(212,178,95,0.04))", "rgba(212,178,95,0.30)", "#e8cb84"),
    "Solid Performer": ("linear-gradient(150deg, rgba(212,178,95,0.14), rgba(212,178,95,0.04))", "rgba(212,178,95,0.30)", "#e8cb84"),
    "Inconsistent Performer": ("linear-gradient(150deg, rgba(222,128,72,0.15), rgba(222,128,72,0.04))", "rgba(222,128,72,0.30)", "#f0a77a"),
    "Risk of Stagnation": ("linear-gradient(150deg, rgba(222,128,72,0.15), rgba(222,128,72,0.04))", "rgba(222,128,72,0.30)", "#f0a77a"),
    "Under Performer": ("linear-gradient(150deg, rgba(228,106,106,0.17), rgba(228,106,106,0.05))", "rgba(228,106,106,0.35)", "#ff9b93"),
}
# Opaque fills for the plotly trajectory chart (dark-surface equivalents of the tints above)
BOX_FILL = {"Star": "#1b4d36", "High Potential": "#143a2a", "High Performer": "#143a2a", "Core Player": "#15211c",
            "Rough Diamond": "#2a2716", "Solid Performer": "#2a2716", "Inconsistent Performer": "#2c1f15",
            "Risk of Stagnation": "#2c1f15", "Under Performer": "#311a1a"}

LOGO = """<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2fb57a"/>
<stop offset="1" stop-color="#0b3d27"/></linearGradient>
<linearGradient id="ls" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f1f5f3"/>
<stop offset="1" stop-color="#9fb0a8"/></linearGradient></defs>
<rect x="1" y="1" width="38" height="38" rx="11" fill="url(#lg)" stroke="rgba(199,208,203,0.45)"/>
<path d="M13 10 V28 H27" fill="none" stroke="url(#ls)" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M21 19 L26 13 L31 19" fill="none" stroke="url(#ls)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M26 13.5 V23" stroke="url(#ls)" stroke-width="3" stroke-linecap="round"/></svg>"""

st.markdown("""
<style>
:root {
  --lu-bg:#07110d; --lu-surface:#0d1c15; --lu-surface-2:#122a1f; --lu-border:#1f3b2e; --lu-border-2:#2b5240;
  --lu-emerald:#2fb57a; --lu-emerald-bright:#5fd6a0; --lu-silver:#c7d0cb; --lu-silver-dim:#8fa39a;
  --lu-ink:#e7efea; --lu-ink-2:#a9bdb2; --lu-muted:#6f877b;
  --lu-serif:"Cormorant Garamond", Georgia, serif;
}
.stApp {
  background:
    radial-gradient(1100px 520px at 85% -8%, rgba(47,181,122,0.16), transparent 60%),
    radial-gradient(800px 400px at -10% 110%, rgba(47,181,122,0.08), transparent 60%),
    var(--lu-bg);
}
[data-testid="stHeader"] {background: transparent;}
.stAppDeployButton {display:none;}
.block-container, [data-testid="stMainBlockContainer"] {padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1440px;}
h1, h2, h3, h4 {font-family: var(--lu-serif) !important; letter-spacing: 0.005em; color: var(--lu-ink);}
h2 {font-size: 1.75rem !important;} h3 {font-size: 1.45rem !important;} h4 {font-size: 1.2rem !important;}

/* Sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a1f16 0%, #071510 60%, #06110c 100%);
  border-right: 1px solid var(--lu-border);
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.68rem; color: var(--lu-silver-dim); font-weight:600;
}
.lu-brand {display:flex; align-items:center; gap:12px; margin: 0 0 6px 0;}
.lu-brand-name {font-family: var(--lu-serif); font-size: 1.85rem; font-weight: 700; line-height: 1;
  background: linear-gradient(180deg, #f4f8f6, #a8b8b0); -webkit-background-clip: text; background-clip:text; color: transparent;}
.lu-brand-tag {font-size: 0.6rem; letter-spacing: 0.16em; white-space: nowrap; text-transform: uppercase; color: var(--lu-emerald-bright); margin-top:4px;}
.lu-firm {font-size: 0.8rem; color: var(--lu-ink-2); line-height: 1.45; padding: 10px 12px; border-radius: 10px;
  background: rgba(199,208,203,0.04); border: 1px solid var(--lu-border); margin: 12px 0 4px 0;}
.lu-firm b {color: var(--lu-silver);}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding: 3px 0;}

/* Page hero */
.lu-hero {position: relative; padding: 26px 30px 24px 30px; border-radius: 20px; margin-bottom: 18px; overflow: hidden;
  background: linear-gradient(120deg, rgba(20,58,42,0.92) 0%, rgba(13,32,24,0.92) 55%, rgba(9,22,17,0.9) 100%);
  border: 1px solid var(--lu-border-2); box-shadow: 0 18px 50px -24px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.05);}
.lu-hero:after {content:""; position:absolute; right:-80px; top:-120px; width:360px; height:360px; border-radius:50%;
  background: radial-gradient(circle, rgba(95,214,160,0.22), transparent 65%);}
.lu-hero:before {content:""; position:absolute; left:0; right:0; top:0; height:1px;
  background: linear-gradient(90deg, transparent, rgba(199,208,203,0.55), transparent);}
.lu-hero-kicker {font-size: 0.68rem; letter-spacing: 0.24em; text-transform: uppercase; color: var(--lu-emerald-bright);
  font-weight: 600; margin-bottom: 6px;}
.lu-hero-title {font-family: var(--lu-serif); font-size: 2.7rem; font-weight: 600; line-height: 1.05; color: #f2f6f4;}
.lu-hero-sub {font-size: 0.95rem; color: var(--lu-ink-2); margin-top: 8px; max-width: 900px;}
.lu-hero-row {display:flex; align-items:center; gap:20px; position:relative; z-index:1;}
.lu-avatar {width:74px; height:74px; border-radius:50%; flex: 0 0 auto; display:flex; align-items:center;
  justify-content:center; font-family: var(--lu-serif); font-size: 1.9rem; font-weight:700; color:#f2f6f4;
  background: linear-gradient(145deg, #2fb57a, #0b3d27); box-shadow: 0 0 0 2px rgba(199,208,203,0.55), 0 0 0 6px rgba(47,181,122,0.15);}

/* Human-in-the-loop banner */
.lu-hitl {display:flex; gap:12px; align-items:flex-start; background: rgba(47,181,122,0.06);
  border: 1px solid rgba(95,214,160,0.22); border-left: 3px solid var(--lu-emerald); border-radius: 12px;
  padding: 11px 16px; color: var(--lu-ink-2); font-size: 0.88rem; margin-bottom: 1.1rem;}
.lu-hitl b {color: var(--lu-silver);}
.lu-hitl-icon {color: var(--lu-emerald-bright); font-size: 1rem; line-height: 1.3;}

/* Metric cards */
[data-testid="stMetric"] {background: linear-gradient(160deg, rgba(18,42,31,0.9), rgba(11,26,19,0.9));
  border: 1px solid var(--lu-border); border-radius: 16px; padding: 16px 18px 14px 18px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);}
[data-testid="stMetricLabel"] p {text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.68rem !important;
  color: var(--lu-silver-dim); font-weight: 600;}
[data-testid="stMetricValue"] {font-family: var(--lu-serif); font-size: 2.3rem !important; font-weight: 600; color: #f2f6f4;}

/* Bordered cards (st.container(border=True, key="card_…")) */
[class*="st-key-card_"] {background: linear-gradient(160deg, rgba(16,36,27,0.85), rgba(10,23,17,0.85)) !important;
  border: 1px solid var(--lu-border) !important; border-radius: 16px !important;
  box-shadow: 0 10px 30px -20px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255,255,255,0.03);}
[class*="st-key-card_"]:hover {border-color: var(--lu-border-2) !important;}

/* Buttons */
[data-testid="stBaseButton-primary"] {background: linear-gradient(135deg, #2fb57a, #17734b) !important;
  border: 1px solid rgba(95,214,160,0.55) !important; color: #f4fbf7 !important; font-weight: 600;
  box-shadow: 0 6px 18px -8px rgba(47,181,122,0.7);}
[data-testid="stBaseButton-primary"]:hover {filter: brightness(1.08);}
[data-testid="stBaseButton-secondary"] {background: rgba(199,208,203,0.04) !important; border: 1px solid var(--lu-border-2) !important;
  color: var(--lu-silver) !important;}
[data-testid="stBaseButton-secondary"]:hover {border-color: var(--lu-emerald) !important; color: #f2f6f4 !important;}

/* Tabs */
[data-baseweb="tab-list"] {gap: 4px; border-bottom: 1px solid var(--lu-border);}
[data-baseweb="tab"] {padding: 8px 14px !important; border-radius: 10px 10px 0 0;}
[data-baseweb="tab"] p {font-size: 0.9rem; font-weight: 500;}
[data-baseweb="tab"][aria-selected="true"] p {color: #f2f6f4;}

/* Expanders, dataframes */
[data-testid="stExpander"] details {border: 1px solid var(--lu-border) !important; border-radius: 14px !important;
  background: rgba(13,28,21,0.6);}
[data-testid="stDataFrame"] {border-radius: 12px; overflow: hidden; border: 1px solid var(--lu-border);}
hr {border-color: var(--lu-border) !important;}

/* Small components */
.lu-kicker {font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.16em; color: var(--lu-silver-dim);
  font-weight: 600; margin-bottom: 4px;}
.lu-pill {display:inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.76rem; font-weight: 600;
  margin: 0 5px 4px 0; white-space: nowrap; border: 1px solid rgba(255,255,255,0.07);}
.lu-section {display:flex; align-items:baseline; gap:10px; margin: 6px 0 10px 0;}
.lu-section-title {font-family: var(--lu-serif); font-size: 1.55rem; font-weight: 600; color: var(--lu-ink);}
.lu-section-line {flex:1; height:1px; background: linear-gradient(90deg, var(--lu-border-2), transparent);}

/* 9-box */
.lu-grid {display:grid; grid-template-columns: 30px repeat(3, 1fr); grid-template-rows: repeat(3, auto) 28px;
  gap: 8px; width: 100%;}
.lu-cell {border-radius: 14px; padding: 11px 12px 12px 12px; min-height: 128px; position: relative;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);}
.lu-cell-title {font-family: var(--lu-serif); font-weight: 700; font-size: 1.08rem; display:flex;
  justify-content: space-between; align-items: baseline;}
.lu-cell-n {font-family: Inter, sans-serif; font-size: 0.66rem; letter-spacing: 0.12em; color: var(--lu-muted);
  margin-right: 6px; font-weight: 600;}
.lu-cell-count {font-family: Inter, sans-serif; font-size: 0.72rem; font-weight: 700; color: var(--lu-ink);
  background: rgba(0,0,0,0.28); border: 1px solid rgba(255,255,255,0.08); border-radius: 999px; padding: 1px 8px;}
.lu-cell-sub {font-size: 0.72rem; color: var(--lu-ink-2); margin: 2px 0 8px 0;}
.lu-chip {display:inline-flex; align-items:center; gap:6px; background: rgba(5,14,10,0.55);
  border: 1px solid rgba(199,208,203,0.12); border-radius: 999px; padding: 3px 10px 3px 3px; margin: 3px 4px 3px 0;
  font-size: 0.78rem; color: var(--lu-ink); backdrop-filter: blur(4px);}
.lu-chip:hover {border-color: rgba(95,214,160,0.6);}
.lu-ini {width: 20px; height: 20px; border-radius: 50%; display:inline-flex; align-items:center; justify-content:center;
  font-size: 0.6rem; font-weight: 700; color: #f2f6f4; background: linear-gradient(145deg, #2fb57a, #0f5132);
  box-shadow: 0 0 0 1px rgba(199,208,203,0.4);}
.lu-axis-y {writing-mode: vertical-rl; transform: rotate(180deg); text-align: center; font-size: 0.64rem;
  color: var(--lu-silver-dim); font-weight: 600; letter-spacing: 0.2em;}
.lu-axis-x {text-align: center; font-size: 0.64rem; color: var(--lu-silver-dim); font-weight: 600; letter-spacing: 0.2em;
  padding-top: 6px;}
.lu-legend {font-size: 0.76rem; color: var(--lu-muted); margin-top: 10px;}

/* AI summary */
.lu-summary {position: relative; background: linear-gradient(150deg, rgba(20,58,42,0.55), rgba(10,23,17,0.7));
  border: 1px solid rgba(95,214,160,0.28); border-radius: 16px; padding: 18px 20px; font-size: 1rem;
  line-height: 1.6; color: var(--lu-ink);}
.lu-evidence {font-size: 0.85rem; color: var(--lu-ink-2); border-left: 2px solid var(--lu-border-2);
  padding-left: 10px; margin: 4px 0;}
.lu-rank {font-family: var(--lu-serif); font-size: 2.4rem; font-weight: 700; line-height: 1;
  background: linear-gradient(180deg, #f1f5f3, #7f938a); -webkit-background-clip: text; background-clip: text; color: transparent;}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {width: 300px !important; min-width: 300px !important;}
[data-testid="stSidebarContent"] {padding-top: 0.2rem;}
[data-testid="stSidebarUserContent"] {padding: 0.6rem 1.1rem 1.5rem 1.1rem;}
[data-testid="stSidebar"]:before {content:""; position:absolute; left:0; right:0; top:0; height:220px; pointer-events:none;
  background: radial-gradient(260px 160px at 20% 0%, rgba(47,181,122,0.20), transparent 70%);}
.lu-brand {padding-bottom: 14px; margin-bottom: 4px; border-bottom: 1px solid var(--lu-border);}
.lu-sb-label {font-size: 0.62rem; letter-spacing: 0.22em; text-transform: uppercase; color: var(--lu-muted);
  font-weight: 600; margin: 18px 0 8px 2px; display:flex; align-items:center; gap:8px;}
.lu-sb-label:after {content:""; flex:1; height:1px; background: linear-gradient(90deg, var(--lu-border), transparent);}
/* role toggle: full-width pill switch */
[data-testid="stSidebar"] .stElementContainer:has([data-testid="stButtonGroup"]),
[data-testid="stSidebar"] [data-testid="stButtonGroup"] {width: 100% !important;}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button {flex: 0 0 calc(50% - 2px) !important; width: calc(50% - 2px) !important;
  max-width: none !important; min-width: 0; white-space: nowrap; padding: 4px 8px !important;}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] [data-baseweb="button-group"] {display:flex; width:100%;
  background: rgba(0,0,0,0.25); border: 1px solid var(--lu-border); border-radius: 12px; padding: 3px; gap: 3px;}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button {border: none !important; border-radius: 9px !important;
  background: transparent !important; color: var(--lu-ink-2) !important; min-height: 34px;}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button:hover {color: #f2f6f4 !important; background: rgba(199,208,203,0.05) !important;}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"] {
  background: linear-gradient(135deg, #2fb57a, #17734b) !important; color: #f4fbf7 !important;
  box-shadow: 0 4px 14px -6px rgba(47,181,122,0.8), inset 0 1px 0 rgba(255,255,255,0.15);}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button p {font-size: 0.85rem; font-weight: 600;}
/* signed-in card */
.lu-user {display:flex; align-items:center; gap:11px; margin-top: 10px; padding: 10px 12px; border-radius: 14px;
  background: linear-gradient(160deg, rgba(18,42,31,0.9), rgba(10,24,18,0.9)); border: 1px solid var(--lu-border);
  position: relative;}
.lu-user-av {width: 36px; height: 36px; border-radius: 50%; flex: 0 0 auto; display:flex; align-items:center;
  justify-content:center; font-family: var(--lu-serif); font-weight: 700; font-size: 1rem; color: #f2f6f4;
  background: linear-gradient(145deg, #2fb57a, #0b3d27); box-shadow: 0 0 0 1.5px rgba(199,208,203,0.5);}
.lu-user-name {font-weight: 600; font-size: 0.88rem; color: var(--lu-ink); white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis;}
.lu-user-role {font-size: 0.72rem; color: var(--lu-silver-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.lu-user-dot {position:absolute; right: 12px; top: 12px; width: 7px; height: 7px; border-radius: 50%;
  background: var(--lu-emerald-bright); box-shadow: 0 0 0 3px rgba(95,214,160,0.18);}
/* navigation */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap: 2px;}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {width: 100%; margin: 0;
  padding: 8px 12px !important; border-radius: 10px; border: 1px solid transparent; transition: all 0.15s ease;
  cursor: pointer;}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {display: none;}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] p {font-size: 0.9rem; color: var(--lu-ink-2);
  font-weight: 500; display:flex; align-items:center;}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] p span[data-testid="stIconMaterial"] {
  color: var(--lu-muted); font-size: 1.15rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover {background: rgba(199,208,203,0.05);}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover p {color: #f2f6f4;}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
  background: linear-gradient(90deg, rgba(47,181,122,0.22), rgba(47,181,122,0.04));
  border-color: rgba(95,214,160,0.28); box-shadow: inset 3px 0 0 var(--lu-emerald-bright);}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {color: #f2f6f4; font-weight: 600;}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span[data-testid="stIconMaterial"] {
  color: var(--lu-emerald-bright);}
/* timeline */
.lu-time {padding: 12px 14px 10px 14px; border-radius: 14px; border: 1px solid var(--lu-border);
  background: linear-gradient(160deg, rgba(18,42,31,0.9), rgba(10,24,18,0.9));}
.lu-time-k {font-size: 0.7rem; color: var(--lu-silver-dim);}
.lu-time-row {display:flex; align-items:center; justify-content:space-between; margin-top: 2px;}
.lu-time-v {font-family: var(--lu-serif); font-size: 1.6rem; font-weight: 600; color: #f2f6f4;}
.lu-time-tag {font-size: 0.66rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; padding: 3px 9px;
  border-radius: 999px;}
.lu-time-tag.live {color: #7fe3b4; background: rgba(47,181,122,0.14); border: 1px solid rgba(95,214,160,0.3);}
.lu-time-tag.replay {color: #e8cb84; background: rgba(212,178,95,0.12); border: 1px solid rgba(212,178,95,0.3);}
[data-testid="stSidebar"] [data-testid="stSlider"] {padding: 0 6px;}
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"] {font-size: 0.72rem; color: var(--lu-emerald-bright);}
[data-testid="stSidebar"] [data-testid="stSliderTickBar"] {font-size: 0.7rem; color: var(--lu-muted);}
.lu-sb-gap {height: 10px;}
.lu-sb-note {font-size: 0.74rem; color: var(--lu-muted); line-height: 1.45; margin-top: -4px;}
.lu-sb-foot {margin-top: 26px; padding-top: 14px; border-top: 1px solid var(--lu-border); font-size: 0.74rem;
  color: var(--lu-silver-dim); line-height: 1.55;}
.lu-sb-foot b {color: var(--lu-silver); font-weight: 600;}
.lu-sb-fict {color: var(--lu-muted); font-style: italic;}
[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] {color: var(--lu-silver-dim) !important; padding-left: 0;}
[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:hover {color: var(--lu-emerald-bright) !important;}


/* ---- Decision log ---- */
.lu-log {table-layout: fixed;}
.lu-log td, .lu-log th {vertical-align: top; white-space: normal !important; word-break: break-word; padding: 10px 10px;}
.lu-log td .sub {font-size: 0.72rem; color: var(--lu-muted); font-weight: 400; margin-top: 2px; white-space: normal;}
.lu-log td.reason {line-height: 1.45;}
.lu-log td.stt {white-space: nowrap !important; font-size: 0.8rem;}
.lu-log .lu-pill {font-size: 0.7rem; padding: 2px 8px;}
.lu-log td.name {white-space: normal;}

/* ---- Survey phone mockups ---- */
.lu-phone {max-width: 380px; margin: 6px auto 10px auto; border-radius: 38px; padding: 14px 16px 18px 16px;
  background: linear-gradient(170deg, #0f2219, #08140f); border: 1px solid #2b5240;
  box-shadow: 0 0 0 6px #050c09, 0 0 0 7px #2b5240, 0 30px 60px -20px rgba(0,0,0,0.9);}
.lu-ph-notch {width: 96px; height: 20px; border-radius: 0 0 14px 14px; background: #050c09; margin: -14px auto 12px auto;}
.lu-ph-head {display:flex; align-items:center; gap:10px; padding: 0 4px 10px 4px;}
.lu-ph-head svg {width: 30px; height: 30px; flex: 0 0 auto;}
.lu-ph-title {font-family: var(--lu-serif); font-size: 1.25rem; font-weight: 700; color: #f2f6f4; line-height: 1.1;}
.lu-ph-sub {font-size: 0.72rem; color: var(--lu-silver-dim);}
.lu-ph-prog {height: 4px; border-radius: 99px; background: rgba(199,208,203,0.1); margin: 0 4px 12px 4px; overflow:hidden;}
.lu-ph-prog span {display:block; height:100%; background: linear-gradient(90deg, #17734b, #5fd6a0);}
.lu-ph-body {padding: 0 2px;}
.lu-ph-role {font-size: 0.6rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--lu-emerald-bright);
  font-weight: 700; margin: 6px 4px 6px 4px;}
.lu-q {background: rgba(199,208,203,0.04); border: 1px solid var(--lu-border); border-radius: 16px; padding: 11px 12px;
  margin-bottom: 9px;}
.lu-q-n {font-size: 0.6rem; font-weight: 700; letter-spacing: 0.14em; color: var(--lu-muted);}
.lu-q-t {font-size: 0.86rem; color: var(--lu-ink); font-weight: 500; margin: 2px 0 8px 0; line-height: 1.35;}
.lu-q-h {font-size: 0.72rem; color: var(--lu-muted);}
.lu-sc-row {display:flex; gap: 4px;}
.lu-sc {flex:1; text-align:center; font-size: 0.72rem; font-weight: 600; padding: 6px 0; border-radius: 8px;
  background: rgba(199,208,203,0.06); color: var(--lu-ink-2); border: 1px solid transparent;}
.lu-sc.on {background: linear-gradient(135deg, #2fb57a, #17734b); color: #fff; border-color: rgba(95,214,160,0.6);
  box-shadow: 0 4px 12px -4px rgba(47,181,122,0.8);}
.lu-sc-ends {display:flex; justify-content: space-between; font-size: 0.64rem; color: var(--lu-muted); margin-top: 4px;}
.lu-opt {display:flex; align-items:center; gap: 8px; font-size: 0.8rem; color: var(--lu-ink-2); padding: 6px 8px;
  border-radius: 10px; border: 1px solid var(--lu-border); margin-bottom: 4px;}
.lu-opt span {width: 12px; height: 12px; border-radius: 50%; border: 1.5px solid var(--lu-silver-dim); flex: 0 0 auto;}
.lu-opt.on {border-color: rgba(95,214,160,0.6); background: rgba(47,181,122,0.12); color: #f2f6f4;}
.lu-opt.on span {border-color: #5fd6a0; background: radial-gradient(circle, #5fd6a0 45%, transparent 50%);}
.lu-txt {font-size: 0.8rem; color: var(--lu-ink-2); font-style: italic; background: rgba(0,0,0,0.25);
  border: 1px solid var(--lu-border); border-radius: 10px; padding: 8px 10px; min-height: 44px;}
.lu-ph-btn {margin: 12px 4px 6px 4px; text-align:center; font-weight: 700; font-size: 0.88rem; color: #f4fbf7;
  padding: 11px 0; border-radius: 14px; background: linear-gradient(135deg, #2fb57a, #17734b);
  box-shadow: 0 8px 20px -8px rgba(47,181,122,0.9);}
.lu-ph-foot {text-align:center; font-size: 0.62rem; color: var(--lu-muted);}
.lu-try {display:flex; align-items:center; gap: 22px; padding: 14px 18px; border-radius: 16px; border: 1px solid var(--lu-border);
  background: linear-gradient(160deg, rgba(18,42,31,0.9), rgba(10,24,18,0.9));}
.lu-try-v {font-family: var(--lu-serif); font-size: 2.6rem; font-weight: 700; color: #f2f6f4; line-height: 1;}
.lu-try-v span {font-size: 1rem; color: var(--lu-muted); margin-left: 2px;}
.lu-try-bar {flex: 1; height: 10px; border-radius: 99px; background: rgba(199,208,203,0.1); overflow: hidden;}
.lu-try-bar span {display:block; height: 100%; border-radius: 99px; transition: width 0.3s ease;}

/* ---- Markers (replace emojis) ---- */
.lu-mk {display:inline-block; width:7px; height:7px; border-radius:50%; margin-left:5px; vertical-align:middle; flex:0 0 auto;}
.lu-mk.pend {background:#d4b25f; box-shadow:0 0 0 2.5px rgba(212,178,95,0.18);}
.lu-mk.adj {background:transparent; border:1.5px solid #c7d0cb; width:8px; height:8px;}
.lu-mk.risk {background:#e46a6a; box-shadow:0 0 0 2.5px rgba(228,106,106,0.22);}
.lu-mk.prov {background:#5fd6a0; border-radius:1.5px; transform:rotate(45deg); width:6px; height:6px;}
.lu-mk.ok {background:#5fd6a0; box-shadow:0 0 0 2.5px rgba(95,214,160,0.18);}
.lu-mv {color:#c7d0cb; font-size:0.75rem; margin-left:4px; opacity:0.85;}
.lu-legend .lu-mk {margin:0 5px 0 0;}
.lu-legend span.item {margin-right:16px; white-space:nowrap;}

/* ---- Tables ---- */
.lu-table {width:100%; border-collapse:separate; border-spacing:0; font-size:0.86rem; margin: 2px 0 6px 0;
  border:1px solid var(--lu-border); border-radius:14px; overflow:hidden; background: rgba(10,23,17,0.6);}
.lu-table th {text-align:left; font-size:0.64rem; letter-spacing:0.14em; text-transform:uppercase; font-weight:600;
  color: var(--lu-silver-dim); padding:10px 14px; background: rgba(19,42,32,0.9); border-bottom:1px solid var(--lu-border);}
.lu-table td {padding:10px 14px; border-bottom:1px solid rgba(31,59,46,0.6); color: var(--lu-ink); vertical-align:middle;}
.lu-table tr:last-child td {border-bottom:none;}
.lu-table tbody tr:hover td {background: rgba(47,181,122,0.05);}
.lu-table td.src {color: var(--lu-ink-2); font-size:0.8rem; line-height:1.4;}
.lu-table td.num {text-align:right; font-variant-numeric: tabular-nums; white-space:nowrap;}
.lu-table td.name {font-weight:600; white-space:nowrap;}
.lu-table tfoot td {background: rgba(19,42,32,0.9); border-top:1px solid var(--lu-border-2); font-weight:600;}
.lu-table tfoot td.total {font-family: var(--lu-serif); font-size:1.35rem; color:#f2f6f4; text-align:right;}
.lu-bar {display:inline-block; width:92px; height:6px; border-radius:99px; background: rgba(199,208,203,0.1);
  vertical-align:middle; margin-right:8px; overflow:hidden;}
.lu-bar > span {display:block; height:100%; border-radius:99px; background: linear-gradient(90deg, #17734b, #5fd6a0);}
.lu-bar.risk > span {background: linear-gradient(90deg, #8a3a3a, #e46a6a);}

/* ---- Compact hero ---- */
.lu-hero.compact {padding: 16px 24px 15px 24px; border-radius:16px; margin-bottom:14px;}
.lu-hero.compact .lu-hero-title {font-size: 2rem;}
.lu-hero.compact .lu-hero-sub {margin-top:4px; font-size:0.88rem;}
.lu-hero.compact .lu-avatar {width:54px; height:54px; font-size:1.4rem;}
.lu-hero.compact:after {width:240px; height:240px; top:-110px;}

/* ---- Welcome screen ---- */
.lu-land {text-align:center; padding: 7vh 0 2vh 0; position:relative;}
.lu-land-logo svg {width:84px; height:84px; filter: drop-shadow(0 10px 30px rgba(47,181,122,0.45));}
.lu-land-kicker {font-size:0.72rem; letter-spacing:0.32em; text-transform:uppercase; color: var(--lu-emerald-bright);
  font-weight:600; margin-top:22px;}
.lu-land-title {font-family: var(--lu-serif); font-size: 5.4rem; font-weight:700; line-height:1; margin-top:10px;
  background: linear-gradient(180deg, #ffffff 10%, #9fb0a8 95%); -webkit-background-clip:text; background-clip:text;
  color:transparent;}
.lu-land-tag {font-family: var(--lu-serif); font-size: 1.75rem; font-style: italic; color: var(--lu-silver); margin-top:10px;}
.lu-land-sub {color: var(--lu-ink-2); font-size: 0.98rem; max-width: 640px; margin: 14px auto 0 auto; line-height:1.6;}
.lu-land-rule {width:120px; height:1px; margin: 26px auto; background: linear-gradient(90deg, transparent, #c7d0cb, transparent);}
.lu-feat {display:grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 6px 0 28px 0;}
.lu-feat div {text-align:left; padding: 16px 18px; border-radius: 16px; border:1px solid var(--lu-border);
  background: linear-gradient(160deg, rgba(18,42,31,0.85), rgba(10,24,18,0.85));}
.lu-feat b {display:block; font-family: var(--lu-serif); font-size: 1.25rem; color:#f2f6f4; margin-bottom: 4px;}
.lu-feat span {font-size: 0.82rem; color: var(--lu-ink-2); line-height:1.5;}
.lu-feat i {font-style:normal; font-size:0.62rem; letter-spacing:0.2em; color: var(--lu-emerald-bright); font-weight:700;}
.lu-land-foot {text-align:center; color: var(--lu-muted); font-size: 0.76rem; margin-top: 26px;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data & context
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _load(version):
    return engine.load_data()


def data_version():
    return engine.DB_PATH.stat().st_mtime_ns


def build_context(data, period):
    as_of = engine.period_end(period)
    dec = engine.decisions()
    active = [e for _, e in data["employees"].iterrows() if engine.is_active(e, as_of)]
    ctx = dict(as_of=as_of, period=period, dec=dec, rows={})
    quarters = engine.quarter_periods(data, as_of)
    prev_q = [q for q in quarters if engine.period_end(q) < as_of]
    prev_q = prev_q[-1] if prev_q else None
    for e in active:
        pl = engine.placement(data, e["id"], as_of)
        rk = engine.risk(data, e["id"], as_of)
        d = engine.latest_decision(dec, "9-box", e["id"], period)
        if d is None:
            status, eff, reason, actor = "pending", pl["box"], None, None
        else:
            status, eff, reason, actor = d["status"], d["final_value"], d["reason"], d["actor"]
            if d["algo_value"] != pl["box"]:
                # Data changed since the manager's decision (e.g. a new check-in): re-validation needed.
                status, eff, reason = "pending", pl["box"], f"Algorithm changed since last decision ({d['final_value']})"
        prev_box = None
        if prev_q and engine.is_active(e, engine.period_end(prev_q)):
            prev_box = engine.placement(data, e["id"], engine.period_end(prev_q))["box"]
        ctx["rows"][e["id"]] = dict(emp=e, pl=pl, rk=rk, status=status, box=eff, reason=reason, actor=actor,
                                    prev_box=prev_box, prev_q=prev_q)
    return ctx


def first(name):
    return name.split()[0]


def initials(name):
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper()


_card_n = [0]


def card():
    """Bordered container with the premium card styling (CSS targets the st-key-card_ class)."""
    _card_n[0] += 1
    return st.container(border=True, key=f"card_{_card_n[0]}")


def pill(text, bg, fg):
    return f'<span class="lu-pill" style="background:{bg};color:{fg}">{html.escape(text)}</span>'


def box_pill(box):
    bg, border, fg = BOX_STYLE[box]
    return (f'<span class="lu-pill" style="background:{bg};color:{fg};border-color:{border}">'
            f'{html.escape(box)}</span>')


def silver_pill(text):
    return pill(text, "rgba(199,208,203,0.07)", SILVER)


def risk_pill(rk):
    bg, fg, ic = RISK_STYLE[rk["level"]]
    return pill(f"{ic} {rk['model']}: {rk['level']}", bg, fg)


def mk(kind):
    return f'<span class="lu-mk {kind}"></span>'


def status_pill(status):
    styles = {"pending": ("pend", "Awaiting manager validation", "rgba(212,178,95,0.14)", "#e8cb84"),
              "confirmed": ("ok", "Confirmed by manager", "rgba(47,181,122,0.15)", "#7fe3b4"),
              "overridden": ("adj", "Adjusted by manager", "rgba(199,208,203,0.10)", "#e7efea")}
    if status not in styles:
        return silver_pill(status)
    k, text, bg, fg = styles[status]
    return (f'<span class="lu-pill" style="background:{bg};color:{fg}">{mk(k)}'
            f'&nbsp;{text}</span>')


def hero(title, sub=None, kicker=None, avatar=None, compact=True):
    kicker = kicker or f"{data['meta']['firm']} · Talent intelligence"
    av = f'<div class="lu-avatar">{html.escape(avatar)}</div>' if avatar else ""
    st.markdown(f'<div class="lu-hero{" compact" if compact else ""}"><div class="lu-hero-row">{av}<div>'
                f'<div class="lu-hero-kicker">{html.escape(kicker)}</div><div class="lu-hero-title">'
                f'{html.escape(title)}</div>' + (f'<div class="lu-hero-sub">{sub}</div>' if sub else "")
                + '</div></div></div>', unsafe_allow_html=True)


def section(title):
    st.markdown(f'<div class="lu-section"><span class="lu-section-title">{html.escape(title)}</span>'
                f'<span class="lu-section-line"></span></div>', unsafe_allow_html=True)


def hitl_banner(text=None):
    st.markdown(f'<div class="lu-hitl"><span class="lu-hitl-icon">◈</span><div><b>Human in the loop.</b> '
                f'{text or "Level UP proposes — people decide. Placements, risk flags, succession rankings and career suggestions are recommendations only; each needs a manager or HR action, and every action is logged."}'
                f'</div></div>', unsafe_allow_html=True)


def fig_base(fig, height=320, legend=True):
    fig.update_layout(template="plotly_dark", height=height, margin=dict(l=10, r=10, t=36, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, system-ui, sans-serif", size=12.5, color=INK2),
                      hoverlabel=dict(bgcolor="#0d1c15", bordercolor="#2b5240", font=dict(color=INK, size=13)),
                      showlegend=legend,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None, font=dict(color=INK2)))
    fig.update_xaxes(showgrid=False, linecolor="rgba(199,208,203,0.18)", tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)", tickfont=dict(color=MUTED),
                     title_font=dict(color=MUTED, size=12))
    return fig


# ---------------------------------------------------------------------------
# 9-box grid (HTML)
# ---------------------------------------------------------------------------
def render_grid(ctx, emp_ids, show_legend=True):
    cells = {}
    for eid in emp_ids:
        r = ctx["rows"][eid]
        icons = ""
        if r["status"] == "pending":
            icons += mk("pend")
        elif r["status"] == "overridden":
            icons += mk("adj")
        if r["rk"]["level"] == "High":
            icons += mk("risk")
        if r["pl"]["provisional"]:
            icons += mk("prov")
        if r["prev_box"] and r["prev_box"] != r["pl"]["box"]:
            icons += '<span class="lu-mv">↗</span>'
        tip = (f"{r['emp']['name']} — {r['pl']['title']}, {r['emp']['practice']}. Perf {r['pl']['perf']:.0f}, "
               f"Pot {r['pl']['pot']:.0f}. Algorithm: {r['pl']['box']}")
        if r["status"] == "overridden":
            tip += f" → manager: {r['box']}"
        if r["prev_box"] and r["prev_box"] != r["pl"]["box"]:
            tip += f". Last quarter: {r['prev_box']}"
        cells.setdefault(r["box"], []).append(
            f'<span class="lu-chip" title="{html.escape(tip)}"><span class="lu-ini">{initials(r["emp"]["name"])}</span>'
            f'{html.escape(r["emp"]["name"])}{icons}</span>')
    rows_html = []
    for pot_band, ylab in ((2, "HIGH"), (1, "MODERATE"), (0, "LOW")):
        cells_html = []
        for perf_band in (0, 1, 2):
            b = engine.BOXES[(pot_band, perf_band)]
            bg, border, fg = BOX_STYLE[b["name"]]
            chips = "".join(cells.get(b["name"], [])) or f'<span style="color:{MUTED};font-size:0.78rem">—</span>'
            count = len(cells.get(b["name"], []))
            cells_html.append(
                f'<div class="lu-cell" style="background:{bg};border:1px solid {border}">'
                f'<div class="lu-cell-title"><span style="color:{fg}"><span class="lu-cell-n">{b["n"]:02d}</span>'
                f'{b["name"]}</span><span class="lu-cell-count">{count}</span></div>'
                f'<div class="lu-cell-sub">{b["desc"]}</div>{chips}</div>')
        rows_html.append(f'<div class="lu-axis-y">{ylab}</div>' + "".join(cells_html))
    axis = ('<div></div><div class="lu-axis-x">LOW</div><div class="lu-axis-x">MODERATE</div>'
            '<div class="lu-axis-x">HIGH</div>')
    grid = (f'<div style="display:flex;gap:8px"><div style="display:flex;align-items:center"><div class="lu-axis-y" '
            f'style="color:{SILVER}">POTENTIAL →</div></div><div style="flex:1"><div class="lu-grid">'
            f'{"".join(rows_html)}{axis}</div><div class="lu-axis-x" style="color:{SILVER}">PERFORMANCE →</div>'
            f'</div></div>')
    st.markdown(grid, unsafe_allow_html=True)
    if show_legend:
        st.markdown(f'<div class="lu-legend"><span class="item">{mk("pend")}Awaiting manager validation</span>'
                    f'<span class="item">{mk("adj")}Adjusted by manager</span>'
                    f'<span class="item">{mk("risk")}High flight / onboarding risk</span>'
                    f'<span class="item">{mk("prov")}Provisional (no annual review yet)</span>'
                    f'<span class="item"><span class="lu-mv" style="margin:0 5px 0 0">↗</span>Moved since last quarter</span>'
                    f'<span class="item">Hover a name for scores</span></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def trajectory_chart(data, emp_id, as_of, current_box):
    hist = engine.box_history(data, emp_id, as_of)
    fig = go.Figure()
    lo, hi = engine.BAND_LOW, engine.BAND_HIGH
    for (pb, fb), b in engine.BOXES.items():
        x0, x1 = [(0, lo), (lo, hi), (hi, 100)][fb]
        y0, y1 = [(0, lo), (lo, hi), (hi, 100)][pb]
        is_cur = b["name"] == current_box
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      line=dict(color="rgba(95,214,160,0.85)" if is_cur else "#07110d", width=2 if is_cur else 3),
                      fillcolor=BOX_FILL[b["name"]], opacity=1 if is_cur else 0.8, layer="below")
        fig.add_annotation(x=(x0 + x1) / 2, y=y1 - 5, text=f"<b>{b['name']}</b>" if is_cur else b["name"],
                           showarrow=False, font=dict(size=14 if is_cur else 12.5, color=INK if is_cur else INK2,
                                                      family="Cormorant Garamond, Georgia, serif"))

    def frame_traces(k):
        h = hist.iloc[:k]
        labels = [""] * len(h)
        if len(h):
            labels[-1] = h["quarter"].iloc[-1]
        last = h.iloc[-1]
        return [
            go.Scatter(x=h["perf"], y=h["pot"], mode="lines+markers+text", text=labels, customdata=h["quarter"],
                       textposition="bottom center", textfont=dict(size=11, color=INK),
                       line=dict(color=SILVER, width=1.6, dash="dot"),
                       marker=dict(size=9, color=SILVER, line=dict(color="#07110d", width=2)),
                       hovertemplate="%{customdata}<br>Performance %{x:.0f}<br>Potential %{y:.0f}<extra></extra>"),
            go.Scatter(x=[last["perf"]], y=[last["pot"]], mode="markers", hoverinfo="skip",
                       marker=dict(size=26, color="rgba(95,214,160,0.22)")),
            go.Scatter(x=[last["perf"]], y=[last["pot"]], mode="markers", hoverinfo="skip",
                       marker=dict(size=14, color=EMERALD_BRIGHT, line=dict(color="#f2f6f4", width=2))),
        ]

    if not hist.empty:
        for tr in frame_traces(len(hist)):
            fig.add_trace(tr)
        if len(hist) > 1:
            fig.frames = [go.Frame(data=frame_traces(k), name=str(k)) for k in range(1, len(hist) + 1)]
            fig.update_layout(updatemenus=[dict(
                type="buttons", showactive=False, x=0.0, y=-0.13, xanchor="left", yanchor="top",
                bgcolor="#122a1f", bordercolor="#2b5240", borderwidth=1, font=dict(color=INK, size=12),
                pad=dict(l=8, r=8, t=4, b=4),
                buttons=[dict(label="▶  Replay trajectory", method="animate",
                              args=[None, dict(frame=dict(duration=750, redraw=True), fromcurrent=False,
                                               transition=dict(duration=450, easing="cubic-in-out"))])])])
    fig = fig_base(fig, 440, legend=False)
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=50))
    fig.update_xaxes(range=[0, 100], title="Performance score", showgrid=False, tickvals=[0, lo, hi, 100])
    fig.update_yaxes(range=[0, 100], title="Potential score", showgrid=False, tickvals=[0, lo, hi, 100])
    return fig


def engagement_story(data, as_of):
    """Cohort average in emerald, practices muted, and the practice that is slipping most highlighted."""
    p = data["pulses"]
    p = p[p["pulse_date"] <= as_of].merge(data["employees"][["id", "practice"]], left_on="emp_id", right_on="id")
    p["month"] = pd.to_datetime(p["pulse_date"]).dt.to_period("M").dt.to_timestamp()
    avg = p.groupby("month")["engagement_index"].mean()
    by = {pr: p[p["practice"] == pr].groupby("month")["engagement_index"].mean() for pr in PRACTICE_COLORS}
    lookback = min(4, len(avg) - 1)
    worst, worst_d = None, 0.0
    if lookback >= 2:
        for pr, s in by.items():
            if len(s) > lookback:
                dlt = s.iloc[-1] - s.iloc[-1 - lookback]
                if dlt < worst_d:
                    worst, worst_d = pr, dlt
    if worst_d > -3:
        worst = None
    fig = go.Figure()
    for pr, s in by.items():
        if pr == worst:
            continue
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=pr, line=dict(color="rgba(199,208,203,0.28)",
                                 width=1.3, shape="spline", smoothing=0.5),
                                 hovertemplate=f"{pr}: %{{y:.0f}}<extra></extra>"))
    if worst:
        s = by[worst]
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines+markers", name=worst,
                                 line=dict(color=RED, width=2.6, shape="spline", smoothing=0.5),
                                 marker=dict(size=6, color=RED), hovertemplate=f"{worst}: %{{y:.0f}}<extra></extra>"))
        fig.add_annotation(x=s.index[-1], y=s.values[-1], text=f"<b>{worst}</b><br>{worst_d:+.0f} pts",
                           xanchor="left", xshift=8, showarrow=False, align="left", font=dict(size=12, color="#ff9b93"))
        start = s.index[-1 - lookback]
        fig.add_vrect(x0=start, x1=s.index[-1], fillcolor="rgba(228,106,106,0.06)", line_width=0)
    fig.add_trace(go.Scatter(x=avg.index, y=avg.values, mode="lines+markers", name="Cohort average",
                             line=dict(color=EMERALD_BRIGHT, width=3.4, shape="spline", smoothing=0.5),
                             marker=dict(size=7, color=EMERALD_BRIGHT, line=dict(color="#07110d", width=2)),
                             hovertemplate="Cohort average: %{y:.0f}<extra></extra>"))
    fig.add_annotation(x=avg.index[-1], y=avg.values[-1], text=f"<b>Cohort {avg.values[-1]:.0f}</b>", xanchor="left",
                       xshift=8, yshift=(16 if worst and avg.values[-1] >= by[worst].values[-1] else -16) if worst else 0,
                       showarrow=False, font=dict(size=12, color=EMERALD_BRIGHT))
    fig = fig_base(fig, 340, legend=False)
    fig.update_layout(margin=dict(l=10, r=120, t=20, b=10), hovermode="x unified")
    vals = pd.concat([avg] + list(by.values()))
    fig.update_yaxes(range=[max(0, vals.min() - 6), min(100, vals.max() + 6)], title="Engagement index")
    fig.update_xaxes(range=[avg.index[0] - pd.Timedelta(days=8), avg.index[-1] + pd.Timedelta(days=12)],
                     dtick="M2", tickformat="%b %y")
    if worst:
        headline = f"{worst} engagement down {abs(worst_d):.0f} pts in {lookback} months"
    elif lookback >= 2:
        headline = f"Engagement {'up' if avg.iloc[-1] >= avg.iloc[-1 - lookback] else 'down'} " \
                   f"{abs(avg.iloc[-1] - avg.iloc[-1 - lookback]):.0f} pts in {lookback} months"
    else:
        headline = "Engagement trend"
    return fig, headline


def monthly_series(fn):
    """Apply fn(as_of) to every month-end up to the selected date (for metric sparklines)."""
    return [fn(engine.period_end(p)) for p in PERIODS if engine.period_end(p) <= as_of]


def count_risk(ids_fn, model, levels, when):
    n = 0
    for e in ids_fn(when):
        rk = engine.risk(data, e, when)
        if rk["model"] == model and rk["level"] in levels:
            n += 1
    return n


def active_ids(when, among=None):
    return [e for e, emp in data["emp_by_id"].items() if emp["start_date"] <= when and (among is None or e in among)]


def engagement_chart(series, title=None):
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=50, fillcolor="rgba(228,106,106,0.07)", line_width=0)
    fig.add_trace(go.Scatter(x=series["pulse_date"], y=series["engagement_index"], mode="lines+markers",
                             line=dict(color=EMERALD_BRIGHT, width=2.5, shape="spline", smoothing=0.6),
                             fill="tozeroy", fillcolor="rgba(95,214,160,0.08)",
                             marker=dict(size=8, color=EMERALD_BRIGHT, line=dict(color="#07110d", width=2)),
                             name="Engagement index", hovertemplate="%{x|%b %Y}: %{y:.0f}/100<extra></extra>"))
    fig = fig_base(fig, 270, legend=False)
    fig.update_yaxes(range=[0, 100], title="Engagement index (0-100)")
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=13, color=INK)))
    return fig


def pulse_detail_chart(series):
    fig = go.Figure()
    for col, label, color in (("engagement", "Engagement", EMERALD_BRIGHT), ("sentiment", "Sentiment", BLUE),
                              ("workload", "Workload (6 = healthy)", GOLD)):
        fig.add_trace(go.Scatter(x=series["pulse_date"], y=series[col], mode="lines+markers", name=label,
                                 line=dict(color=color, width=2), marker=dict(size=7, line=dict(color="#07110d", width=1.5)),
                                 hovertemplate=f"{label}: %{{y:.1f}}/10<extra></extra>"))
    fig = fig_base(fig, 270)
    fig.update_yaxes(range=[0, 10.5], title="Pulse answer (1-10)")
    fig.update_layout(hovermode="x unified")
    return fig


def org_engagement_chart(data, as_of, emp_ids=None):
    p = data["pulses"]
    p = p[p["pulse_date"] <= as_of].merge(data["employees"][["id", "practice"]], left_on="emp_id", right_on="id")
    if emp_ids is not None:
        p = p[p["emp_id"].isin(emp_ids)]
    p["month"] = pd.to_datetime(p["pulse_date"]).dt.to_period("M").dt.to_timestamp()
    fig = go.Figure()
    if emp_ids is None:
        for prac, color in PRACTICE_COLORS.items():
            s = p[p["practice"] == prac].groupby("month")["engagement_index"].mean()
            fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=prac,
                                     line=dict(color=color, width=1.8, shape="spline", smoothing=0.5), opacity=0.85,
                                     hovertemplate=f"{prac}: %{{y:.0f}}<extra></extra>"))
    s = p.groupby("month")["engagement_index"].mean()
    fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines+markers", name="Cohort average",
                             line=dict(color="#f2f6f4", width=3, shape="spline", smoothing=0.5),
                             marker=dict(size=7, color="#f2f6f4", line=dict(color="#07110d", width=2)),
                             hovertemplate="Average: %{y:.0f}<extra></extra>"))
    fig = fig_base(fig, 330)
    fig.update_yaxes(range=[30, 90], title="Engagement index")
    fig.update_layout(hovermode="x unified")
    return fig


def html_table(df, bar_cols=("Weight",), name_col=None):
    """Styled HTML table. Columns listed in bar_cols hold 'NN%' strings and get a mini bar."""
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = []
    for _, row in df.iterrows():
        tds = []
        for c in df.columns:
            v = str(row[c])
            if c in bar_cols:
                pct = float(v.rstrip("%"))
                tds.append(f'<td class="num" style="text-align:left"><span class="lu-bar" style="width:70px">'
                           f'<span style="width:{min(100, pct * 2):.0f}%"></span></span>{html.escape(v)}</td>')
            elif c == (name_col or df.columns[0]):
                tds.append(f'<td class="name">{html.escape(v)}</td>')
            else:
                tds.append(f'<td class="src">{html.escape(v)}</td>')
        body.append("<tr>" + "".join(tds) + "</tr>")
    st.markdown(f'<table class="lu-table"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>',
                unsafe_allow_html=True)


def contributions_table(components, total, label, risk=False):
    rows = []
    for c in components:
        rows.append(
            f'<tr><td class="name">{html.escape(c["component"])}</td><td class="num">{c["weight"]:.0%}</td>'
            f'<td class="num" style="text-align:left"><span class="lu-bar{" risk" if risk else ""}">'
            f'<span style="width:{c["score"]:.0f}%"></span></span>{c["score"]:.0f}</td>'
            f'<td class="num">{c["contribution"]:.1f}</td><td class="src">{html.escape(c["source"])}</td></tr>')
    formula = " + ".join(f"{c['weight']:.2f}×{c['score']:.0f}" for c in components)
    st.markdown(
        f'<table class="lu-table"><thead><tr><th>Component</th><th>Weight</th><th>Score (0-100)</th><th>Points</th>'
        f'<th>Where it comes from</th></tr></thead><tbody>{"".join(rows)}</tbody><tfoot><tr>'
        f'<td colspan="3">{html.escape(label)} score</td><td class="total">{total:.1f}</td>'
        f'<td class="src">{formula}</td></tr></tfoot></table>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
data = _load(data_version())
PERIODS = engine.periods(data)
MANAGERS = [m for m in data["employees"]["id"] if (data["employees"]["manager_id"] == m).any()]

PAGE_ICONS = {"Overview": ":material/space_dashboard:", "Org 9-box": ":material/grid_view:",
              "Succession": ":material/account_tree:", "Engagement": ":material/monitoring:",
              "Employee profile": ":material/person:", "Decision log": ":material/history_edu:",
              "Methodology": ":material/functions:", "Employee surveys": ":material/assignment:", "My team": ":material/groups:"}

def landing():
    st.markdown("""<style>
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] {display:none !important;}
    [data-testid="stMainBlockContainer"] {max-width: 1080px;}
    </style>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="lu-land">
      <div class="lu-land-logo">{LOGO}</div>
      <div class="lu-land-kicker">{html.escape(data['meta']['firm'])} · Talent intelligence</div>
      <div class="lu-land-title">Level UP</div>
      <div class="lu-land-tag">Every talent trajectory, read continuously.</div>
      <div class="lu-land-sub">AI-assisted 9-box, engagement tracking and succession matching for a 250-person
      consulting firm. The algorithm proposes — people decide.</div>
      <div class="lu-land-rule"></div>
    </div>
    <div class="lu-feat">
      <div><i>01 · PLACE</i><b>Automatic 9-box</b><span>Performance × potential from reviews, check-ins, surveys and
      skills — fully explainable, validated by managers.</span></div>
      <div><i>02 · DETECT</i><b>Risk signals</b><span>Monthly pulses reveal disengagement early, with a dedicated
      model for new hires' first 90 days.</span></div>
      <div><i>03 · GROW</i><b>Succession & paths</b><span>Ranked internal candidates for open roles and a suggested
      trajectory for every employee.</span></div>
    </div>""", unsafe_allow_html=True)
    _, c1, c2, _ = st.columns([0.25, 1, 1, 0.25], gap="medium")
    if c1.button(f"Enter as HR  ·  {HR_NAME}", type="primary", width="stretch", icon=":material/badge:"):
        st.session_state.update(entered=True, role="HR / People team", page="Overview")
        st.rerun()
    if c2.button(f"Enter as Manager  ·  {data['names'][MANAGERS[0]]}", width="stretch",
                 icon=":material/supervisor_account:"):
        st.session_state.update(entered=True, role="Manager", manager_id=MANAGERS[0], page="My team")
        st.rerun()
    st.markdown('<div class="lu-land-foot">Demo prototype · fictional data · business school group project</div>',
                unsafe_allow_html=True)


PRESENT_CSS = """<style>
html {font-size: 17.5px;}
:root {--lu-ink:#ffffff; --lu-ink-2:#d6e3dc; --lu-muted:#a3b8ad; --lu-silver-dim:#b9c8c0;
  --lu-border:#2f5a46; --lu-border-2:#468a6a;}
.stApp {background: radial-gradient(1100px 520px at 85% -8%, rgba(47,181,122,0.22), transparent 60%), #0f241a !important;}
[data-testid="stMetric"], [class*="st-key-card_"], .lu-user, .lu-time {background: #173828 !important;}
.lu-hero {background: linear-gradient(120deg, #1d4a35, #153527) !important;}
.lu-table {background: #132e22;} .lu-table td {color:#ffffff;}
.lu-cell-sub, .lu-sb-note, .lu-legend {color: #d6e3dc !important;}
.lu-chip {background: rgba(5,14,10,0.7); font-size: 0.85rem;}
section[data-testid="stSidebar"] {width: 330px !important; min-width: 330px !important;}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button p {font-size: 0.8rem !important;}
</style>"""

if not st.session_state.get("entered"):
    landing()
    st.stop()

PAGE_LABELS = {"Org 9-box": "9-box", "Employee profile": "Profiles", "Employee surveys": "Surveys",
               "Decision log": "Decisions", "Methodology": "Method & ethics"}

with st.sidebar:
    st.markdown(f'<div class="lu-brand">{LOGO}<div><div class="lu-brand-name">Level UP</div>'
                f'<div class="lu-brand-tag">Talent trajectories</div></div></div>', unsafe_allow_html=True)

    if st.session_state.get("role") not in ("HR / People team", "Manager"):
        st.session_state["role"] = "HR / People team"
    role = st.segmented_control("View as", ["HR / People team", "Manager"],
                                key="role", label_visibility="collapsed",
                                format_func=lambda r: {"HR / People team": ":material/badge: HR",
                                                       "Manager": ":material/supervisor_account: Manager"}[r])
    role = role or "HR / People team"
    manager_id = None
    if role == "Manager":
        manager_id = st.selectbox("Manager", MANAGERS, label_visibility="collapsed",
                                  format_func=lambda m: f"Signed in as {data['names'][m]}", key="manager_id")
        pages = ["My team", "Employee profile", "Employee surveys", "Decision log", "Methodology"]
        actor = data["names"][manager_id]
        who_name, who_role = actor, f"{data['emp_by_id'][manager_id]['title']} · {data['emp_by_id'][manager_id]['practice']}"
    else:
        pages = ["Overview", "Org 9-box", "Succession", "Engagement", "Employee profile", "Employee surveys",
                 "Decision log", "Methodology"]
        actor = HR_ACTOR
        who_name, who_role = HR_NAME, "HR Business Partner"
    if role != "Manager":
        st.markdown(f'<div class="lu-user"><div class="lu-user-av">{initials(who_name)}</div><div style="min-width:0">'
                    f'<div class="lu-user-name">{html.escape(who_name)}</div>'
                    f'<div class="lu-user-role">{html.escape(who_role)}</div></div>'
                    f'<span class="lu-user-dot" title="Signed in"></span></div>', unsafe_allow_html=True)

    if st.session_state.get("goto") in pages:
        st.session_state["page"] = st.session_state.pop("goto")
    if st.session_state.get("page") not in pages:
        st.session_state["page"] = pages[0]
    st.markdown('<div class="lu-sb-gap"></div>', unsafe_allow_html=True)
    page = st.radio("Navigation", pages, key="page", label_visibility="collapsed",
                    format_func=lambda p: f"{PAGE_ICONS[p]}&nbsp;&nbsp;{PAGE_LABELS.get(p, p)}")

    cur = st.session_state.get("period", PERIODS[-1])
    live = cur == PERIODS[-1]
    st.markdown(f'<div class="lu-time"><div class="lu-time-row"><div><div class="lu-time-k">Data up to</div>'
                f'<span class="lu-time-v">{engine.period_label(cur)}</span></div>'
                f'<span class="lu-time-tag {"live" if live else "replay"}">{"● Live" if live else "↺ Replay"}</span>'
                f'</div></div>', unsafe_allow_html=True)
    period = st.select_slider("Timeline", options=PERIODS, value=PERIODS[-1], label_visibility="collapsed",
                              format_func=lambda p: engine.period_label(p)[:3] + " " + p[2:4], key="period",
                              help="Replay the simulated year: scores, boxes and trends recompute from the data "
                                   "available at that date.")

    st.markdown('<div class="lu-sb-gap"></div>', unsafe_allow_html=True)
    with st.popover("Settings", icon=":material/tune:", width="stretch"):
        present = st.toggle("Projector mode", key="present",
                            help="Brighter surfaces and larger text for video projectors")
        if st.button("Reset demo data", icon=":material/restart_alt:", width="stretch",
                     help="Re-run seed.py: restores the original dataset and clears new decisions"):
            seed.build()
            st.cache_resource.clear()
            st.rerun()
        if st.button("Back to welcome screen", icon=":material/logout:", width="stretch"):
            st.session_state["entered"] = False
            st.rerun()
        st.caption(f"{data['meta']['firm']} · {data['meta']['headcount']} people · pilot cohort of 18 · "
                   "fictional data")

if present:
    st.markdown(PRESENT_CSS, unsafe_allow_html=True)
    INK2, MUTED, GRID = "#d6e3dc", "#a3b8ad", "rgba(199,208,203,0.14)"

ctx = build_context(data, period)
as_of = ctx["as_of"]
team_ids = [eid for eid in ctx["rows"] if ctx["rows"][eid]["emp"]["manager_id"] == manager_id] if manager_id else None
visible_ids = team_ids if role == "Manager" else list(ctx["rows"].keys())


def open_profile(emp_id):
    st.session_state["profile_emp"] = emp_id
    st.session_state["goto"] = "Employee profile"


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------
def risk_flag_list(ids, key_prefix):
    flagged = [eid for eid in ids if ctx["rows"][eid]["rk"]["level"] in ("High", "Medium")]
    flagged.sort(key=lambda e: -ctx["rows"][e]["rk"]["score"])
    if not flagged:
        st.success("No risk flags at this date.")
        return
    for eid in flagged:
        r = ctx["rows"][eid]
        rk = r["rk"]
        top = max(rk["components"], key=lambda c: c["contribution"])
        bg, fg, ic = RISK_STYLE[rk["level"]]
        d = engine.latest_decision(ctx["dec"], "Risk flag", eid, period)
        with card():
            st.markdown(f"**{r['emp']['name']}** · {r['pl']['title']}, {r['emp']['practice']}  \n"
                        f"{risk_pill(rk)} <span style='color:{INK2};font-size:0.85rem'>score {rk['score']:.0f}/100 "
                        f"· engagement trend: {rk['trend'].lower()}</span>", unsafe_allow_html=True)
            st.caption(f"Main driver: {top['component']} — {top['source']}")
            if d is not None:
                c1, c2 = st.columns([2.6, 1])
                c1.markdown(f"{mk('ok')}&nbsp; **{d['final_value']}** <span style='font-size:0.8rem;color:{MUTED}'>"
                            f"— {d['actor']}</span>", unsafe_allow_html=True)
                if c2.button("Profile", key=f"{key_prefix}_open_{eid}", width="stretch"):
                    open_profile(eid)
                    st.rerun()
            else:
                choice = st.selectbox("Action", ["Schedule stay conversation", "Review workload & staffing",
                                                 "Monitor — no action now", "Dismiss (false positive)"],
                                      key=f"{key_prefix}_act_{eid}", label_visibility="collapsed")
                c2, c3 = st.columns(2)
                if c2.button("Log action", key=f"{key_prefix}_btn_{eid}", type="primary", width="stretch",
                             icon=":material/check:"):
                    engine.log_decision(actor, "Manager" if manager_id else "HR", "Risk flag", eid, None, period,
                                        f"{rk['model']} {rk['level']} ({rk['score']:.0f})", choice,
                                        "acknowledged", None)
                    st.rerun()
                if c3.button("Open profile", key=f"{key_prefix}_open_{eid}", width="stretch"):
                    open_profile(eid)
                    st.rerun()


def profile_picker(ids, key):
    c1, c2 = st.columns([3, 1])
    with c1:
        sel = st.selectbox("Open an employee profile", ids, key=key,
                           format_func=lambda e: f"{data['names'][e]} — {ctx['rows'][e]['box']}")
    with c2:
        st.write("")
        st.write("")
        if st.button("Open profile →", key=key + "_go", width="stretch"):
            open_profile(sel)
            st.rerun()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def page_overview():
    hero("People overview", f"Data as of <b>{as_of:%d %b %Y}</b> · pilot cohort of {len(ctx['rows'])} employees "
         "from a 250-person firm across Strategy, HR Consulting, Finance &amp; Transactions and Operations.",
         compact=False)
    hitl_banner()
    rows = ctx["rows"].values()
    pending = sum(1 for r in rows if r["status"] == "pending")
    flight = [r for r in rows if r["rk"]["model"] == "Flight risk" and r["rk"]["level"] == "High"]
    onboard = [r for r in rows if r["rk"]["model"] == "Onboarding risk"]
    onboard_flag = [r for r in onboard if r["rk"]["level"] != "Low"]
    p = data["pulses"][data["pulses"]["pulse_date"] <= as_of].copy()
    p["m"] = pd.to_datetime(p["pulse_date"]).dt.to_period("M")
    monthly = p.groupby("m")["engagement_index"].mean()
    c = st.columns(5)
    c[0].metric("In view", f"{len(ctx['rows'])}", help="Pilot cohort out of 250 staff")
    c[1].metric("To validate", pending, help="9-box placements awaiting manager validation")
    fr = monthly_series(lambda w: count_risk(active_ids, "Flight risk", ("High",), w))
    c[2].metric("Flight risk", len(flight), (f"{fr[-1] - fr[-4]:+d} vs 3 mo" if len(fr) >= 4 else None),
                delta_color="inverse", help="Employees with a High flight-risk flag — monthly trend below",
                chart_data=fr, chart_type="bar")
    c[3].metric("Onboarding", f"{len(onboard_flag)}/{len(onboard)}", help="New hires flagged by the onboarding risk model")
    if len(monthly) >= 4:
        c[4].metric("Engagement", f"{monthly.iloc[-1]:.0f}", f"{monthly.iloc[-1] - monthly.iloc[-4]:+.1f} vs 3 mo",
                    chart_data=[round(v, 1) for v in monthly.values], chart_type="area")
    elif len(monthly):
        c[4].metric("Engagement", f"{monthly.iloc[-1]:.0f}")

    left, right = st.columns([1.55, 1], gap="large")
    with left:
        fig, headline = engagement_story(data, as_of)
        section(headline)
        st.plotly_chart(fig, key="org_eng")
        st.caption("Monthly pulse surveys → engagement index (engagement 50%, sentiment 30%, workload balance 20%). "
                   "Emerald = cohort average; red = the practice slipping most; other practices muted.")
        section("Distribution across the 9-box")
        counts = pd.Series([r["box"] for r in rows]).value_counts()
        dist = pd.DataFrame({"Box": engine.BOX_ORDER, "Employees": [int(counts.get(b, 0)) for b in engine.BOX_ORDER]})
        fig = go.Figure(go.Bar(x=dist["Employees"], y=dist["Box"], orientation="h", marker_color=EMERALD,
                               hovertemplate="%{y}: %{x}<extra></extra>", text=dist["Employees"],
                               textposition="outside"))
        fig = fig_base(fig, 300, legend=False)
        fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
        fig.update_xaxes(visible=False)
        st.plotly_chart(fig, key="dist")
    with right:
        section("Risk flags needing a decision")
        st.caption("Flight risk for established staff; a separate onboarding model for people in their first 90 days.")
        risk_flag_list(list(ctx["rows"].keys()), "ov")


def page_grid():
    hero("Org 9-box", f"Algorithmic placement as of <b>{as_of:%d %b %Y}</b>, shown after any manager adjustment.")
    hitl_banner("The algorithm places each person; their manager confirms or adjusts. Pending placements are shown "
                "with a gold dot and are not used for decisions until validated.")
    c1, c2 = st.columns([1, 1])
    with c1:
        practices = st.pills("Practice", list(PRACTICE_COLORS), selection_mode="multi",
                             default=list(PRACTICE_COLORS)) or []
    with c2:
        bands = ["New hire (<90 days)", "Early-career", "Mid-tenure", "Senior / long tenure"]
        tb = st.pills("Tenure", bands, selection_mode="multi", default=bands) or []
    ids = [e for e, r in ctx["rows"].items() if r["emp"]["practice"] in practices
           and engine.tenure_band(r["emp"], as_of) in tb]
    render_grid(ctx, ids)
    st.write("")
    section("Placement details")
    tbl = []
    for e in ids:
        r = ctx["rows"][e]
        tbl.append({"Employee": r["emp"]["name"], "Title": r["pl"]["title"], "Practice": r["emp"]["practice"],
                    "Tenure": engine.tenure_label(r["emp"], as_of), "Performance": r["pl"]["perf"],
                    "Potential": r["pl"]["pot"], "Algorithm": r["pl"]["box"], "Final": r["box"],
                    "Last quarter": r["prev_box"] or "—",
                    "Status": {"pending": "Pending", "confirmed": "Confirmed", "overridden": "Adjusted"}.get(
                        r["status"], r["status"]),
                    "Risk": f"{r['rk']['level']} ({r['rk']['model'].split()[0].lower()})"})
    st.dataframe(pd.DataFrame(tbl), hide_index=True, column_config={
        "Performance": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
        "Potential": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f")})
    profile_picker(ids, "grid_pick")


def page_succession():
    hero("Succession matching", "Rank internal candidates for open roles — weighted by 9-box position, skills, "
         "readiness and aspiration.")
    hitl_banner("Rankings are a starting point for a talent conversation. Shortlisting is an HR decision — "
                "employees are not notified and nothing is offered automatically.")
    vac = data["vacancies"]
    vid = st.selectbox("Vacant role", vac["id"], format_func=lambda v: vac.set_index("id").loc[v, "title"])
    v = vac.set_index("id").loc[vid]
    v = dict(v, id=vid)
    with card():
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"### {v['title']}")
            st.write(v["context"])
            st.markdown("**Required skills:** " + " ".join(silver_pill(s) for s in v["skills"]),
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='lu-kicker'>Grade</div>{engine.LEVEL_NAMES[v['level']]} (level {v['level']})",
                        unsafe_allow_html=True)
            st.markdown(f"<div class='lu-kicker'>Practice</div>{v['practice']}", unsafe_allow_html=True)
            st.markdown(f"<div class='lu-kicker'>Hiring manager</div>{v['hiring_manager']}", unsafe_allow_html=True)
            st.markdown(f"<div class='lu-kicker'>Opened</div>{v['opened']}", unsafe_allow_html=True)
    eff = {e: r["box"] for e, r in ctx["rows"].items()}
    df = engine.succession(data, v, as_of, eff)
    weights = " · ".join(f"{k} {int(w * 100)}%" for k, w in engine.SUCCESSION_WEIGHTS.items())
    st.caption(f"Match score = {weights}. Candidates considered: same grade (other practices) up to two grades below. "
               "9-box position uses the manager-validated box where available.")
    if df.empty:
        st.info("No internal candidates in the pilot cohort for this role.")
        return
    elig = df[df["eligible"]]
    section(f"Top internal candidates ({len(elig)} eligible)")
    for i, row in elig.head(5).iterrows():
        d = engine.latest_decision(ctx["dec"], "Succession", row["emp_id"], vacancy_id=vid)
        with card():
            c1, c2, c3 = st.columns([0.35, 3, 1.4])
            c1.markdown(f"<div class='lu-rank'>{i + 1:02d}</div>",
                        unsafe_allow_html=True)
            with c2:
                b = engine.BOX_BY_NAME[row["box"]][1]
                st.markdown(f"**{row['name']}** · {row['title']}, {row['practice']}  \n"
                            f"{box_pill(row['box'])} {silver_pill(row['readiness'])} "
                            f"<span style='color:{INK2}'>match <b>{row['score']:.0f}</b>/100</span>",
                            unsafe_allow_html=True)
                st.caption("Why: " + row["rationale"])
                if row["flags"]:
                    st.markdown(f"<span style='font-size:0.85rem;color:#ff9b93'>{html.escape(row['flags'])}</span>",
                                unsafe_allow_html=True)
                st.progress(int(row["score"]) / 100)
            with c3:
                if d is not None and d["status"] != "reopened":
                    st.markdown(f"**{'★ Shortlisted' if d['status'] == 'shortlisted' else '✕ Not pursued'}**  \n"
                                f"<span style='font-size:0.8rem;color:{MUTED}'>{d['actor']} · {d['ts'][:10]}</span>",
                                unsafe_allow_html=True)
                    if st.button("Undo", key=f"undo_{vid}_{row['emp_id']}"):
                        engine.log_decision(actor, "HR", "Succession", row["emp_id"], vid, period,
                                            f"rank #{i + 1} ({row['score']:.0f})", "Re-opened", "reopened",
                                            "Decision re-opened")
                        st.rerun()
                else:
                    if st.button("Shortlist", key=f"sl_{vid}_{row['emp_id']}", type="primary", icon=":material/star:",
                                 width="stretch"):
                        engine.log_decision(actor, "HR", "Succession", row["emp_id"], vid, period,
                                            f"rank #{i + 1} ({row['score']:.0f})", "Shortlisted", "shortlisted",
                                            None)
                        st.rerun()
                    if st.button("Not pursued", key=f"np_{vid}_{row['emp_id']}", width="stretch"):
                        engine.log_decision(actor, "HR", "Succession", row["emp_id"], vid, period,
                                            f"rank #{i + 1} ({row['score']:.0f})", "Not pursued", "dismissed", None)
                        st.rerun()
    with st.expander("Full ranking and score components (incl. ineligible)"):
        rows = []
        for _, x in df.iterrows():
            rows.append(
                f'<tr><td class="name">{html.escape(x["name"])}<div class="lu-q-h">{html.escape(x["title"])} · '
                f'{html.escape(x["practice"])}</div></td><td>{box_pill(x["box"])}</td>'
                + "".join(f'<td class="num">{x[k]:.0f}</td>' for k in ("9-box position", "Skills match",
                                                                      "Readiness (level gap)",
                                                                      "Aspiration & mobility fit"))
                + f'<td class="num" style="text-align:left"><span class="lu-bar" style="width:60px"><span '
                  f'style="width:{x["raw_score"]:.0f}%"></span></span>{x["raw_score"]:.0f}</td>'
                  f'<td class="src">{"Eligible" if x["eligible"] else "Not eligible"} · {html.escape(x["readiness"])}'
                  f'{("<br>" + html.escape(x["flags"])) if x["flags"] else ""}</td></tr>')
        st.markdown('<table class="lu-table"><thead><tr><th>Candidate</th><th>9-box</th><th>Box</th><th>Skills</th>'
                    '<th>Readiness</th><th>Fit</th><th>Match</th><th>Notes</th></tr></thead><tbody>'
                    + "".join(rows) + '</tbody></table>', unsafe_allow_html=True)
        st.caption("Component scores are 0-100 before weighting (box 40%, skills 25%, readiness 20%, fit 15%).")


def page_engagement():
    hero("Engagement & disengagement", "A continuous signal from monthly pulse surveys — not an annual snapshot.")
    hitl_banner("Trends flag where to look; a manager conversation decides what (if anything) to do.")
    ids = visible_ids
    p = data["pulses"][(data["pulses"]["pulse_date"] <= as_of) & (data["pulses"]["emp_id"].isin(ids))].copy()
    p["month"] = pd.to_datetime(p["pulse_date"]).dt.strftime("%b %y")
    order = [engine.period_label(x)[:3] + " " + x[2:4] for x in PERIODS if engine.period_end(x) <= as_of]
    mat = p.pivot_table(index="emp_id", columns="month", values="engagement_index").reindex(columns=order)
    labels = []
    trends = {}
    for e in mat.index:
        trends[e] = ctx["rows"][e]["rk"]["trend"]
    mat = mat.loc[sorted(mat.index, key=lambda e: (data["emp_by_id"][e]["practice"], data["names"][e]))]
    labels = [f"{data['names'][e]} ({trends[e].lower()})" for e in mat.index]
    c = st.columns(3)
    vals = list(trends.values())
    c[0].metric("Improving", vals.count("Improving"))
    c[1].metric("Stable", vals.count("Stable") + vals.count("Too early"))
    c[2].metric("Declining", vals.count("Declining"))
    fig = go.Figure(go.Heatmap(z=mat.values, x=mat.columns, y=labels, zmin=30, zmax=90,
                               colorscale=[[0, "#10261c"], [0.5, "#1f8a5b"], [1, "#9ff0c9"]],
                               colorbar=dict(title=dict(text="Index", font=dict(color=MUTED)), thickness=10,
                                             outlinewidth=0, tickfont=dict(color=MUTED)), xgap=3, ygap=3,
                               hovertemplate="%{y}<br>%{x}: %{z:.0f}/100<extra></extra>"))
    fig = fig_base(fig, 40 + 28 * len(labels), legend=False)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
    section("Engagement index per employee per month")
    st.plotly_chart(fig, key="heat")
    st.caption("Darker = more engaged. Blank = not yet employed / no pulse. Trend = slope of the last 6 pulses.")
    sel = st.selectbox("Inspect one employee", list(mat.index), format_func=lambda e: data["names"][e])
    s = engine.engagement_series(data, sel, as_of)
    c1, c2 = st.columns(2)
    c1.plotly_chart(engagement_chart(s, "Engagement index"), key="eng1")
    c2.plotly_chart(pulse_detail_chart(s), key="eng2")


def validation_panel(eid):
    r = ctx["rows"][eid]
    pl = r["pl"]
    is_manager = manager_id is not None and r["emp"]["manager_id"] == manager_id
    with card():
        st.markdown("<div class='lu-kicker'>Manager validation</div>", unsafe_allow_html=True)
        st.markdown(f"Algorithm proposes **{pl['box']}**  \n{status_pill(r['status'])}", unsafe_allow_html=True)
        if r["status"] in ("confirmed", "overridden"):
            st.caption(f"{r['actor']}: final box **{r['box']}**" + (f" — “{r['reason']}”" if r["reason"] else ""))
        elif r["reason"]:
            st.caption(r["reason"])
        if not is_manager:
            st.caption("Only the employee's manager can validate. HR sees the status.")
            return
        if r["status"] == "pending":
            if st.button("Confirm placement", type="primary", key=f"conf_{eid}", width="stretch"):
                engine.log_decision(actor, "Manager", "9-box", eid, None, period, pl["box"], pl["box"], "confirmed",
                                    "Agree with proposed placement.")
                st.rerun()
        with st.expander("Adjust placement" if r["status"] == "pending" else "Change decision"):
            with st.form(f"ovr_{eid}"):
                opts = engine.BOX_ORDER
                new_box = st.selectbox("Final box", opts, index=opts.index(r["box"]))
                reason = st.text_area("Reason (required — recorded in the audit log)",
                                      placeholder="e.g. Context the data doesn't capture…")
                if st.form_submit_button("Submit decision"):
                    if not reason.strip():
                        st.error("Please give a reason.")
                    else:
                        status = "confirmed" if new_box == pl["box"] else "overridden"
                        engine.log_decision(actor, "Manager", "9-box", eid, None, period, pl["box"], new_box, status,
                                            reason.strip())
                        st.rerun()


def page_profile():
    ids = visible_ids
    if not ids:
        st.info("No employees at this date.")
        return
    default = st.session_state.get("profile_emp")
    idx = ids.index(default) if default in ids else 0
    eid = st.selectbox("Employee", ids, index=idx, format_func=lambda e: f"{data['names'][e]} — "
                       f"{ctx['rows'][e]['pl']['title']}, {ctx['rows'][e]['emp']['practice']}")
    st.session_state["profile_emp"] = eid
    r = ctx["rows"][eid]
    emp, pl, rk = r["emp"], r["pl"], r["rk"]
    mgr = data["names"].get(emp["manager_id"]) or emp["manager_ext"]

    pills = [box_pill(r["box"]), risk_pill(rk), silver_pill(engine.tenure_band(emp, as_of))]
    if pl["provisional"]:
        pills.append(f'<span class="lu-pill" style="background:rgba(47,181,122,0.12);color:#7fe3b4">{mk("prov")}'
                     f'&nbsp; Provisional — no annual review yet</span>')
    hero(emp["name"], f"{pl['title']} · {html.escape(emp['practice'])} · reports to <b>{html.escape(mgr)}</b> · "
         f"joined {emp['start_date']:%d %b %Y} ({engine.tenure_label(emp, as_of)})"
         f"<div style='margin-top:12px'>{' '.join(pills)}</div>",
         kicker="Employee profile", avatar=initials(emp["name"]))

    c1, c2, c3 = st.columns([1.8, 0.9, 1])
    with c1:
        st.plotly_chart(trajectory_chart(data, eid, as_of, r["box"]), key="traj")
        st.caption("Dotted path = algorithmic placement at each quarter end. Press ▶ to replay how the placement moved.")
    with c2:
        st.metric(f"Performance · {pl['perf_band']}", f"{pl['perf']:.0f}/100")
        st.metric(f"Potential · {pl['pot_band']}", f"{pl['pot']:.0f}/100")
        st.metric(f"{rk['model']} · {rk['level']}", f"{rk['score']:.0f}/100")
        if r["prev_box"]:
            st.caption(f"Last quarter ({engine.quarter_label(r['prev_q'])}): {r['prev_box']}")
    with c3:
        validation_panel(eid)
        pdf = report.talent_card(data, eid, as_of, r, engine.ai_summary(data, eid, as_of),
                                 engine.career_suggestion(data, eid, as_of, r["box"]))
        st.download_button("Export talent card (PDF)", pdf, file_name=f"talent-card-{emp['name'].replace(' ', '-')}.pdf",
                           mime="application/pdf", icon=":material/picture_as_pdf:", width="stretch",
                           on_click="ignore", key=f"pdf_{eid}")

    tabs = [":material/calculate: Score breakdown", ":material/auto_awesome: AI summary",
            ":material/forum: Reviews & check-ins", ":material/monitoring: Engagement",
            ":material/route: Career path", ":material/psychology: Surveys & personality"]
    ob = data["checkins"][(data["checkins"]["emp_id"] == eid) & data["checkins"]["kind"].str.startswith("Onboarding")]
    if not ob.empty:
        tabs.append(":material/flag: Onboarding")
    t = st.tabs(tabs)

    with t[0]:
        st.markdown("#### Performance axis")
        if pl["provisional"]:
            st.caption(f"No annual review yet → onboarding formula, then pulled halfway to neutral (50) for low "
                       f"confidence: raw {pl['perf_raw']:.1f} → {pl['perf']:.1f}.")
        contributions_table(pl["perf_components"], pl["perf_raw"], "Performance")
        st.markdown("#### Potential axis")
        contributions_table(pl["pot_components"], pl["pot"], "Potential")
        st.caption(f"Bands: Low < {engine.BAND_LOW:.0f} ≤ Moderate < {engine.BAND_HIGH:.0f} ≤ High.")
        st.markdown(f"#### {rk['model']}")
        contributions_table(rk["components"], rk["score"], rk["model"], risk=True)

    with t[1]:
        summ = engine.ai_summary(data, eid, as_of)
        st.markdown("<div class='lu-kicker'>AI-generated summary · simulated LLM step · for manager review</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='lu-summary'>{summ['text'].replace('**', '')}</div>", unsafe_allow_html=True)
        st.write("")
        st.caption(f"Pipeline: {summ['n_notes']} most recent manager notes → sentence-level theme extraction → "
                   "summary → structured signals (tone feeds Performance; leadership/learning/ambition feed "
                   "Potential; motivation/workload feed the risk model). Raw text is never scored directly.")
        if summ["themes"]:
            html_table(pd.DataFrame([(x["theme"], x["feeds"], x["positive"], x["negative"], x["direction"])
                                     for x in summ["themes"]],
                                    columns=["Theme", "Feeds into", "+ mentions", "− mentions", "Net"]), bar_cols=())
            with st.expander("Evidence — the sentences behind each theme"):
                for x in summ["themes"]:
                    st.markdown(f"**{x['theme']}**")
                    for dt, pol, ev in x["evidence"]:
                        st.markdown(f"<div class='lu-evidence'>{'▲' if pol > 0 else '▼'} {dt:%d %b %Y} — "
                                    f"“{html.escape(ev)}”</div>", unsafe_allow_html=True)
        is_mgr = manager_id is not None and emp["manager_id"] == manager_id
        st.markdown("#### Add a check-in note")
        if not is_mgr:
            st.caption("Switch to the Manager view (as this employee's manager) to add notes.")
        else:
            st.caption(f"Saved as an ad-hoc check-in dated {as_of:%d %b %Y}. The AI summary and the scores update "
                       "immediately; the 9-box placement then needs re-validation.")
            with st.form(f"note_{eid}", clear_on_submit=True):
                txt = st.text_area("Manager note", height=110, placeholder=(
                    f"e.g. {first(emp['name'])} led the client workshop and mentored two analysts. "
                    "Workload has been heavy — long hours on the due diligence."))
                if st.form_submit_button("Save note & re-run analysis", type="primary") and txt.strip():
                    st.session_state["before"] = (eid, pl["perf"], pl["pot"], pl["box"], rk["score"])
                    engine.add_checkin(eid, as_of, actor, txt.strip())
                    st.rerun()
            before = st.session_state.get("before")
            if before and before[0] == eid:
                _, bp, bpo, bb, br = before
                st.success(f"Re-scored. Performance {bp:.0f} → {pl['perf']:.0f} · Potential {bpo:.0f} → "
                           f"{pl['pot']:.0f} · Box {bb} → {pl['box']} · {rk['model']} {br:.0f} → {rk['score']:.0f}")

    with t[2]:
        rv = data["reviews"][(data["reviews"]["emp_id"] == eid) & (data["reviews"]["review_date"] <= as_of)]
        st.markdown("#### Annual reviews")
        if rv.empty:
            st.info("No annual review yet (first review falls on the 12-month anniversary).")
        else:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=rv["review_date"].astype(str), y=rv["rating"], marker_color=EMERALD,
                                 text=rv["rating"], textposition="outside", name="Rating",
                                 hovertemplate="%{x}: %{y}/5<extra></extra>"))
            fig = fig_base(fig, 230, legend=False)
            fig.update_yaxes(range=[0, 5.6], title="Review rating (1-5)")
            st.plotly_chart(fig, key="rev")
            html_table(pd.DataFrame([(f"{x['review_date']:%d %b %Y}", x["title_at_review"], f"{x['rating']}/5",
                                      f"{x['objectives_pct']:.0f}%", f"{x['potential_rating']}/5", x["notes"])
                                     for _, x in rv.iloc[::-1].iterrows()],
                                    columns=["Date", "Title", "Rating", "Objectives", "Potential", "Manager notes"]),
                       bar_cols=())
        st.markdown("#### Check-ins")
        ck = data["checkins"][(data["checkins"]["emp_id"] == eid) & (data["checkins"]["checkin_date"] <= as_of)]
        for _, row in ck.iloc[::-1].iterrows():
            tags = " ".join(pill(("▲ " if h["polarity"] > 0 else "▼ ") + h["label"],
                                 "rgba(47,181,122,0.14)" if h["polarity"] > 0 else "rgba(228,106,106,0.14)",
                                 "#7fe3b4" if h["polarity"] > 0 else "#ff9b93") for h in row["hits"])
            extra = ""
            if pd.notna(row["ramp_up"]):
                extra = f" · ramp-up {row['ramp_up']}/5 · expectation gap {row['expectation_gap']}/10"
            with card():
                st.markdown(f"**{row['kind']}** · {row['checkin_date']:%d %b %Y} · {row['author']}{extra}")
                st.write(row["notes"])
                st.markdown(tags or "<span style='color:#999'>no themes detected</span>", unsafe_allow_html=True)

    with t[3]:
        s = engine.engagement_series(data, eid, as_of)
        if s.empty:
            st.info("No pulse survey answered yet.")
        else:
            a, b2 = st.columns(2)
            a.plotly_chart(engagement_chart(s, f"Engagement index — trend: {rk['trend'].lower()} "
                                               f"({rk['slope']:+.1f}/month)"), key="pe1")
            b2.plotly_chart(pulse_detail_chart(s), key="pe2")
            if rk["model"] == "Onboarding risk":
                st.caption("For new hires the trend is too short to read; the onboarding risk model leans on the "
                           "expectation gap and ramp-up instead.")

    with t[4]:
        sug = engine.career_suggestion(data, eid, as_of, r["box"])
        st.markdown(f"### Suggested trajectory: {sug['kind']}")
        st.markdown(sug["rationale"])
        if r["box"] != pl["box"]:
            st.caption(f"Uses the manager-validated box ({r['box']}) rather than the algorithm's ({pl['box']}).")
        for a in sug["actions"]:
            st.markdown(f"- {a}")
        d = engine.latest_decision(ctx["dec"], "Career path", eid, period)
        is_mgr = manager_id is not None and emp["manager_id"] == manager_id
        if d is not None:
            st.success(f"{d['status'].capitalize()} by {d['actor']} — {d['final_value']}"
                       + (f" · “{d['reason']}”" if d["reason"] else ""))
        if is_mgr:
            with st.form(f"cp_{eid}"):
                choice = st.radio("Decision", ["Approve", "Modify", "Reject"], horizontal=True)
                note = st.text_input("Comment / modified plan (required for Modify or Reject)")
                if st.form_submit_button("Record decision", type="primary"):
                    if choice != "Approve" and not note.strip():
                        st.error("Please add a comment.")
                    else:
                        status = {"Approve": "approved", "Modify": "modified", "Reject": "rejected"}[choice]
                        final = sug["kind"] if choice == "Approve" else (note.strip() if choice == "Modify" else "—")
                        engine.log_decision(actor, "Manager", "Career path", eid, None, period, sug["kind"], final,
                                            status, note.strip() or None)
                        st.rerun()
        elif d is None:
            st.caption("Awaiting the manager's decision. Nothing is communicated to the employee until approved.")

    with t[5]:
        pers = data["personality"][data["personality"]["emp_id"] == eid]
        sv = data["survey"][(data["survey"]["emp_id"] == eid) & (data["survey"]["survey_date"] <= as_of)]
        a, b2 = st.columns(2)
        with a:
            st.markdown("#### Big Five personality profile")
            if pers.empty or pers.iloc[0]["taken_date"] > as_of:
                st.info("Not taken yet at this date.")
            else:
                pr = pers.iloc[0]
                traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
                vals = [pr[x] for x in traits]
                fig = go.Figure(go.Scatterpolar(r=vals + vals[:1], theta=[x.capitalize() for x in traits + traits[:1]],
                                                fill="toself", line=dict(color=EMERALD_BRIGHT, width=2),
                                                fillcolor="rgba(95,214,160,0.18)",
                                                hovertemplate="%{theta}: %{r}<extra></extra>"))
                fig = fig_base(fig, 300, legend=False)
                fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], gridcolor="rgba(199,208,203,0.12)", linecolor="rgba(0,0,0,0)"), angularaxis=dict(gridcolor="rgba(199,208,203,0.12)"), bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig, key="big5")
                st.caption(f"Self-assessment, taken {pr['taken_date']:%d %b %Y}. Only *openness* is used in scoring "
                           "(learning agility, 10% of potential).")
        with b2:
            st.markdown("#### Annual engagement & career survey")
            if sv.empty:
                st.info("Not answered yet (survey ran in Feb 2026; new hires join next cycle).")
            else:
                x = sv.iloc[-1]
                m1, m2, m3 = st.columns(3)
                m1.metric("Satisfaction", f"{x['satisfaction']}/5")
                m2.metric("Growth opportunities", f"{x['growth_opportunities']}/5")
                m3.metric("eNPS answer", f"{x['enps']}/10")
                m1.metric("Intent to stay (2y)", f"{x['intent_to_stay']}/5")
                m2.metric("Open to mobility", "Yes" if x["open_to_mobility"] else "No")
                st.markdown(f"**Career aspiration:** {x['aspiration']}")

    if not ob.empty:
        with t[6]:
            st.markdown("#### First 90 days — 30/60/90 check-ins")
            cols = st.columns(3)
            for i, k in enumerate((30, 60, 90)):
                sched = emp["start_date"] + pd.Timedelta(days=k)
                done = ob[(ob["kind"] == f"Onboarding {k}-day") & (ob["checkin_date"] <= as_of)]
                with cols[i]:
                    with card():
                        st.markdown(f"**{k}-day check-in** · due {sched:%d %b}")
                        if not done.empty:
                            row = done.iloc[0]
                            late = (row["checkin_date"] - sched).days
                            st.markdown(f"Held {row['checkin_date']:%d %b}" + (f" — **{late} days late**" if late > 5 else " ✓"))
                            st.metric("Ramp-up speed", f"{row['ramp_up']}/5")
                            st.metric("Expectation-vs-reality gap", f"{row['expectation_gap']}/10",
                                      help="0 = role is exactly as described; 10 = completely different")
                        elif sched > as_of:
                            st.caption("Upcoming")
                        else:
                            st.warning("Not held yet")
            if rk["model"] == "Onboarding risk":
                st.caption("While in the first 90 days, risk is read through the onboarding model (gap and ramp-up "
                           "weigh 65%) rather than the pulse trend, which is too short to be meaningful.")
            else:
                st.caption("Onboarding completed — risk is now read through the standard flight-risk model.")


def page_team():
    hero(f"My team", f"{data['names'][manager_id]} · {data['emp_by_id'][manager_id]['title']}, "
         f"{html.escape(data['emp_by_id'][manager_id]['practice'])} · data as of <b>{as_of:%d %b %Y}</b>",
         kicker="Manager workspace", avatar=initials(data["names"][manager_id]))
    hitl_banner("Review each proposed placement: confirm it, or adjust it with a reason. Your decisions feed HR "
                "calibration and succession planning.")
    ids = team_ids
    if not ids:
        st.info("No direct reports at this date.")
        return
    pend = [e for e in ids if ctx["rows"][e]["status"] == "pending"]
    flags = [e for e in ids if ctx["rows"][e]["rk"]["level"] != "Low"]
    p = data["pulses"][(data["pulses"]["emp_id"].isin(ids)) & (data["pulses"]["pulse_date"] <= as_of)]
    c = st.columns(4)
    c[0].metric("Direct reports", len(ids))
    c[1].metric("To validate", len(pend))
    c[2].metric("Risk flags", len(flags), help="Medium or High risk — monthly trend below",
                chart_data=monthly_series(lambda w: count_risk(lambda x: active_ids(x, ids), "Flight risk",
                                                               ("High", "Medium"), w)
                                          + count_risk(lambda x: active_ids(x, ids), "Onboarding risk",
                                                       ("High", "Medium"), w)), chart_type="bar")
    last_m = p[p["pulse_date"] == p["pulse_date"].max()]["engagement_index"].mean() if not p.empty else None
    tp = p.copy()
    tp["m"] = pd.to_datetime(tp["pulse_date"]).dt.to_period("M")
    team_monthly = tp.groupby("m")["engagement_index"].mean()
    c[3].metric("Engagement", f"{last_m:.0f}" if last_m is not None else "—", help="Team average, latest pulse (0-100)",
                chart_data=[round(v, 1) for v in team_monthly.values] or None, chart_type="area")

    section("Team 9-box")
    render_grid(ctx, ids)
    st.write("")
    right, flags_col = st.columns(2, gap="large")
    with right:
        section("Validation queue")
        if not pend:
            st.success("All placements validated for this period.")
        for e in pend:
            r = ctx["rows"][e]
            with card():
                mv = f" (was {r['prev_box']})" if r["prev_box"] and r["prev_box"] != r["pl"]["box"] else ""
                st.markdown(f"**{r['emp']['name']}** → proposed **{r['pl']['box']}**{mv}  \n"
                            f"<span style='font-size:0.85rem;color:{INK2}'>Perf {r['pl']['perf']:.0f} · Pot "
                            f"{r['pl']['pot']:.0f}{' · provisional' if r['pl']['provisional'] else ''}</span>",
                            unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("Confirm", key=f"q_conf_{e}", type="primary", width="stretch", icon=":material/check:"):
                    engine.log_decision(actor, "Manager", "9-box", e, None, period, r["pl"]["box"], r["pl"]["box"],
                                        "confirmed", "Agree with proposed placement.")
                    st.rerun()
                if b2.button("Review / adjust", key=f"q_adj_{e}", width="stretch"):
                    open_profile(e)
                    st.rerun()
    with flags_col:
        section("Team risk flags")
        risk_flag_list(ids, "team")
    section("Team engagement trend")
    st.plotly_chart(org_engagement_chart(data, as_of, ids), key="team_eng")


def box_value(box):
    (pb, fb), _ = engine.BOX_BY_NAME[box]
    return pb + fb


def short_actor(name):
    name = str(name)
    return "Practice partners (outside pilot)" if "outside pilot" in name or "Partner" in name and \
        name not in data["names"].values() else name


def calibration_view():
    dec = engine.decisions()
    nine = dec[dec["kind"] == "9-box"].copy()
    if nine.empty:
        st.info("No 9-box decisions logged yet.")
        return
    rounds = sorted(nine["period"].unique(), reverse=True)
    full = [r for r in rounds if (nine["period"] == r).sum() >= 3]
    sel = st.pills("Calibration round", rounds, default=full[0] if full else rounds[0],
                   format_func=lambda p: f"{engine.quarter_label(p)} ({engine.period_label(p)})", key="cal_round")
    sel = sel or rounds[0]
    d = nine[nine["period"] == sel].sort_values("ts").groupby("emp_id").tail(1).copy()
    d["delta"] = d.apply(lambda r: box_value(r["final_value"]) - box_value(r["algo_value"]), axis=1)
    d["manager"] = d["actor"].map(short_actor)
    pe = engine.period_end(sel)
    top = {"Star", "High Potential", "High Performer"}

    over = d[d["status"] == "overridden"]
    c = st.columns(4)
    c[0].metric("Placements reviewed", len(d))
    c[1].metric("Overrides", len(over), f"{len(over) / max(1, len(d)) * 100:.0f}% of placements", delta_color="off")
    c[2].metric("Upgrades", int((d["delta"] > 0).sum()), help="Manager placed the person in a stronger box")
    c[3].metric("Downgrades", int((d["delta"] < 0).sum()), help="Manager placed the person in a weaker box")

    rows, chart = [], []
    for mgr, g in d.groupby("manager"):
        n, o = len(g), int((g["status"] == "overridden").sum())
        up, down = int((g["delta"] > 0).sum()), int((g["delta"] < 0).sum())
        top_share = (g["final_value"].isin(top)).mean() * 100
        perf = [engine.placement(data, e, pe)["perf"] for e in g["emp_id"]]
        rate = o / n * 100
        if up >= 2 and down == 0:
            flag = pill("Leniency pattern — discuss", "rgba(212,178,95,0.14)", "#e8cb84")
        elif down >= 1 and up == 0:
            flag = pill("Stricter than model", "rgba(74,163,223,0.14)", "#9fd0f2")
        elif rate >= 34:
            flag = pill("High override rate", "rgba(212,178,95,0.14)", "#e8cb84")
        else:
            flag = pill("Aligned with model", "rgba(47,181,122,0.14)", "#7fe3b4")
        rows.append(f'<tr><td class="name">{html.escape(mgr)}</td><td class="num">{n}</td>'
                    f'<td class="num" style="text-align:left"><span class="lu-bar"><span style="width:{rate:.0f}%">'
                    f'</span></span>{rate:.0f}%</td><td class="num">↑ {up} &nbsp; ↓ {down}</td>'
                    f'<td class="num">{top_share:.0f}%</td><td class="num">{sum(perf) / len(perf):.0f}</td>'
                    f'<td>{flag}</td></tr>')
        chart.append((mgr, up, down))
    st.write("")
    a, b = st.columns([1.5, 1], gap="large")
    with a:
        section("Manager consistency")
        st.markdown('<table class="lu-table"><thead><tr><th>Manager</th><th>Placements</th><th>Override rate</th>'
                    '<th>Direction</th><th>In top 3 boxes</th><th>Avg perf.</th><th>Calibration signal</th></tr>'
                    f'</thead><tbody>{"".join(rows)}</tbody></table>', unsafe_allow_html=True)
        st.caption("Direction compares the manager's box with the algorithm's (↑ stronger, ↓ weaker). A manager who "
                   "only ever upgrades may be lenient; one who only downgrades may be stricter than peers. These are "
                   "conversation starters for the calibration session, not judgements.")
    with b:
        section("Upgrades vs downgrades")
        chart = [x for x in chart if x[1] or x[2]] or chart
        fig = go.Figure()
        fig.add_trace(go.Bar(y=[x[0] for x in chart], x=[x[1] for x in chart], orientation="h", name="Upgrades",
                             marker_color=EMERALD_BRIGHT, hovertemplate="%{y}: %{x} upgrade(s)<extra></extra>"))
        fig.add_trace(go.Bar(y=[x[0] for x in chart], x=[-x[2] for x in chart], orientation="h", name="Downgrades",
                             marker_color=RED, customdata=[x[2] for x in chart],
                             hovertemplate="%{y}: %{customdata} downgrade(s)<extra></extra>"))
        fig = fig_base(fig, 60 + 46 * len(chart))
        fig.update_layout(barmode="relative")
        fig.update_xaxes(zeroline=True, zerolinecolor="rgba(199,208,203,0.4)", dtick=1, tickformat="d")
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, key="cal_chart")

    section("Overrides to discuss")
    if over.empty:
        st.success("No overrides in this round — every placement was confirmed as proposed.")
    else:
        html_table(pd.DataFrame([(data["names"].get(r["emp_id"], "—"), r["manager"], r["algo_value"],
                                  ("↑ " if r["delta"] > 0 else "↓ " if r["delta"] < 0 else "") + r["final_value"],
                                  r["reason"] or "—") for _, r in over.iterrows()],
                                columns=["Employee", "Manager", "Algorithm", "Manager decision", "Reason"]),
                   bar_cols=())


def fairness_table(by_col, label):
    rows = []
    org_top = None
    recs = []
    for e, r in ctx["rows"].items():
        key = r["emp"]["practice"] if by_col == "practice" else engine.tenure_band(r["emp"], as_of)
        recs.append((key, r["box"] in ("Star", "High Potential", "High Performer"), r["pl"]["pot"], r["pl"]["perf"]))
    df = pd.DataFrame(recs, columns=["group", "top", "pot", "perf"])
    org_top = df["top"].mean() * 100
    for g, x in df.groupby("group"):
        share = x["top"].mean() * 100
        gap = share - org_top
        flag = "Check" if abs(gap) >= 25 and len(x) >= 3 else "OK"
        rows.append((g, len(x), f"{share:.0f}%", f"{gap:+.0f} pts", f"{x['perf'].mean():.0f}", f"{x['pot'].mean():.0f}",
                     flag))
    html_table(pd.DataFrame(rows, columns=[label, "People", "In top 3 boxes", "vs cohort", "Avg perf.", "Avg pot.",
                                           "Signal"]), bar_cols=())
    return org_top


def ethics_view():
    st.markdown('<div class="lu-feat">'
                '<div><i>PRINCIPLE 1</i><b>Humans decide</b><span>No placement, flag or ranking takes effect '
                'without a named manager or HR decision. Every decision is logged next to the proposal.</span></div>'
                '<div><i>PRINCIPLE 2</i><b>Explainable</b><span>Every score is a weighted sum with visible sources; '
                'every AI theme links to the sentence that triggered it.</span></div>'
                '<div><i>PRINCIPLE 3</i><b>Contestable</b><span>Managers can override with a reason; employees '
                'can ask for their data and challenge a placement.</span></div>'
                '<div><i>PRINCIPLE 4</i><b>Proportionate</b><span>Short surveys, free-text comments never scored, '
                'personality weighted at only 10% of potential.</span></div>'
                '<div><i>PRINCIPLE 5</i><b>Consent-based</b><span>The personality test is optional and consent can '
                'be withdrawn at any time, deleting the results.</span></div>'
                '<div><i>PRINCIPLE 6</i><b>Monitored for bias</b><span>Placements are compared across practices and '
                'tenure bands every calibration round (see below).</span></div></div>', unsafe_allow_html=True)

    section("Who can see what")
    Y, N, T = "✓", "—", "Own team"
    html_table(pd.DataFrame([
        ("Monthly pulse answers", "✓", T, "Own answers", "✓ (index)"),
        ("Pulse free-text comment", N, T, "Own answers", "Not used"),
        ("Manager check-in notes", "✓", T, "On request", "✓ (AI themes)"),
        ("Annual review", "✓", T, "✓", "✓"),
        ("Annual survey answers", "✓", T, "Own answers", "✓ (mobility, intent to stay)"),
        ("Personality results", "✓", T, "✓", "Openness only"),
        ("9-box placement & scores", "✓", T, "On request", "Produces it"),
        ("Flight / onboarding risk flag", "✓", T, N, "Produces it"),
        ("Succession shortlist", "✓", N, N, "Proposes ranking"),
    ], columns=["Data", "HR", "Manager", "Employee", "Used by algorithm"]), bar_cols=())
    st.caption("Proposed access model for roll-out. The employee self-service view is on the roadmap; in this "
               "prototype employees can request their data from HR.")

    section("Regulatory checklist")
    html_table(pd.DataFrame([
        ("No decision based solely on automated processing", "GDPR Art. 22",
         "Human validation is mandatory for every placement, flag, ranking and career path; all logged."),
        ("Information & right of access", "GDPR Art. 13-15",
         "Plain-language notice at each survey; score breakdown with sources can be shared on request."),
        ("Lawful basis & consent", "GDPR Art. 6-7",
         "Legitimate interest for performance data; explicit, withdrawable consent for the personality test."),
        ("Data minimisation & retention", "GDPR Art. 5",
         "Only scored fields are kept; e.g. pulses 24 months, personality deleted on withdrawal or exit."),
        ("Impact assessment before roll-out", "GDPR Art. 35 (DPIA)",
         "Required: systematic evaluation of employees using new technology."),
        ("High-risk AI system (employment)", "EU AI Act, Annex III",
         "Human oversight, logging, risk management, bias testing, documentation, informing employees."),
        ("Employee representatives", "Labour law (e.g. CSE in France)",
         "Inform and consult staff representatives before introducing the tool."),
    ], columns=["Requirement", "Source", "How Level UP addresses it"]), bar_cols=())
    st.caption("Framing for discussion in a business-school prototype — not legal advice.")

    section("Bias monitoring — live check")
    a, b = st.columns(2, gap="large")
    with a:
        org_top = fairness_table("practice", "Practice")
    with b:
        fairness_table("tenure", "Tenure band")
    st.caption(f"Share of people in the top 3 boxes (Star, High Potential, High Performer) by group, against the "
               f"cohort average ({org_top:.0f}%). A gap of 25+ points in a group of 3+ people is marked “Check” for "
               "the calibration session. In production this would also cover gender, age and other protected "
               "characteristics, with appropriate safeguards.")


def page_log():
    hero("Decisions", "Every human decision next to what the algorithm proposed — and how consistent managers are.")
    if manager_id is None:
        t_audit, t_cal = st.tabs([":material/history_edu: Audit trail", ":material/balance: Calibration"])
        with t_cal:
            calibration_view()
        with t_audit:
            audit_trail()
    else:
        audit_trail()


def audit_trail():
    dec = engine.decisions()
    if manager_id:
        dec = dec[dec["emp_id"].isin(team_ids) | (dec["actor"] == actor)]
    dec = dec.copy()
    vac_titles = dict(zip(data["vacancies"]["id"], data["vacancies"]["title"]))
    kinds = st.pills("Decision type", sorted(dec["kind"].unique()), selection_mode="multi",
                     default=sorted(dec["kind"].unique())) or []
    dec = dec[dec["kind"].isin(kinds)]
    c = st.columns(3)
    nine = dec[dec["kind"] == "9-box"]
    c[0].metric("Decisions logged", len(dec))
    c[1].metric("9-box confirmations", int((nine["status"] == "confirmed").sum()))
    c[2].metric("9-box overrides", int((nine["status"] == "overridden").sum()),
                help="Overrides are a healthy signal: the model is a proposal, not a verdict.")
    status_style = {"confirmed": ("ok", "Confirmed"), "overridden": ("adj", "Overridden"), "approved": ("ok", "Approved"),
                    "modified": ("adj", "Modified"), "rejected": ("risk", "Rejected"),
                    "shortlisted": ("ok", "Shortlisted"), "dismissed": ("risk", "Not pursued"),
                    "reopened": ("pend", "Re-opened"), "acknowledged": ("ok", "Acknowledged"), "closed": ("ok", "Closed")}
    rows = []
    for _, d in dec.head(200).iterrows():
        ts = pd.to_datetime(d["ts"])
        who = html.escape(str(d["actor"]))
        subject = html.escape(data["names"].get(d["emp_id"], "—") if d["emp_id"] else "—")
        if d["vacancy_id"]:
            subject += f'<div class="sub">{html.escape(vac_titles.get(d["vacancy_id"], ""))}</div>'
        changed = d["algo_value"] != d["final_value"] and d["kind"] in ("9-box", "Career path")
        k, label = status_style.get(d["status"], ("pend", str(d["status"]).capitalize()))
        reason = html.escape(d["reason"]) if d["reason"] else '<span style="color:var(--lu-muted)">—</span>'
        rows.append(
            f'<tr><td class="num" style="text-align:left">{ts:%d %b %Y}<div class="sub">{ts:%H:%M} · '
            f'{html.escape(str(d["period"] or ""))}</div></td>'
            f'<td class="name">{who}</td><td>{silver_pill(d["kind"])}</td><td class="name">{subject}</td>'
            f'<td class="src">{html.escape(str(d["algo_value"] or "—"))}</td>'
            f'<td class="{"name" if changed else "src"}">{"→ " if changed else ""}'
            f'{html.escape(str(d["final_value"] or "—"))}</td>'
            f'<td class="stt">{mk(k)}&nbsp;{label}</td><td class="src reason">{reason}</td></tr>')
    if not rows:
        st.info("No decisions logged for this selection yet.")
        return
    cols = "".join(f'<col style="width:{w}%">' for w in (10, 12, 10, 11, 11, 11, 11, 24))
    st.markdown(f'<table class="lu-table lu-log"><colgroup>{cols}</colgroup><thead><tr><th>When</th><th>Who</th><th>Type</th><th>Employee</th>'
                f'<th>Algorithm proposed</th><th>Human decision</th><th>Status</th><th>Reason</th></tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Employee surveys — what employees actually receive
# ---------------------------------------------------------------------------
def scale_html(lo, hi, selected, left, right, mid=None):
    chips = "".join(f'<span class="lu-sc{" on" if v == selected else ""}">{v}</span>' for v in range(lo, hi + 1))
    ends = f'<div class="lu-sc-ends"><span>{left}</span>' + (f'<span>{mid}</span>' if mid else "") + \
           f'<span>{right}</span></div>'
    return f'<div class="lu-sc-row">{chips}</div>{ends}'


def phone(title, subtitle, body, step=None, button="Submit"):
    prog = f'<div class="lu-ph-prog"><span style="width:{step}%"></span></div>' if step else ""
    return (f'<div class="lu-phone"><div class="lu-ph-notch"></div><div class="lu-ph-head">{LOGO}<div>'
            f'<div class="lu-ph-title">{title}</div><div class="lu-ph-sub">{subtitle}</div></div></div>{prog}'
            f'<div class="lu-ph-body">{body}</div><div class="lu-ph-btn">{button}</div>'
            f'<div class="lu-ph-foot">Confidential · used only for Level UP indices</div></div>')


def q(n, text, inner, hint=None):
    return (f'<div class="lu-q"><div class="lu-q-n">Q{n}</div><div class="lu-q-t">{text}</div>'
            + (f'<div class="lu-q-h">{hint}</div>' if hint else "") + inner + '</div>')


def choice_html(options, selected):
    return "".join(f'<div class="lu-opt{" on" if o == selected else ""}"><span></span>{html.escape(o)}</div>'
                   for o in options)


def usage_table(rows):
    html_table(pd.DataFrame(rows, columns=["Question", "Feeds into", "Weight in model"]), bar_cols=())


def page_surveys():
    hero("Employee surveys", "What employees receive, how often, and exactly how each answer feeds the model.")
    hitl_banner("Surveys are short by design and explained to employees up front. The personality test is optional "
                "and consent-based; answers are used only to compute the indices shown in Level UP.")
    active = [e for e in ctx["rows"]]
    p = data["pulses"]
    last_month = p[p["pulse_date"] <= as_of]["pulse_date"].max()
    lm = p[p["pulse_date"] == last_month] if pd.notna(last_month) else p.iloc[0:0]
    st.markdown('<div class="lu-feat" style="grid-template-columns:repeat(4,1fr)">'
                '<div><i>EVERY MONTH</i><b>Pulse survey</b><span>3 questions · about 1 minute · all employees</span></div>'
                '<div><i>DAY 30 · 60 · 90</i><b>Onboarding check-ins</b><span>New hire + manager · replaces the '
                'quarterly check-in</span></div>'
                '<div><i>ONCE A YEAR · FEB</i><b>Engagement & career</b><span>6 questions · about 4 minutes · '
                'all employees</span></div>'
                '<div><i>ONE-TIME · OPTIONAL</i><b>Personality profile</b><span>10 statements · about 3 minutes · '
                'with consent</span></div></div>', unsafe_allow_html=True)

    t = st.tabs([":material/favorite: Monthly pulse", ":material/flag: Onboarding 30-60-90",
                 ":material/assignment: Annual engagement & career survey", ":material/psychology: Personality (Big Five)"])

    with t[0]:
        a, b = st.columns([1, 1.25], gap="large")
        with a:
            body = (q(1, "How engaged and energised do you feel in your work this month?",
                      scale_html(1, 10, 8, "Not at all", "Fully engaged"))
                    + q(2, "How heavy has your workload been this month?",
                        scale_html(1, 10, 6, "Far too light", "Unsustainable", "About right"))
                    + q(3, "Overall, how do you feel about your work and your team right now?",
                        scale_html(1, 10, 7, "Very negative", "Very positive"))
                    + q(4, "Anything you'd like your manager or HR to know? <i>(optional)</i>",
                        '<div class="lu-txt">Busy month on Project Atlas, but the team is great.</div>'))
            st.markdown(phone("Monthly pulse · September", "3 questions · about 1 minute", body, 100), unsafe_allow_html=True)
        with b:
            section("How it is used")
            usage_table([("Q1 Engagement", "Engagement index → trend & flight risk", "50%"),
                         ("Q2 Workload", "Workload balance (6/10 = healthy; above 6 is penalised)", "20%"),
                         ("Q3 Sentiment", "Engagement index → trend & flight risk", "30%"),
                         ("Q4 Comment", "Not scored — read by the manager only", "—")])
            st.caption("Engagement index = 50% engagement + 30% sentiment + 20% workload balance, on a 0-100 scale. "
                       "The trend over the last 6 pulses drives the flight-risk signal.")
            section("Try it live")
            s1, s2, s3 = st.columns(3)
            e_ = s1.slider("Engagement", 1, 10, 8, key="try_e")
            w_ = s2.slider("Workload", 1, 10, 6, key="try_w")
            s_ = s3.slider("Sentiment", 1, 10, 7, key="try_s")
            idx = engine.engagement_index(e_, w_, s_)
            tone = ("#7fe3b4", "Healthy") if idx >= 65 else (("#e8cb84", "Watch") if idx >= 50 else ("#ff9b93", "At risk"))
            st.markdown(f'<div class="lu-try"><div><div class="lu-kicker">Engagement index</div>'
                        f'<div class="lu-try-v">{idx:.0f}<span>/100</span></div></div>'
                        f'<div class="lu-try-bar"><span style="width:{idx:.0f}%;background:{tone[0]}"></span></div>'
                        f'<div style="color:{tone[0]};font-weight:600">{tone[1]}</div></div>', unsafe_allow_html=True)
            if len(lm):
                section(f"Latest wave · {pd.to_datetime(last_month):%B %Y}")
                m = st.columns(4)
                m[0].metric("Replies", f"{len(lm)}", help=f"{len(lm)} responses out of {len(active)} employees")
                m[1].metric("Engaged", f"{lm['engagement'].mean():.1f}", help="Average engagement answer (1-10)")
                m[2].metric("Workload", f"{lm['workload'].mean():.1f}", help="Average workload answer (6 = healthy)")
                m[3].metric("Mood", f"{lm['sentiment'].mean():.1f}", help="Average sentiment answer (1-10)")

    with t[1]:
        a, b = st.columns([1, 1.25], gap="large")
        with a:
            body = ('<div class="lu-ph-role">Answered by the new hire</div>'
                    + q(1, "How different is the job from what was described during recruitment?",
                        scale_html(0, 10, 3, "Exactly as described", "Completely different"))
                    + q(2, "Do you have what you need to do your job (tools, access, buddy)?",
                        choice_html(["Yes, everything", "Mostly", "Not yet"], "Mostly"))
                    + '<div class="lu-ph-role">Answered by the manager</div>'
                    + q(3, "How quickly is the new hire becoming autonomous?",
                        scale_html(1, 5, 4, "Very slowly", "Very quickly"))
                    + q(4, "Check-in notes",
                        '<div class="lu-txt">Settling in well; the buddy programme is working. Picked up the '
                        'valuation toolkit quickly.</div>'))
            st.markdown(phone("Onboarding check-in · Day 60", "Lucas Fontaine · started 6 Jul 2026", body, 66,
                              "Save check-in"), unsafe_allow_html=True)
        with b:
            section("How it is used")
            usage_table([("Q1 Expectation gap", "Onboarding risk", "35%"),
                         ("Q2 Equipment & support", "Shown to manager — not scored", "—"),
                         ("Q3 Ramp-up speed", "Onboarding risk (30%) + provisional performance (60%)", "30% / 60%"),
                         ("Q4 Notes", "AI themes → provisional performance (40%)", "40%"),
                         ("Check-in held on time?", "Onboarding risk (late or missed = higher)", "15%"),
                         ("Early pulse answers", "Onboarding risk", "20%")])
            st.caption("During the first 90 days the quarterly check-in is replaced by these three touchpoints. "
                       "A new hire has too few pulses for a trend, so risk is read through the expectation gap and "
                       "ramp-up instead.")

    with t[2]:
        a, b = st.columns([1, 1.25], gap="large")
        with a:
            body = (q(1, "Overall, how satisfied are you working at Northvale?",
                      scale_html(1, 5, 4, "Very dissatisfied", "Very satisfied"))
                    + q(2, "I see real opportunities to grow my career here.",
                        scale_html(1, 5, 4, "Strongly disagree", "Strongly agree"))
                    + q(3, "How likely are you to recommend Northvale as a place to work?",
                        scale_html(0, 10, 8, "Not at all likely", "Extremely likely"))
                    + q(4, "I see myself still working at Northvale in two years.",
                        scale_html(1, 5, 4, "Strongly disagree", "Strongly agree"))
                    + q(5, "Would you be open to a move to another practice, office or country?",
                        choice_html(["Yes", "No"], "Yes"))
                    + q(6, "Which statement best describes your career aspiration?",
                        choice_html(["Partner / Director track", "Move into management", "Move to another practice",
                                     "Deepen expertise in my current role", "Undecided"], "Move into management")))
            st.markdown(phone("Engagement & career survey 2026", "6 questions · about 4 minutes", body, 100),
                        unsafe_allow_html=True)
        with b:
            section("How it is used")
            usage_table([("Q1 Satisfaction", "Context for HR — reported, not scored", "—"),
                         ("Q2 Growth opportunities", "Context for HR — reported, not scored", "—"),
                         ("Q3 eNPS", "Context for HR — reported, not scored", "—"),
                         ("Q4 Intent to stay", "Flight risk", "20%"),
                         ("Q5 Open to mobility", "Potential → desired mobility", "15% (shared)"),
                         ("Q6 Career aspiration", "Potential → mobility · succession fit", "15% (shared)")])
            sv = data["survey"][data["survey"]["survey_date"] <= as_of]
            if len(sv):
                section("Results · Feb 2026 wave")
                m = st.columns(4)
                m[0].metric("Replies", len(sv))
                m[1].metric("Satisfied", f"{sv['satisfaction'].mean():.1f}", help="Average satisfaction (1-5)")
                promoters = (sv["enps"] >= 9).mean() * 100
                detractors = (sv["enps"] <= 6).mean() * 100
                m[2].metric("eNPS", f"{promoters - detractors:+.0f}")
                m[3].metric("Mobile", f"{sv['open_to_mobility'].mean() * 100:.0f}%", help="Open to mobility")
                asp = sv["aspiration"].value_counts()
                fig = go.Figure(go.Bar(x=asp.values, y=asp.index, orientation="h", marker_color=EMERALD,
                                       text=asp.values, textposition="outside",
                                       hovertemplate="%{y}: %{x}<extra></extra>"))
                fig = fig_base(fig, 230, legend=False)
                fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
                fig.update_xaxes(visible=False)
                fig.update_layout(title=dict(text="Career aspirations", font=dict(size=13, color=INK)))
                st.plotly_chart(fig, key="asp")
            else:
                st.info("The annual survey runs in February 2026 — move the timeline forward to see results.")

    with t[3]:
        a, b = st.columns([1, 1.25], gap="large")
        items = [("I enjoy exploring new ideas and new ways of working.", 5),
                 ("I prefer familiar routines over trying new approaches.", 2),
                 ("I plan my work carefully and follow through on commitments.", 4),
                 ("I sometimes leave tasks unfinished.", 2),
                 ("I get energy from working with lots of people.", 4),
                 ("I tend to stay quiet in group discussions.", 2)]
        with a:
            body = '<div class="lu-q-h" style="margin-bottom:10px">How much do you agree? 1 = strongly disagree · 5 = strongly agree</div>'
            for i, (txt, v) in enumerate(items, 1):
                body += q(i, txt, scale_html(1, 5, v, "", ""))
            body += '<div class="lu-q-h" style="text-align:center">… 4 more items · try it live below ↓</div>'
            st.markdown(phone("Work-style profile", "10 statements · about 3 minutes · optional", body, 60, "Next"),
                        unsafe_allow_html=True)
        with b:
            section("How it is used")
            usage_table([("Openness (2 items)", "Potential → learning agility", "10%"),
                         ("Conscientiousness (2 items)", "Shown on profile — not scored", "—"),
                         ("Extraversion (2 items)", "Shown on profile — not scored", "—"),
                         ("Agreeableness (2 items)", "Shown on profile — not scored", "—"),
                         ("Emotional stability (2 items)", "Shown on profile — not scored", "—")])
            st.caption("Illustrative short Big Five questionnaire written for this demo (two statements per trait, one "
                       "of them reverse-scored), scored 0-100 per trait. Taken once, at onboarding or at the "
                       "Nov 2025 roll-out. Only openness enters the model, deliberately at a low weight; a "
                       "production version would use a validated instrument with explicit consent.")
            pers = data["personality"]
            avg = [pers[x].mean() for x in ["openness", "conscientiousness", "extraversion", "agreeableness",
                                            "neuroticism"]]
            traits = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
            fig = go.Figure(go.Scatterpolar(r=avg + avg[:1], theta=traits + traits[:1], fill="toself",
                                            line=dict(color=EMERALD_BRIGHT, width=2), fillcolor="rgba(95,214,160,0.18)",
                                            hovertemplate="%{theta}: %{r:.0f}<extra></extra>"))
            fig = fig_base(fig, 300, legend=False)
            fig.update_layout(title=dict(text="Cohort average profile", font=dict(size=13, color=INK)),
                              polar=dict(radialaxis=dict(range=[0, 100], gridcolor="rgba(199,208,203,0.12)",
                                                         linecolor="rgba(0,0,0,0)"),
                                         angularaxis=dict(gridcolor="rgba(199,208,203,0.12)"),
                                         bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, key="b5avg")

        section("Try it live — take the test")
        st.caption("Answer the 10 statements (1 = strongly disagree, 5 = strongly agree). Each trait uses two "
                   "statements; the second one is reverse-scored. The profile updates as you move the sliders.")
        b5_items = [("openness", "I enjoy exploring new ideas and new ways of working.", False),
                    ("openness", "I prefer familiar routines over trying new approaches.", True),
                    ("conscientiousness", "I plan my work carefully and follow through on commitments.", False),
                    ("conscientiousness", "I sometimes leave tasks unfinished.", True),
                    ("extraversion", "I get energy from working with lots of people.", False),
                    ("extraversion", "I tend to stay quiet in group discussions.", True),
                    ("agreeableness", "I go out of my way to help colleagues.", False),
                    ("agreeableness", "I can be quick to criticise other people's work.", True),
                    ("neuroticism", "I often worry about how my work will be judged.", False),
                    ("neuroticism", "I stay calm under pressure.", True)]
        defaults = [5, 2, 4, 2, 4, 2, 4, 2, 2, 4]
        left, right = st.columns([1.25, 1], gap="large")
        answers = {}
        with left:
            for i, ((trait, text, rev), dv) in enumerate(zip(b5_items, defaults)):
                v = st.slider(f"{i + 1}. {text}" + ("  ↺" if rev else ""), 1, 5, dv, key=f"b5_{i}")
                answers.setdefault(trait, []).append(6 - v if rev else v)
        names = {"openness": "Openness", "conscientiousness": "Conscientiousness", "extraversion": "Extraversion",
                 "agreeableness": "Agreeableness", "neuroticism": "Neuroticism"}
        scores = {t: (sum(v) - 2) / 8 * 100 for t, v in answers.items()}
        with right:
            r = [scores[t] for t in names]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=avg + avg[:1], theta=traits + traits[:1], name="Cohort average",
                                          line=dict(color="rgba(199,208,203,0.55)", width=1.5, dash="dot"),
                                          hovertemplate="Cohort · %{theta}: %{r:.0f}<extra></extra>"))
            fig.add_trace(go.Scatterpolar(r=r + r[:1], theta=traits + traits[:1], fill="toself", name="Your profile",
                                          line=dict(color=EMERALD_BRIGHT, width=2.5), fillcolor="rgba(95,214,160,0.22)",
                                          hovertemplate="You · %{theta}: %{r:.0f}<extra></extra>"))
            fig = fig_base(fig, 360, legend=True)
            fig.update_layout(margin=dict(l=70, r=70, t=50, b=30), polar=dict(radialaxis=dict(range=[0, 100], gridcolor="rgba(199,208,203,0.12)",
                                                         linecolor="rgba(0,0,0,0)"),
                                         angularaxis=dict(gridcolor="rgba(199,208,203,0.12)"),
                                         bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, key="b5try")
            html_table(pd.DataFrame([(names[t], f"{scores[t]:.0f}/100") for t in names],
                                    columns=["Trait", "Your score"]), bar_cols=())
            contrib = engine.POT_WEIGHTS["Learning agility (Big Five openness)"] * scores["openness"]
            st.markdown(f'<div class="lu-try"><div style="flex:0 0 auto"><div class="lu-kicker" style="white-space:nowrap">Used in the model</div>'
                        f'<div class="lu-try-v">+{contrib:.1f}<span> pts</span></div></div>'
                        f'<div style="color:var(--lu-ink-2);font-size:0.85rem">Only <b>openness</b> counts: it is the '
                        f'“learning agility” input, worth 10% of the potential score '
                        f'(10% × {scores["openness"]:.0f}). The other traits are shown on the profile for context '
                        f'only.</div></div>', unsafe_allow_html=True)


def page_method():
    hero("Method & ethics", "How every score is built — and how Level UP stays fair, explainable and compliant.")
    hitl_banner()
    t_model, t_eth = st.tabs([":material/functions: Scoring model", ":material/verified_user: Ethics & GDPR"])
    with t_eth:
        ethics_view()
    with t_model:
        scoring_model()


def scoring_model():
    a, b = st.columns(2)
    with a:
        st.markdown("#### Performance axis")
        html_table(pd.DataFrame({"Component": list(engine.PERF_WEIGHTS), "Weight": [f"{w:.0%}" for w in engine.PERF_WEIGHTS.values()]}))
        st.caption("New hires without an annual review: ramp-up speed 60% + check-in sentiment 40%, then pulled "
                   f"{engine.PROVISIONAL_SHRINK:.0%} towards neutral (50) and marked provisional.")
        st.markdown("#### Potential axis")
        html_table(pd.DataFrame({"Component": list(engine.POT_WEIGHTS), "Weight": [f"{w:.0%}" for w in engine.POT_WEIGHTS.values()]}))
        st.caption(f"Bands: Low < {engine.BAND_LOW:.0f} ≤ Moderate < {engine.BAND_HIGH:.0f} ≤ High, on both axes.")
    with b:
        st.markdown("#### Flight risk (established staff)")
        html_table(pd.DataFrame({"Signal": list(engine.FLIGHT_WEIGHTS), "Weight": [f"{w:.0%}" for w in engine.FLIGHT_WEIGHTS.values()]}))
        st.caption(f"High ≥ {engine.RISK_HIGH:.0f}, Medium ≥ {engine.RISK_MED:.0f}.")
        st.markdown("#### Onboarding risk (first 90 days)")
        html_table(pd.DataFrame({"Signal": list(engine.ONBOARD_WEIGHTS), "Weight": [f"{w:.0%}" for w in engine.ONBOARD_WEIGHTS.values()]}))
        st.caption(f"High ≥ {engine.ONBOARD_HIGH:.0f}, Medium ≥ {engine.ONBOARD_MED:.0f}. Different model because a "
                   "new hire has too few pulses for a trend, and early disengagement shows up as an expectation gap.")
        st.markdown("#### Succession match")
        html_table(pd.DataFrame({"Factor": list(engine.SUCCESSION_WEIGHTS), "Weight": [f"{w:.0%}" for w in engine.SUCCESSION_WEIGHTS.values()]}))
    st.markdown("#### Career path rules (by 9-box cell)")
    html_table(pd.DataFrame([{"9-box cell": k, "Suggested trajectory": v[0], "Example actions": "; ".join(v[1])}
                           for k, v in engine.CAREER_PATHS.items()]))
    st.markdown("#### Data cadence (simulated 12 months, Oct 2025 → Sep 2026)")
    html_table(pd.DataFrame([
        ("Pulse survey", "Monthly", "Engagement, workload, sentiment (1-10)", "Engagement index & trend, risk"),
        ("Manager check-in", "Quarterly (Dec, Mar, Jun, Sep)", "Free-text notes → AI themes", "Performance (tone), potential (signals), risk"),
        ("Onboarding check-in", "Day 30 / 60 / 90 (replaces quarterly)", "Notes, ramp-up 1-5, expectation gap 0-10", "Provisional performance, onboarding risk"),
        ("Annual review", "On each start anniversary", "Rating 1-5, objectives %, potential 1-5", "Performance, potential"),
        ("Annual survey", "Once (Feb 2026)", "Satisfaction, growth, eNPS, intent to stay, aspiration", "Mobility, flight risk"),
        ("Personality test", "Once (Big Five)", "O-C-E-A-N, 0-100", "Learning agility (openness)"),
    ], columns=["Source", "Cadence", "Content", "Feeds"]))
    st.markdown("#### About the AI summary")
    st.write("In production, manager notes would be summarised by a large language model with a fixed output schema "
             "(themes, polarity, evidence quotes). In this demo the same step is simulated with a transparent "
             "theme lexicon so results are reproducible. Only the extracted signals — never the raw text — enter the "
             "scores, and every theme links back to the sentence that triggered it.")
    st.markdown("#### Human-in-the-loop principles")
    st.markdown("- The algorithm **proposes**; managers and HR **decide**. Nothing is auto-executed.\n"
                "- Every 9-box placement needs manager validation; overrides require a written reason.\n"
                "- If new data changes a validated placement, it goes back to *pending*.\n"
                "- Risk flags are prompts for a conversation, never triggers for an action.\n"
                "- Every decision is logged next to the algorithm's proposal (Decision log).")


PAGES = {"Overview": page_overview, "Org 9-box": page_grid, "Succession": page_succession,
         "Engagement": page_engagement, "Employee profile": page_profile, "Decision log": page_log,
         "Methodology": page_method, "My team": page_team, "Employee surveys": page_surveys}
PAGES[page]()
