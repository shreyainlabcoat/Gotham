import json
import os
from typing import Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# -----------------------------------------------------------------------------

# Load environment variables
load_dotenv()
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # Updated variable name

def configure_page() -> None:
    st.set_page_config(
        page_title="Gotham: NYC Air-Pulse",
        page_icon="🏙️",
        layout="wide",
    )

    # CUSTOM CSS: Dark Mode "Gotham" Theme & Text Visibility Fixes
    st.markdown(
        """
        <style>
            /* Main Background - Dark Gotham Gradient */
            .stApp {
                background: radial-gradient(circle at top left, #202433 0, #050609 55%);
            }
            
            /* Text Visibility Overrides - Forces text to be white/light grey */
            h1, h2, h3, h4, h5, h6, p, li, span, div, label {
                color: #e0e0e0 !important;
            }
            
            /* Streamlit Metric Styling */
            [data-testid="stMetricLabel"] {
                color: #afb4c6 !important;
            }
            [data-testid="stMetricValue"] {
                color: #ffffff !important;
            }

            /* Sidebar Styling */
            section[data-testid="stSidebar"] {
                background-color: #0f131c;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            /* Custom Metric Cards */
            .metric-card {
                padding: 1.2rem;
                border-radius: 10px;
                background: rgba(30, 35, 50, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                margin-bottom: 1rem;
            }
            .metric-label {
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #a0a5b9 !important;
            }
            .metric-value {
                font-size: 2rem;
                font-weight: 700;
                color: #ffffff !important;
            }
            .metric-subtitle {
                font-size: 0.8rem;
                color: #868aa0 !important;
            }

            /* Advice Box Styling */
            .advice-box {
                padding: 1.5rem;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.05);
                border-left: 5px solid;
                margin-top: 1rem;
            }
            .advice-green { border-color: #00cc66; }
            .advice-yellow { border-color: #ffcc00; }
            .advice-red { border-color: #ff3333; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def get_pollutant_config() -> Dict[str, Dict[str, any]]:
    """
    Configuration for pollutants, including API parameters and Clinical context.
    Parameter IDs: PM2.5 = 2, O3 = 7
    """
    return {
        "PM2.5 (Fine particulate matter)": {
            "parameter_id": 2,
            "unit": "µg/m³",
            "clinical_title": "Why PM2.5 matters for Commuters",
            "clinical_text": (
                "PM2.5 particles are small enough to penetrate deep into the lungs. "
                "For commuters, high levels mean that deep breathing (like during biking "
                "or running) can increase exposure significantly.\n\n"
                "- **Health Impact**: Triggers inflammation, asthma attacks, and cardiovascular stress.\n"
                "- **Vulnerable Groups**: Cyclists, runners, and those waiting near busy roadway intersections."
            ),
        },
        "O₃ (Ozone)": {
            "parameter_id": 7,
            "unit": "µg/m³",
            "clinical_title": "Why Ozone matters for Commuters",
            "clinical_text": (
                "Ozone is a lung irritant often highest on hot, sunny afternoons. "
                "It reacts with lung tissue like a sunburn inside your airways.\n\n"
                "- **Health Impact**: Coughing, throat irritation, and reduced lung capacity.\n"
                "- **Commuter Tip**: Ozone levels often drop in the early morning and late evening."
            ),
        },
    }

# -----------------------------------------------------------------------------
# 2. LOGIC: DATA FETCHING & COMMUTER ADVICE
# -----------------------------------------------------------------------------

def get_commuter_advice(pollutant_key: str, value: float) -> Tuple[str, str]:
    """
    Returns (Advice Text, CSS Class) based on pollutant levels.
    """
    if "PM2.5" in pollutant_key:
        if value < 12:
            return ("✅ **Green Light:** Air is clean. Safe for biking, walking, or running to work.", "advice-green")
        elif value < 35.4:
            return ("⚠️ **Caution:** Moderate particles. Sensitive groups (asthma/heart conditions) should wear a mask if walking near heavy traffic.", "advice-yellow")
        else:
            return ("🛑 **Hazard:** High pollution. Avoid outdoor exertion. Recommend taking the subway, bus, or taxi. Keep windows closed.", "advice-red")
    
    elif "O₃" in pollutant_key:
        if value < 54:
            return ("✅ **Green Light:** Ozone levels are low. Safe for outdoor commute.", "advice-green")
        elif value < 70:
            return ("⚠️ **Caution:** Rising ozone. If you have asthma, carry your rescue inhaler. Consider reducing walking pace.", "advice-yellow")
        else:
            return ("🛑 **Hazard:** High Ozone. Limit time outdoors. Avoid biking or jogging during peak afternoon hours.", "advice-red")
            
    return ("No specific data available.", "advice-yellow")

def fetch_air_quality_data(lat: float, lon: float, radius_km: int, pollutant_key: str) -> Tuple[pd.DataFrame, Dict]:
    """
    Fetch latest measurements from OpenAQ API v3.
    Uses /v3/locations endpoint with coordinates and parameters_id filter,
    then fetches latest measurements for each location.
    """
    config = get_pollutant_config()
    if pollutant_key not in config:
        st.error(f"Invalid pollutant key: {pollutant_key}")
        return pd.DataFrame(), {}
    
    parameter_id = config[pollutant_key]["parameter_id"]
    unit = config[pollutant_key]["unit"]
    
    headers = {}
    if not OPENAQ_API_KEY:
        st.error("⚠️ OpenAQ API key is missing. Please set OPENAQ_API_KEY in your .env file.")
        return pd.DataFrame(), {}
    headers["X-API-Key"] = OPENAQ_API_KEY
    
    # Step 1: Get locations within radius that have this parameter
    locations_url = "https://api.openaq.org/v3/locations"
    locations_params = {
        "coordinates": f"{lat},{lon}",
        "radius": radius_km * 1000,
        "parameters_id": parameter_id,
        "limit": 100,
        "page": 1,
    }
    
    try:
        locations_response = requests.get(locations_url, params=locations_params, headers=headers, timeout=10)
        locations_response.raise_for_status()
        locations_data = locations_response.json()
    except requests.exceptions.HTTPError as e:
        error_msg = f"⚠️ API Error: {e}"
        if locations_response.status_code == 404:
            error_msg += "\nEndpoint not found. Please verify your API key is valid."
        elif locations_response.status_code == 422:
            error_msg += "\nInvalid parameters. Check coordinates and radius values."
        st.error(error_msg)
        return pd.DataFrame(), {}
    except Exception as e:
        st.error(f"⚠️ API Error: {e}")
        return pd.DataFrame(), {}
    
    locations = locations_data.get("results", [])
    if not locations:
        return pd.DataFrame(), {}
    
    # Step 2: Fetch latest measurements for each location (limit to avoid too many calls)
    records = []
    max_locations = min(50, len(locations))  # Limit to 50 locations to avoid timeout
    
    for loc in locations[:max_locations]:
        location_id = loc.get("id")
        location_name = loc.get("name", f"Location {location_id}")
        coords = loc.get("coordinates") or {}
        
        # Get latest measurements for this location
        latest_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
        latest_params = {
            "limit": 1,  # Just get the latest one
            "page": 1,
        }
        
        try:
            latest_response = requests.get(latest_url, params=latest_params, headers=headers, timeout=5)
            latest_response.raise_for_status()
            latest_data = latest_response.json()
            
            # Get the first measurement (should be for our parameter since we filtered locations)
            measurements = latest_data.get("results", [])
            if measurements:
                measurement = measurements[0]
                datetime_obj = measurement.get("datetime") or {}
                measurement_coords = measurement.get("coordinates") or coords
                
                records.append({
                    "Location": location_name,
                    "Value": measurement.get("value"),
                    "Unit": unit,
                    "Time": datetime_obj.get("local") if isinstance(datetime_obj, dict) else None,
                    "latitude": measurement_coords.get("latitude") or coords.get("latitude"),
                    "longitude": measurement_coords.get("longitude") or coords.get("longitude"),
                })
        except Exception:
            # If latest fetch fails, skip this location
            continue
    
    df = pd.DataFrame.from_records(records)
    if not df.empty:
        df = df.dropna(subset=["latitude", "longitude"])
    
    return df, locations_data.get("meta", {})

# -----------------------------------------------------------------------------
# 3. GOOGLE MAPS RENDERING
# -----------------------------------------------------------------------------

def render_google_map(df: pd.DataFrame, center_lat: float, center_lon: float):
    """
    Generates an HTML embed for Google Maps JavaScript API with Dark Mode styling.
    """
    if df.empty:
        st.info("No data to display on map.")
        return
    
    if not GOOGLE_MAPS_API_KEY:
        st.error("Google Maps API key is missing. Please set GOOGLE_MAPS_API_KEY in your .env file.")
        return

    # Create marker JS array
    markers_js = ""
    for _, row in df.iterrows():
        # Properly escape JavaScript string (handle quotes, newlines, etc.)
        loc_name = json.dumps(str(row['Location']))  # JSON encoding handles all escaping
        val = row['Value']
        unit = row['Unit']
        # Handle NaN/None values
        if pd.isna(val):
            val_display = "N/A"
        else:
            val_display = f"{val} {unit}" if not pd.isna(unit) else str(val)
        val_display_escaped = json.dumps(val_display)
        
        lat = row['latitude']
        lon = row['longitude']
        # Skip if coordinates are invalid
        if pd.isna(lat) or pd.isna(lon):
            continue
            
        markers_js += f"{{lat: {lat}, lng: {lon}, title: {loc_name}, val: {val_display_escaped}}},\n"

    html_code = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}"></script>
        <script>
          function initMap() {{
            var center = {{lat: {center_lat}, lng: {center_lon}}};
            
            // Dark Mode Styles for "Gotham" feel
            var darkStyle = [
              {{elementType: 'geometry', stylers: [{{color: '#242f3e'}}]}},
              {{elementType: 'labels.text.stroke', stylers: [{{color: '#242f3e'}}]}},
              {{elementType: 'labels.text.fill', stylers: [{{color: '#746855'}}]}},
              {{featureType: 'road', elementType: 'geometry', stylers: [{{color: '#38414e'}}]}},
              {{featureType: 'road', elementType: 'geometry.stroke', stylers: [{{color: '#212a37'}}]}},
              {{featureType: 'water', elementType: 'geometry', stylers: [{{color: '#17263c'}}]}}
            ];

            var map = new google.maps.Map(document.getElementById('map'), {{
              zoom: 11,
              center: center,
              styles: darkStyle,
              disableDefaultUI: true,
            }});

            var infowindow = new google.maps.InfoWindow();
            var markers = [{markers_js}];

            markers.forEach(function(m) {{
               var marker = new google.maps.Marker({{
                 position: {{lat: m.lat, lng: m.lng}},
                 map: map,
                 title: m.title
               }});
               
               marker.addListener('click', function() {{
                 infowindow.setContent(
                    '<div style="color:black; font-family:sans-serif;">' + 
                    '<b>' + m.title + '</b><br>' + 
                    'Pollution: ' + m.val + 
                    '</div>'
                 );
                 infowindow.open(map, marker);
               }});
            }});
          }}
        </script>
        <style>
           #map {{ height: 500px; width: 100%; border-radius: 12px; }}
           body {{ margin: 0; padding: 0; background: transparent; }}
        </style>
      </head>
      <body onload="initMap()">
        <div id="map"></div>
      </body>
    </html>
    """
    
    components.html(html_code, height=520)

# -----------------------------------------------------------------------------
# 4. DASHBOARD UI
# -----------------------------------------------------------------------------

def render_sidebar() -> Tuple[float, float, int, str]:
    st.sidebar.title("Commuter Settings")
    st.sidebar.markdown("Configure your route location.")

    default_lat = 40.7128
    default_lon = -74.0060

    lat = st.sidebar.number_input("Latitude", value=default_lat, format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=default_lon, format="%.4f")
    radius = st.sidebar.slider("Search Radius (km)", 1, 50, 10)
    
    pollutant = st.sidebar.selectbox(
        "Pollutant Layer", 
        list(get_pollutant_config().keys())
    )
    
    return lat, lon, radius, pollutant

def render_dashboard(df: pd.DataFrame, pollutant_key: str, lat: float, lon: float):
    config = get_pollutant_config()
    if pollutant_key not in config:
        st.error(f"Invalid pollutant key: {pollutant_key}")
        return
    
    unit = config[pollutant_key]["unit"]
    
    if df.empty:
        st.warning("No sensors found in this area. Try increasing the Radius.")
        return

    avg_val = df["Value"].mean()
    max_val = df["Value"].max()
    min_val = df["Value"].min()

    # Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Avg Level</div><div class="metric-value">{avg_val:.1f} {unit}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Peak Hotspot</div><div class="metric-value">{max_val:.1f} {unit}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Cleanest Spot</div><div class="metric-value">{min_val:.1f} {unit}</div></div>', unsafe_allow_html=True)

    # Commuter Advice
    advice_text, css_class = get_commuter_advice(pollutant_key, avg_val)
    st.markdown(f"""
        <div class="advice-box {css_class}">
            <h3 style="margin-top:0;">🚦 Commuter Health Guide</h3>
            <p style="font-size: 1.1rem;">{advice_text}</p>
        </div>
    """, unsafe_allow_html=True)

    st.write("") 
    
    # TABS: Map / Data / Info
    tab_map, tab_data, tab_info = st.tabs(["🗺️ Live Map", "📊 Data Table", "ℹ️ About Gotham"])
    
    with tab_map:
        if GOOGLE_MAPS_API_KEY:
            # Use Google Maps if key is present
            render_google_map(df, lat, lon)
        else:
            # Fallback to Standard Map
            st.warning("⚠️ Google Maps API Key not found. Displaying standard map.")
            st.map(df, use_container_width=True)
    
    with tab_data:
        st.dataframe(df[["Location", "Value", "Unit", "Time"]], use_container_width=True)
        
    with tab_info:
        st.markdown("""
        ### About Gotham: NYC Air-Pulse
        **Gotham** is an environmental health dashboard designed to help NYC residents minimize exposure to urban pollutants.
        
        **Features:**
        * **Real-time Integration:** Pulls live sensor data via the OpenAQ API.
        * **Google Maps:** Uses the Google Maps Platform for dark-mode street visualization.
        * **Commuter Guide:** Translates complex atmospheric data (µg/m³) into actionable "Green/Yellow/Red" light advice.
        """)

# -----------------------------------------------------------------------------
# 5. MAIN EXECUTION
# -----------------------------------------------------------------------------

def main():
    configure_page()
    
    st.title("Gotham: NYC Air-Pulse")
    st.caption("Actionable air quality intelligence for the urban commuter.")

    # Sidebar Inputs
    lat, lon, radius, pollutant = render_sidebar()

    # Data Fetching
    with st.spinner("Analyzing atmospheric data..."):
        df, meta = fetch_air_quality_data(lat, lon, radius, pollutant)

    # Render UI
    render_dashboard(df, pollutant, lat, lon)
    
    # Clinical Context Footer
    st.markdown("---")
    config = get_pollutant_config()
    if pollutant in config:
        clinical = config[pollutant]
        st.info(f"**{clinical['clinical_title']}:** {clinical['clinical_text']}")

if __name__ == "__main__":
    main()