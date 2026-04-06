import json
import os
from typing import Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import OpenAI
from rag_health_insights import get_rag_health_insights, format_rag_response

# -----------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# -----------------------------------------------------------------------------

load_dotenv()
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

def configure_page() -> None:
    st.set_page_config(
        page_title="Gotham: NYC Air-Pulse",
        page_icon="🏙️",
        layout="wide",
    )

    st.markdown(
        """
        <style>
            /* ── Base ── */
            .stApp { background: radial-gradient(135deg, #1a1f35 0%, #050609 60%); }
            h1, h2, h3, h4, h5, h6, p, li, span, div, label { color: #e0e0e0 !important; }

            /* ── Sidebar ── */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0b0f1a 0%, #0f1520 100%);
                border-right: 1px solid rgba(100, 120, 200, 0.15);
            }
            section[data-testid="stSidebar"] .stRadio label { font-size: 0.9rem; }

            /* ── Metric cards ── */
            .metric-card {
                padding: 1.2rem 1.4rem; border-radius: 12px;
                background: rgba(25, 30, 50, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                margin-bottom: 0.8rem;
                transition: border-color 0.2s;
            }
            .metric-card:hover { border-color: rgba(120, 140, 255, 0.3); }
            .metric-label {
                font-size: 0.75rem; text-transform: uppercase;
                letter-spacing: 0.12em; color: #7a82a8 !important; margin-bottom: 0.4rem;
            }
            .metric-value { font-size: 1.9rem; font-weight: 700; color: #ffffff !important; line-height: 1.1; }
            .metric-sub  { font-size: 0.78rem; color: #5a6080 !important; margin-top: 0.3rem; }

            /* ── Advice boxes ── */
            .advice-box {
                padding: 1.4rem 1.6rem; border-radius: 10px;
                background: rgba(255, 255, 255, 0.04);
                border-left: 4px solid; margin-top: 1rem;
            }
            .advice-green  { border-color: #00d97e; background: rgba(0, 217, 126, 0.06); }
            .advice-yellow { border-color: #f5c400; background: rgba(245, 196, 0, 0.06); }
            .advice-red    { border-color: #ff4d4d; background: rgba(255, 77, 77, 0.06); }
            .advice-ai     { border-color: #7c5cfc; background: rgba(124, 92, 252, 0.06); }

            /* ── Hero header ── */
            .hero-header {
                padding: 1.6rem 0 1.2rem 0;
                border-bottom: 1px solid rgba(255,255,255,0.07);
                margin-bottom: 1.6rem;
            }
            .hero-title { font-size: 2.2rem !important; font-weight: 800 !important; letter-spacing: -0.02em; margin: 0 !important; }
            .hero-sub   { color: #5a6488 !important; font-size: 0.95rem; margin-top: 0.3rem; }

            /* ── AI table ── */
            .ai-table { width: 100%; border-collapse: collapse; margin-top: 0.8rem; font-size: 0.92rem; }
            .ai-table th { text-align: left; padding: 10px 14px; background: rgba(0,0,0,0.25); width: 22%; border-bottom: 1px solid #2e3450; color: #8891b5 !important; }
            .ai-table td { padding: 10px 14px; border-bottom: 1px solid #1e2438; }
            .ai-table tr:last-child td, .ai-table tr:last-child th { border-bottom: none; }

            /* ── Badge ── */
            .badge {
                display: inline-block; padding: 2px 10px; border-radius: 20px;
                font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em;
            }
            .badge-green  { background: rgba(0,217,126,0.15); color: #00d97e !important; }
            .badge-yellow { background: rgba(245,196,0,0.15);  color: #f5c400 !important; }
            .badge-red    { background: rgba(255,77,77,0.15);   color: #ff4d4d !important; }

            /* ── Report card ── */
            .report-card {
                padding: 1.4rem 1.6rem; border-radius: 12px;
                background: rgba(20, 25, 45, 0.8);
                border: 1px solid rgba(255,255,255,0.08);
                margin-bottom: 1rem;
            }
            .report-card h4 { margin: 0 0 0.6rem 0; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; color: #6a73a0 !important; }
            .report-card p  { margin: 0; font-size: 1rem; line-height: 1.6; }
            .report-risk    { font-size: 1.6rem; font-weight: 800; }
            .risk-high      { color: #ff4d4d !important; }
            .risk-moderate  { color: #f5c400 !important; }
            .risk-low       { color: #00d97e !important; }
            .location-row { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.9rem; }
            .location-row:last-child { border-bottom: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def get_pollutant_config() -> Dict[str, Dict[str, any]]:
    return {
        "PM2.5 (Fine particulate matter)": {
            "parameter_id": 2,
            "unit": "µg/m³",
            "clinical_title": "Why PM2.5 matters for Commuters",
            "clinical_text": "PM2.5 particles penetrate deep into the lungs. High levels mean deep breathing can increase exposure significantly.\n\n- **Health Impact**: Triggers inflammation and asthma.\n- **Vulnerable Groups**: Cyclists and runners.",
        },
        "O₃ (Ozone)": {
            "parameter_id": 7,
            "unit": "µg/m³",
            "clinical_title": "Why Ozone matters for Commuters",
            "clinical_text": "Ozone is a lung irritant highest on sunny afternoons.\n\n- **Health Impact**: Coughing and throat irritation.\n- **Commuter Tip**: Levels drop in the early morning.",
        },
    }

# -----------------------------------------------------------------------------
# 2. LOGIC: DATA FETCHING & AI INTEGRATION
# -----------------------------------------------------------------------------

def get_commuter_advice(pollutant_key: str, value: float) -> Tuple[str, str]:
    if "PM2.5" in pollutant_key:
        if value < 12: return ("✅ **Green Light:** Air is clean. Safe for biking or walking.", "advice-green")
        elif value < 35.4: return ("⚠️ **Caution:** Moderate particles. Wear a mask near heavy traffic.", "advice-yellow")
        else: return ("🛑 **Hazard:** High pollution. Avoid outdoor exertion.", "advice-red")
    elif "O₃" in pollutant_key:
        if value < 54: return ("✅ **Green Light:** Ozone levels are low.", "advice-green")
        elif value < 70: return ("⚠️ **Caution:** Rising ozone. Carry a rescue inhaler.", "advice-yellow")
        else: return ("🛑 **Hazard:** High Ozone. Limit time outdoors.", "advice-red")
    return ("No specific data available.", "advice-yellow")

def get_ai_insights(df: pd.DataFrame, pollutant_key: str, ai_choice: str) -> str:
    if df.empty:
        return '{"error": "Not enough data for AI analysis."}'

    summary_data = df[['Location', 'Value', 'Unit']].head(5).to_dict('records')
    
    # NEW PROMPT: Enforcing JSON schema
    prompt = (
        f"Act as an environmental health specialist in NYC. Analyze this current {pollutant_key} data: {summary_data}. "
        "You MUST return a valid JSON object with EXACTLY these three keys: "
        "'risk_level' (String: Low, Moderate, High, or Severe), "
        "'summary' (String: 2 sentences on immediate health risks for commuters), "
        "'actionable_tip' (String: 1 strict, direct recommendation)."
    )

    if ai_choice == "OpenAI (GPT-4o)":
        if not OPENAI_API_KEY:
            return '{"error": "OpenAI API key is missing. Check your .env file."}'
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}, # FORCES JSON
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            return f'{{"error": "OpenAI Error: {str(e)}"}}'

    elif ai_choice == "Ollama (gemma3:latest)":
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "gemma3:latest",
            "prompt": prompt,
            "stream": False,
            "format": "json" # FORCES JSON IN OLLAMA
        }
        headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json().get("response", '{"error": "No response from local model."}')
        except Exception as e:
            return f'{{"error": "Ollama Error: {str(e)}"}}'

    return '{"error": "Invalid AI configuration."}'

def fetch_air_quality_data(lat: float, lon: float, radius_km: int, pollutant_key: str) -> Tuple[pd.DataFrame, Dict]:
    config = get_pollutant_config()
    if pollutant_key not in config: return pd.DataFrame(), {}
    
    parameter_id = config[pollutant_key]["parameter_id"]
    unit = config[pollutant_key]["unit"]
    
    headers = {"X-API-Key": OPENAQ_API_KEY} if OPENAQ_API_KEY else {}
    locations_url = "https://api.openaq.org/v3/locations"
    locations_params = {"coordinates": f"{lat},{lon}", "radius": radius_km * 1000, "parameters_id": parameter_id, "limit": 100, "page": 1}
    
    try:
        locations_response = requests.get(locations_url, params=locations_params, headers=headers, timeout=10)
        locations_response.raise_for_status()
        locations = locations_response.json().get("results", [])
    except Exception:
        return pd.DataFrame(), {}
    
    records = []
    for loc in locations[:50]:
        location_id = loc.get("id")
        coords = loc.get("coordinates") or {}
        try:
            latest_response = requests.get(f"https://api.openaq.org/v3/locations/{location_id}/latest", params={"limit": 1}, headers=headers, timeout=5)
            measurements = latest_response.json().get("results", [])
            if measurements:
                m = measurements[0]
                records.append({
                    "Location": loc.get("name", f"Loc {location_id}"),
                    "Value": m.get("value"),
                    "Unit": unit,
                    "Time": m.get("datetime", {}).get("local"),
                    "latitude": coords.get("latitude"),
                    "longitude": coords.get("longitude"),
                })
        except Exception: continue
    
    df = pd.DataFrame.from_records(records).dropna(subset=["latitude", "longitude"]) if records else pd.DataFrame()
    return df, {}

# -----------------------------------------------------------------------------
# 3. GOOGLE MAPS RENDERING
# -----------------------------------------------------------------------------
def render_google_map(df: pd.DataFrame, center_lat: float, center_lon: float):
    if df.empty or not GOOGLE_MAPS_API_KEY: return
    markers_js = "".join([
       f"""{{lat: {r['latitude']}, lng: {r['longitude']}, title: {json.dumps(str(r['Location']))}, val: {json.dumps(f"{r['Value']} {r['Unit']}")} }},\n"""
        for _, r in df.iterrows() if not pd.isna(r['latitude'])
    ])

    html_code = f"""
    <!DOCTYPE html><html><head>
    <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}"></script>
    <script>
      function initMap() {{
        var map = new google.maps.Map(document.getElementById('map'), {{
          zoom: 11, center: {{lat: {center_lat}, lng: {center_lon}}}, disableDefaultUI: true,
          styles: [{{elementType: 'geometry', stylers: [{{color: '#242f3e'}}]}}, {{elementType: 'labels.text.fill', stylers: [{{color: '#746855'}}]}}, {{featureType: 'water', elementType: 'geometry', stylers: [{{color: '#17263c'}}]}}]
        }});
        var infowindow = new google.maps.InfoWindow();
        [{markers_js}].forEach(function(m) {{
           var marker = new google.maps.Marker({{position: {{lat: m.lat, lng: m.lng}}, map: map, title: m.title}});
           marker.addListener('click', function() {{ infowindow.setContent('<div style="color:black;"><b>' + m.title + '</b><br>Pollution: ' + m.val + '</div>'); infowindow.open(map, marker); }});
        }});
      }}
    </script><style>#map {{ height: 500px; width: 100%; border-radius: 12px; }} body {{ margin: 0; }}</style>
    </head><body onload="initMap()"><div id="map"></div></body></html>
    """
    components.html(html_code, height=520)

# -----------------------------------------------------------------------------
# 4. DASHBOARD UI
# -----------------------------------------------------------------------------

def render_sidebar() -> Tuple[float, float, int, str, str]:
    st.sidebar.markdown("### 📍 Location")
    col1, col2 = st.sidebar.columns(2)
    lat = col1.number_input("Latitude",  value=40.7128, format="%.4f")
    lon = col2.number_input("Longitude", value=-74.0060, format="%.4f")

    st.sidebar.markdown("### 🔬 Sensor Settings")
    radius = st.sidebar.slider("Search Radius (km)", 1, 50, 10)
    pollutant = st.sidebar.selectbox("Pollutant Layer", list(get_pollutant_config().keys()))

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 AI Engine")
    ai_choice = st.sidebar.radio(
        "Health Analysis Model",
        ["Instant Check", "GPT-4o Analysis", "Research Mode"],
        help="Instant Check: rule-based, no API key needed.\nGPT-4o Analysis: requires OpenAI key.\nResearch Mode: uses local knowledge base."
    )

    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ How to use"):
        st.markdown(
            "1. Set your **location** (default: Manhattan).\n"
            "2. Adjust the **search radius** to find nearby sensors.\n"
            "3. Choose a **pollutant** to monitor.\n"
            "4. Pick an **AI engine** for health recommendations."
        )

    return lat, lon, radius, pollutant, ai_choice

def _risk_badge(pollutant_key: str, value: float) -> str:
    """Return an HTML badge with color-coded risk label."""
    _, css = get_commuter_advice(pollutant_key, value)
    label_map = {"advice-green": ("Low", "green"), "advice-yellow": ("Moderate", "yellow"), "advice-red": ("High", "red")}
    label, color = label_map.get(css, ("Unknown", "yellow"))
    return f'<span class="badge badge-{color}">{label} Risk</span>'


_REPORT_THRESHOLDS = {"PM2.5": (12.0, 35.4), "O3": (54.0, 70.0), "NO2": (53.0, 53.0)}
_REPORT_ACTIONS = {
    "High":     ["Wear an N95/KN95 mask outdoors.", "Avoid strenuous outdoor activity.", "Use indoor air purifiers if available."],
    "Moderate": ["Consider a light mask near heavy traffic.", "Limit prolonged outdoor exertion.", "Check levels again before evening commute."],
    "Low":      ["Air quality is safe — enjoy outdoor activities.", "No special precautions needed today.", "Good time for outdoor exercise."],
}
_REPORT_GROUPS = {
    "High":     "Children, elderly, and people with asthma or heart disease",
    "Moderate": "People with pre-existing respiratory or cardiovascular conditions",
    "Low":      "No specific groups at elevated risk",
}

def _short_pollutant(pollutant_key: str) -> str:
    if "PM2.5" in pollutant_key: return "PM2.5"
    if "O₃" in pollutant_key or "O3" in pollutant_key: return "O3"
    if "NO2" in pollutant_key: return "NO2"
    return pollutant_key

def _report_level(short_key: str, value: float) -> str:
    lo, hi = _REPORT_THRESHOLDS.get(short_key, (float("inf"), float("inf")))
    if value >= hi: return "High"
    if value >= lo: return "Moderate"
    return "Low"

def render_neighborhood_report(df: pd.DataFrame, pollutant_key: str):
    """Render a polished neighborhood health report — no technical jargon."""
    short = _short_pollutant(pollutant_key)
    avg   = df["Value"].mean()
    level = _report_level(short, avg)
    unit  = df["Unit"].iloc[0] if not df.empty else ""
    risk_color = {"High": "#ff4d4d", "Moderate": "#f5c400", "Low": "#00d97e"}.get(level, "#f5c400")
    icon       = {"High": "🔴", "Moderate": "🟡", "Low": "🟢"}.get(level, "🟡")

    # ── Overall risk banner ──────────────────────────────────────────────────
    st.markdown(
        f'<div class="report-card" style="border-left: 4px solid {risk_color}; padding: 1.6rem 1.8rem;">'
        f'<h4 style="margin-bottom:0.8rem;">Overall Air Quality</h4>'
        f'<div style="display:flex; align-items:baseline; gap:0.8rem;">'
        f'  <span style="font-size:2rem; font-weight:800; color:{risk_color};">{icon} {level} Risk</span>'
        f'</div>'
        f'<p style="margin-top:0.6rem; color:#8891b5 !important; font-size:0.9rem;">'
        f'  Average {short}: <strong style="color:#dde;">{avg:.1f} {unit}</strong> &nbsp;·&nbsp; {len(df)} sensors monitored'
        f'</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    # ── Who is at risk ───────────────────────────────────────────────────────
    with col1:
        st.markdown(
            f'<div class="report-card" style="min-height:140px;">'
            f'<h4>Who Should Take Precautions</h4>'
            f'<p style="font-size:0.95rem; line-height:1.6;">{_REPORT_GROUPS[level]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Actions ──────────────────────────────────────────────────────────────
    with col2:
        actions_html = "".join(
            f'<div style="display:flex; gap:0.6rem; margin-bottom:0.5rem;">'
            f'  <span style="color:{risk_color}; flex-shrink:0;">▸</span>'
            f'  <span style="font-size:0.9rem;">{a}</span>'
            f'</div>'
            for a in _REPORT_ACTIONS[level]
        )
        st.markdown(
            f'<div class="report-card" style="min-height:140px;">'
            f'<h4>What To Do Now</h4>'
            f'{actions_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Top hotspots — build entire card as one string ───────────────────────
    top = df.nlargest(5, "Value")[["Location", "Value", "Unit"]]
    rows_html = ""
    for _, r in top.iterrows():
        c = {"High": "#ff4d4d", "Moderate": "#f5c400", "Low": "#00d97e"}.get(_report_level(short, r["Value"]), "#f5c400")
        rows_html += (
            f'<div style="display:flex; justify-content:space-between; align-items:center;'
            f'     padding:0.55rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">'
            f'  <span style="font-size:0.9rem; color:#ccd;">{r["Location"]}</span>'
            f'  <span style="font-size:0.9rem; font-weight:600; color:{c};">{r["Value"]:.1f} {r["Unit"]}</span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="report-card">'
        f'<h4>Pollution Hotspots Near You</h4>'
        f'{rows_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_dashboard(df: pd.DataFrame, pollutant_key: str, lat: float, lon: float, ai_choice: str):
    config = get_pollutant_config()
    unit = config.get(pollutant_key, {}).get("unit", "")

    if df.empty:
        st.markdown(
            '<div class="advice-box advice-yellow"><h3 style="margin-top:0;">📡 No Sensors Found</h3>'
            '<p>No monitoring stations were detected in this area. Try <strong>increasing the search radius</strong> or adjusting your coordinates.</p></div>',
            unsafe_allow_html=True,
        )
        return

    avg_val = df["Value"].mean()
    badge_html = _risk_badge(pollutant_key, avg_val)

    # ── Metric row ────────────────────────────────────────────��─────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f'<div class="metric-card"><div class="metric-label">Avg Level</div>'
        f'<div class="metric-value">{avg_val:.1f}</div>'
        f'<div class="metric-sub">{unit} &nbsp;{badge_html}</div></div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        f'<div class="metric-card"><div class="metric-label">Peak Hotspot</div>'
        f'<div class="metric-value">{df["Value"].max():.1f}</div>'
        f'<div class="metric-sub">{unit}</div></div>',
        unsafe_allow_html=True,
    )
    c3.markdown(
        f'<div class="metric-card"><div class="metric-label">Cleanest Spot</div>'
        f'<div class="metric-value">{df["Value"].min():.1f}</div>'
        f'<div class="metric-sub">{unit}</div></div>',
        unsafe_allow_html=True,
    )
    c4.markdown(
        f'<div class="metric-card"><div class="metric-label">Sensors Found</div>'
        f'<div class="metric-value">{len(df)}</div>'
        f'<div class="metric-sub">within radius</div></div>',
        unsafe_allow_html=True,
    )

    # ── Health insight panel ─────────────────────────────────────────────────
    if ai_choice == "Instant Check":
        advice_text, css_class = get_commuter_advice(pollutant_key, avg_val)
        st.markdown(
            f'<div class="advice-box {css_class}">'
            f'<h3 style="margin-top:0;">🚦 Commuter Guide</h3><p>{advice_text}</p></div>',
            unsafe_allow_html=True,
        )

    elif ai_choice == "GPT-4o Analysis":
        with st.spinner("Querying GPT-4o for structured health insights..."):
            ai_response_str = get_ai_insights(df, pollutant_key, "OpenAI (GPT-4o)")
        try:
            ai_data = json.loads(ai_response_str)
            if "error" in ai_data:
                st.error(ai_data["error"])
            else:
                risk = ai_data.get("risk_level", "N/A")
                st.markdown(
                    f'<div class="advice-box advice-ai">'
                    f'<h3 style="margin-top:0;">🤖 AI Health Analysis <span style="font-size:0.8rem;font-weight:400;color:#a090f0;">GPT-4o</span></h3>'
                    f'<table class="ai-table">'
                    f'<tr><th>Risk Level</th><td><strong>{risk}</strong></td></tr>'
                    f'<tr><th>Clinical Summary</th><td>{ai_data.get("summary", "N/A")}</td></tr>'
                    f'<tr><th>Actionable Tip</th><td>{ai_data.get("actionable_tip", "N/A")}</td></tr>'
                    f'</table></div>',
                    unsafe_allow_html=True,
                )
        except json.JSONDecodeError:
            st.error("The AI model returned invalid JSON.")
            st.code(ai_response_str, language="text")

    # ── Tabs ─────────────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    tab_report, tab_map, tab_data, tab_clinical, tab_rag = st.tabs(["📋 Neighborhood Report", "🗺️ Live Map", "📊 Data Table", "🩺 Clinical Notes", "🧬 RAG Analysis"])

    with tab_report:
        render_neighborhood_report(df, pollutant_key)

    with tab_map:
        if GOOGLE_MAPS_API_KEY:
            render_google_map(df, lat, lon)
        else:
            st.caption("Google Maps API key not set — using built-in map.")
            st.map(df, use_container_width=True)

    with tab_data:
        st.dataframe(
            df[["Location", "Value", "Unit", "Time"]].sort_values("Value", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with tab_clinical:
        cfg = config.get(pollutant_key, {})
        st.subheader(cfg.get("clinical_title", "Clinical Notes"))
        st.markdown(cfg.get("clinical_text", "No clinical notes available."))

    with tab_rag:
        if ai_choice == "Research Mode":
            st.subheader("🧬 RAG Health Analysis")
            st.caption("Retrieval-Augmented Generation: combining a curated knowledge base with live sensor data.")
            with st.spinner("Retrieving health knowledge and generating recommendations..."):
                kb_path = os.path.join(os.path.dirname(__file__), "air_quality_knowledge_base.txt")
                rag_result = get_rag_health_insights(df, pollutant_key, kb_path, "Ollama")
            st.markdown(
                '<div class="advice-box advice-ai"><h3 style="margin-top:0;">💡 Knowledge-Based Recommendations</h3></div>',
                unsafe_allow_html=True,
            )
            st.markdown(format_rag_response(rag_result))
        else:
            st.info("Select **Research Mode** from the sidebar to enable this analysis.")

# -----------------------------------------------------------------------------
# 5. MAIN EXECUTION
# -----------------------------------------------------------------------------

def main():
    configure_page()

    st.markdown(
        '<div class="hero-header">'
        '<div class="hero-title">Gotham: NYC Air-Pulse 🏙️</div>'
        '<div class="hero-sub">Real-time air quality monitoring for NYC commuters · Powered by OpenAQ</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    lat, lon, radius, pollutant, ai_choice = render_sidebar()

    with st.spinner("Fetching sensor data..."):
        df, _ = fetch_air_quality_data(lat, lon, radius, pollutant)

    render_dashboard(df, pollutant, lat, lon, ai_choice)

if __name__ == "__main__":
    main()