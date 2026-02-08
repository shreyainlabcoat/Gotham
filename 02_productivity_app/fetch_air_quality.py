import os
import requests
from dotenv import load_dotenv

# 1. Load the keys from your .env file into Python's memory
load_dotenv()

# 2. Grab your OpenAQ key using its name from the .env file
API_KEY = os.getenv("OPENAQ_API_KEY")

def check_nyc_air():
    # The URL for the OpenAQ API (V3)
    url = "https://api.openaq.org/v3/locations?coordinates=40.7128,-74.0060&radius=5000"
    
    # We pass your key in the 'headers' so OpenAQ knows it's you
    headers = {"X-API-Key": API_KEY}

    # 3. Make the request
    response = requests.get(url, headers=headers)

    # 4. Check if it worked (200 = Success!)
    if response.status_code == 200:
        print("✅ Connection Successful! Status Code: 200")
        data = response.json()
        
        # Print the first sensor's name just to see it work
        if data['results']:
            first_station = data['results'][0]['name']
            print(f"Nearest NYC Health Station found: {first_station}")
    else:
        print(f"❌ Failed. Error Code: {response.status_code}")
        print("Check if your API key is correct in the .env file.")

if __name__ == "__main__":
    check_nyc_air()