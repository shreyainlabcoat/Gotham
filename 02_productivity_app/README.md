# Gotham: NYC Air-Pulse

**Actionable air quality intelligence for the urban commuter.**

Gotham is a real-time environmental health dashboard that helps NYC residents and commuters make informed decisions about their daily routes based on live air quality data. It provides actionable recommendations by translating complex atmospheric measurements into simple, color-coded guidance.

---

## Features

✨ **Real-time Air Quality Integration**
- Fetches live sensor data from the [OpenAQ API v3](https://openaq.org/)
- Supports multiple pollutants: PM2.5 (fine particulate matter) and Ozone (O₃)
- Displays measurements from 50+ sensors across NYC

📍 **Interactive Google Maps Visualization**
- Dark-mode "Gotham" themed mapping interface
- Click-to-view pollution levels at specific locations
- Customizable search radius (1-50 km)

🚦 **Commuter Health Guide**
- Green/Yellow/Red traffic light system for quick decision-making
- Pollutant-specific health advice based on real-time measurements
- Vulnerable population warnings (cyclists, runners, those with respiratory conditions)

📊 **Multi-View Dashboard**
- **Live Map**: Interactive Google Maps with pollution markers
- **Data Table**: Detailed sensor readings and timestamps
- **About Panel**: Educational content on pollutants and health impacts

---

## Installation

### Prerequisites
- Python 3.8+
- Pip package manager

### Setup

1. **Clone or download the repository:**
   ```bash
   git clone <repository-url>
   cd 02_productivity_app
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the `02_productivity_app` directory with your API keys:
   ```
   OPENAQ_API_KEY=your_openaq_api_key_here
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```

   - **OpenAQ API Key**: Get one for free at [https://openaq.org/](https://openaq.org/)
   - **Google Maps API Key**: Create one at [Google Cloud Console](https://console.cloud.google.com/) with Maps JavaScript API enabled

---

## Running the App

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

---

## How It Works

### 1. **Data Collection**
- Queries the OpenAQ v3 API for sensor locations within your specified radius
- Retrieves the latest pollution measurements for each location
- Limits to 50 locations per query to avoid API timeouts

### 2. **Commuter Risk Assessment**
- Calculates average, peak, and minimum pollution levels
- Compares values against health thresholds:
  - **PM2.5**: Green (<12), Yellow (12-35.4), Red (>35.4) µg/m³
  - **Ozone**: Green (<54), Yellow (54-70), Red (>70) µg/m³

### 3. **Actionable Recommendations**
- Provides specific health guidance tailored to the pollutant
- Suggests transportation alternatives for high pollution scenarios
- Targets advice toward commuters (cyclists, runners, public transit users)

---

## Pollutants Monitored

### PM2.5 (Fine Particulate Matter)
- **Health Risk**: Penetrates deep into lungs, triggering asthma and cardiovascular stress
- **High-Risk Groups**: Cyclists, runners, outdoor workers
- **Commuter Tip**: Wearing a mask during high PM2.5 reduces exposure significantly

### Ozone (O₃)
- **Health Risk**: Lung irritant that reacts with airway tissue (like a sunburn inside your lungs)
- **High-Risk Groups**: Those with asthma or respiratory conditions
- **Commuter Tip**: Ozone levels are typically lower in early mornings and late evenings

---

## Configuration

### Sidebar Settings
- **Latitude**: Default is 40.7128 (NYC center). Adjust to your commute location.
- **Longitude**: Default is -74.0060 (NYC center).
- **Search Radius**: How far around your location to fetch sensor data (1-50 km).
- **Pollutant Layer**: Select between PM2.5 and Ozone to view.

---

## UI Components

### Dashboard Layout
- **Top Metrics**: Average, peak, and cleanest pollution readings
- **Commuter Health Guide**: Color-coded health recommendations
- **Tabs**:
  - 🗺️ **Live Map**: Interactive visualization with pollution hotspots
  - 📊 **Data Table**: Detailed sensor readings
  - ℹ️ **About Gotham**: Educational information

### Color Scheme
- **Dark Gotham Theme**: Radial gradient background (#202433 → #050609)
- **Text**: Light grey (#e0e0e0) for optimal readability
- **Metrics**: White values on dark cards for high contrast

---

## Troubleshooting

### Error: "Invalid value: File does not exist: app.py"
- Ensure you're running the command from the `02_productivity_app` directory

### Error: "OpenAQ API key is missing"
- Create a `.env` file with `OPENAQ_API_KEY=your_key`
- Reload the Streamlit app

### Error: "Google Maps API key is missing"
- Create/update `.env` file with `GOOGLE_MAPS_API_KEY=your_key`
- The app will fall back to a standard map if not provided

### No sensors found in this area
- Increase the search radius
- Check that your latitude/longitude are correct
- Verify your OpenAQ API key is valid

### API timeout errors
- The app limits queries to 50 locations to prevent timeouts
- Try reducing the search radius
- Wait a few seconds and refresh

---

## API References

- **OpenAQ v3 Documentation**: https://docs.openaq.org/
- **Google Maps JavaScript API**: https://developers.google.com/maps/documentation/javascript
- **EPA Air Quality Standards**: https://www.epa.gov/air-quality

---

## Files Structure

```
02_productivity_app/
├── app.py                      # Main Streamlit application
├── fetch_air_quality.py        # Optional: Helper script for data fetching
├── my_good_query.py            # Optional: Example query utility
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── .env                        # API keys (not included in repo)
```

---

## Technology Stack

- **Streamlit**: Interactive web dashboard framework
- **Pandas**: Data processing and analysis
- **Requests**: HTTP library for API calls
- **Python-dotenv**: Environment variable management
- **Google Maps API**: Interactive mapping
- **OpenAQ API**: Real-time air quality data

---

## Contributing

Found a bug? Have a feature request? Feel free to open an issue or submit a pull request!

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Author

Created as part of the **Gotham Project** for environmental health awareness in urban areas.

---

## Disclaimer

This dashboard is for informational purposes only and should not replace professional medical advice. Always consult healthcare providers for specific health concerns related to air quality or respiratory conditions.

---

*Last Updated: February 2026*
