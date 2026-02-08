import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAQ_API_KEY")

def fetch_gotham_latest():
    # Adding '/latest' turns a metadata link into a data link
    url = "https://api.openaq.org/v3/parameters/2/latest"
    
    # We ask for 20 rows to meet the assignment requirement
    params = {"limit": 20}
    headers = {"X-API-Key": API_KEY}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() 
        data = response.json()

        if 'results' in data and data['results']:
            print(f"{'Location ID':<12} | {'Value':<10} | {'Last Updated'}")
            print("-" * 50)
            
            for record in data['results']:
                # The 'latest' endpoint uses 'datetime' instead of 'period'
                loc_id = record.get('locationsId', 'N/A')
                val = record.get('value', 'N/A')
                time = record.get('datetime', {}).get('utc', 'N/A')
                
                print(f"{loc_id:<12} | {val:<10} | {time}")
        else:
            print("No data found for this query.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_gotham_latest()