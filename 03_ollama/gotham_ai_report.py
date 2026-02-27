import json
import os
from typing import Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import OpenAI

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
            .stApp { background: radial-gradient(circle at top left, #202433 0, #050609 55%); }
            h1, h2, h3, h4, h5, h6, p, li, span, div, label { color: #e0e0e0 !important; }
            [data-testid="stMetricLabel"] { color: #afb4c6 !important; }
            [data-testid="stMetricValue"] { color: #ffffff !important; }
            section[data-testid="stSidebar"] {
                background-color: #0f131c;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
            .metric-card {
                padding: 1.2rem; border-radius: 10px; background: rgba(30, 35, 50, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 1rem;
            }
            .metric-label { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em; color: #a0a5b9 !important; }
            .metric-value { font-size: 2rem; font-weight: 700; color: #ffffff !important; }
            .advice-box {
                padding: 1.5rem; border-radius: 8px; background: rgba(255, 255, 255, 0.05);
                border-left: 5px solid; margin-top: 1rem;
            }
            .advice-green { border-color: #00cc66; }
            .advice-yellow { border-color: #ffcc00; }
            .advice-red { border-color: #ff3333; }
            .advice-ai { border-color: #9933ff; }
            
            /* Custom Table Styling for JSON Output */
            .ai-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .ai-table th { text-align: left; padding: 12px; background: rgba(0,0,0,0.2); width: 20%; border-bottom: 1px solid #444; }
            .ai-table td { padding: 12px; border-bottom: 1px solid #444; }
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
    st.sidebar.title("Commuter Settings")
    lat = st.sidebar.number_input("Latitude", value=40.7128, format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=-74.0060, format="%.4f")
    radius = st.sidebar.slider("Search Radius (km)", 1, 50, 10)
    pollutant = st.sidebar.selectbox("Pollutant Layer", list(get_pollutant_config().keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.title("🧠 AI Engine")
    ai_choice = st.sidebar.radio("Select Health Analysis Model:", ["None (Static Rules)", "OpenAI (GPT-4o)"])
    
def render_dashboard(df: pd.DataFrame, pollutant_key: str, lat: float, lon: float, ai_choice: str):
    config = get_pollutant_config()
    unit = config.get(pollutant_key, {}).get("unit", "")
    
    if df.empty:
        st.warning("No sensors found in this area. Try increasing the Radius.")
        return

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">Avg Level</div><div class="metric-value">{df["Value"].mean():.1f} {unit}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">Peak Hotspot</div><div class="metric-value">{df["Value"].max():.1f} {unit}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Cleanest Spot</div><div class="metric-value">{df["Value"].min():.1f} {unit}</div></div>', unsafe_allow_html=True)

    # JSON Parsing & Table Rendering
    if ai_choice == "None (Static Rules)":
        advice_text, css_class = get_commuter_advice(pollutant_key, df["Value"].mean())
        st.markdown(f'<div class="advice-box {css_class}"><h3 style="margin-top:0;">🚦 Commuter Guide</h3><p>{advice_text}</p></div>', unsafe_allow_html=True)
    else:
        with st.spinner(f"Querying {ai_choice} for JSON structured insights..."):
            ai_response_str = get_ai_insights(df, pollutant_key, ai_choice)
        
        try:
            # Parse the string returned by the LLM into a Python dictionary
            ai_data = json.loads(ai_response_str)
            
            if "error" in ai_data:
                st.error(ai_data["error"])
            else:
                st.markdown(f"""
                    <div class="advice-box advice-ai">
                        <h3 style="margin-top:0;">🤖 AI Health Analysis ({ai_choice})</h3>
                        <table class="ai-table">
                            <tr>
                                <th>Risk Level</th>
                                <td style="font-weight: bold; color: #fff;">{ai_data.get('risk_level', 'N/A')}</td>
                            </tr>
                            <tr>
                                <th>Clinical Summary</th>
                                <td>{ai_data.get('summary', 'N/A')}</td>
                            </tr>
                            <tr style="border-bottom: none;">
                                <th>Actionable Tip</th>
                                <td>{ai_data.get('actionable_tip', 'N/A')}</td>
                            </tr>
                        </table>
                    </div>
                """, unsafe_allow_html=True)
        except json.JSONDecodeError:
            st.error("⚠️ The AI model failed to return valid JSON.")
            st.write("Raw Output:", ai_response_str)

    st.write("") 
    tab_map, tab_data = st.tabs(["🗺️ Live Map", "📊 Data Table"])
    with tab_map:
        if GOOGLE_MAPS_API_KEY: render_google_map(df, lat, lon)
        else: st.map(df, width='stretch')
    with tab_data: st.dataframe(df[["Location", "Value", "Unit", "Time"]], width='stretch')

# -----------------------------------------------------------------------------
# 5. MAIN EXECUTION
# -----------------------------------------------------------------------------

def main():
    configure_page()
    st.title("Gotham: NYC Air-Pulse")
    
    lat, lon, radius, pollutant, ai_choice = render_sidebar()
    with st.spinner("Analyzing atmospheric data..."):
        df, _ = fetch_air_quality_data(lat, lon, radius, pollutant)
    
    render_dashboard(df, pollutant, lat, lon, ai_choice)

if __name__ == "__main__":
    main()