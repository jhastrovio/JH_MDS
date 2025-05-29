import requests
import os

# List of FX symbols to look up
SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF", "USDCAD", "NZDUSD"
]

# Get OAuth token from environment or prompt user
access_token = os.environ.get("SAXO_API_TOKEN")
if not access_token:
    access_token = input("Enter your Saxo OAuth access token: ")

for symbol in SYMBOLS:
    url = f"https://gateway.saxobank.com/openapi/ref/v1/instruments?Keywords={symbol}&AssetTypes=FxSpot"
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"Looking up UIC for {symbol}...")
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        instruments = data.get("Data", [])
        if instruments:
            uic = instruments[0]["Uic"]
            print(f"{symbol}: UIC = {uic}")
        else:
            print(f"No instrument found for {symbol}")
    else:
        print(f"Failed to fetch UIC for {symbol}: {resp.status_code} {resp.text}")
