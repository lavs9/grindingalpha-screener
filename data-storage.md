
Data to be stored 

Daily EOD : On market working day to be downloaded at 8-9 PM
Holiday list : https://upstox.com/developer/api-documentation/get-market-holidays


1. Listed Securities in NSE
	1. Listed securities : https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv
	2. Listed ETF : https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv
	3. All Indices 
		1. Get all NSE_INDEX from Upstox ( instrument type = INDEX) and store as Indexes separately
		2. 
	4. Historical Download : Not required
	5. Frequency : Daily EOD
2. Market Cap of securities 
	1. Source : https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/PR211025.zip
	2. This file is Zip and inside this file there is a file MCAP01102025 for that respective date need to store the columns as below
		1. Trade Date - to be validated
		2. Symbol - 
		3. Series 
		4. Security Name
		5. Category
		6. Last Trade Date
		7. Face Value(Rs.)
		8. Issue Size
		9. Close Price/Paid up value(Rs.)
		10. Market Cap(Rs.)
	3. Historical : We need to download historical market cap data for all securities here for the last 5 years OR whatever is available ( last 1 year at least) . It can be done by changing the date and hitting the URL and storing the data. *There might be securities which are not part of the listed securities so for them we do not need to store the marketcap for now. In future, we will not update the market cap once the company unlists.*
	4. *It is possible that the marketcap data file is not available post certain dates so we will stop downloading for the dates before that*
	5. Frequency : Daily EOD
3. Bulk and Block Deals 
	1. Block Deals 
		1. Source : https://nsearchives.nseindia.com/content/equities/block.csv
		2. Historical : Not needed, will be provided separately. 
		3. Frequency : Daily EOD
	2. Bulk Deals
		1. Source : https://nsearchives.nseindia.com/content/equities/bulk.csv
		2. Historical : Not needed, will be provided separately
		3. Frequency : Daily EOD
4. Historical Price Download 
	1. For all listed securities, ETF and Indexes from point 1, we need to download the historical prices
	2. Source : Upstox API (https://upstox.com/developer/api-documentation/v3/get-historical-candle-data)
	3. Historical : We need to download the historical data for last 5 years for the universe, for some it will not be available as they are recently listed and we will take from the date they are available. *Need to check if Upstox automatically handles the same without worrying about the listed date*
	4. API data for upstox will be shared separately
5. Daily price and other information download
	1. For the listed securities we need to download the EOD data
	2. Source : Upstox API https://upstox.com/developer/api-documentation/get-full-market-quote
	3. All data except depth to be stored
	4. API data for upstox will be shared separately
	5. Frequency : Daily EOD
6. Industry and Sector
	1. Industry to be scraped from NSE website code for which is mentioned below 
	2. Issue with above code is that it needs to be provided cookie manually -- We can conitnue to keep this code manual where in the API call we pass the cookie also and it downloads for all. 
	3. Frequency : Once a week 
	4. Historical - Not needed
	5. This data should just update the industry sector etc available. 
7. Surveillance measures 
	1. Source : https://nsearchives.nseindia.com/content/cm/REG1_IND211025.csv
	2. Frequency : Daily EOD
	3. Historical : Not needed
	4. Data should be linked to security list
8. Index constituents 
	1. Source : Niftyindices.com
	2. To be shared manually and updated manually once everymonth
9. Option Chain -- to do Later


How things should link
1. Symbol and ISIN should be primary identifier for security and ETF
2. Indices should be tagged separately. 
3. All the reports and historical data should be linked to Symbol/ISIN
4. Historical prices, Market Cap should be kept in timeseries DB ( Clickhouse like) with compression to avoid data bulk up and also enable fast querying. 


```
# NSE Symbols File URL

NSE_SYMBOLS_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

  

headers = {

"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",

"Accept": "text/csv",

"Referer": "https://www.nseindia.com/market-data/securities-available-for-trading",

"Cookie" : "_abck=539108423F076C569291CF5A1B66F9AB~-1~YAAQjdcLF7pd362VAQAA9TfRsg0XRg6fnlrJ1CFaDNPi+jZZ0EHEYoROxkjCBTCBNMuiQ0jmZk6YR8kpEkurry54E5Mlqxg83voZRm5kn6NQly2QRpf22lcpJwg3llKw9HfyD4ae5qPXNBQtBVRW4mtgVnBg1GHGrd7F0/whLODdnkKNJYNUfPSiOKnQLQp8VF3gh9Tdxo0uwm+lB8nKB4POq4KqV/qCCMq/o0epLcoMI/ByKaGR0Ifh11BYOzhHTKH5qSmvF55nJ6AmoyJxc2LSRsKcVc5P3++Owzd1utdzSvvJVRSKsEEndsAofklk1gvryzKX7UZgMiRd8iEMvr255pvtFB8kOjGSoKak8jJr9+4IWORhqqlrwmY5tzqHiLsm/lVHkB/ai/MY5FI9HiD3Zl2QTkTeDD7bvU8R6y3HshUu6Y7C/9iEdLbmh9l0j5zSWvUEKm5xOmFZ82GU7fa8MfbdkfLufuKtanR6QrmWsvh2QzZu3yqU/+EiyzTU+XTxr/mCvxRYDQ==~-1~-1~-1; bm_sz=F6D25B2EE02E6A35DF485D27D48CD406~YAAQjdcLF7td362VAQAA9TfRshsccZSgs7BjvHtfw/J2GKXyhTS01U2a6Mpia1F/msAFGk7SUnK8YmXA8p+prRpfZFjvu1HVV5vVxn4MYzNPhzNVZVn+zvfjalN1F6hLiWODp84WdTlIS+NRflJfuD93xqlhRCTxrlCXHNuMc8fE6xG17/C3UjFuptL2ujsqfJSYLBz1096rInLGjtm9soy3SBHCBvsPmCQ0yD11d0sBxpPnOvshHdKsel6qDvYy4ct3YqwKlyq7JpRfb2MetIv7b5PASI6oqAwuspuwJqeb7YslbUsSVh+qnL0H0P+8lyuUbLdv5QqiAmd3aS+ykzK+wN9NpTvpbmxwLsU=~3223862~4342596"

}

  

def download_symbols():

"""Downloads NSE symbols list and saves it as a CSV file."""

session = requests.Session() # Maintain session for cookies

  

try:

response = session.get(NSE_SYMBOLS_URL, headers=headers, timeout=15) # Add timeout

response.raise_for_status() # Raise error for bad responses

  

if response.status_code == 200:

df = pd.read_csv(io.StringIO(response.text)) # Read CSV directly from response

df.to_csv("/content/drive/MyDrive/Trading/nse_listed_data.csv", index=False) # Save to file

print("✅ NSE symbols downloaded successfully!")

else:

print(f"❌ Failed! HTTP Status: {response.status_code}")

  

except requests.exceptions.RequestException as e:

print(f"❌ Error fetching data: {e}")

  

# Run the function

download_symbols()

# NSE Symbols File (Already downloaded CSV)

FILE_PATH = "/content/drive/MyDrive/Trading/nse_listed_data.csv"

  

# Industry data Output File (To store fetched data)

OUTPUT_FILE = "/content/drive/MyDrive/Trading/nse_industry_data_sept2025.csv"

  

# NSE API URL Template

API_URL = "https://www.nseindia.com/api/quote-equity?symbol={}"

  

# Headers to mimic a browser

headers = {

"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",

"Accept": "application/json",

"Referer": "https://www.nseindia.com/get-quotes/equity?symbol=XYZ",

"Cookie": "your_actual_cookie_here" # Replace with your NSE session cookie

}

  

def load_symbols(file_path):

"""Reads the NSE equity symbols from the manually uploaded CSV file."""

df = pd.read_csv(file_path)

return df["SYMBOL"].tolist() # Extract symbols list

  

def get_last_saved_index(output_file):

"""Finds the last fetched record from the saved CSV to resume fetching."""

if os.path.exists(output_file):

df = pd.read_csv(output_file)

last_symbol = df["Symbol"].iloc[-1] # Get the last symbol fetched

return last_symbol

return None # Start from the first record if no file exists

  

def get_industry(symbol, cookie_value):

"""Fetches Industry data, from NSE API."""

encoded_symbol = urllib.parse.quote(symbol) # Encode special characters

url = API_URL.format(encoded_symbol)

  

headers["Cookie"] = cookie_value # Update cookie dynamically

  

try:

response = requests.get(url, headers=headers, timeout=10)

  

if response.status_code == 403: # Forbidden (likely due to expired cookie)

print("\n🔴 Cookie expired! Please enter a new NSE session cookie.")

new_cookie = input("Enter new cookie value: ")

return get_industry(symbol, new_cookie) # Retry with new cookie

  

elif response.status_code == 200:

data = response.json()

industry_info = data["industryInfo"]

macro = industry_info["macro"]

sector = industry_info["sector"]

industry = industry_info["industry"]

basicIndustry = industry_info["basicIndustry"]

print(f"✅ {symbol}: Industry data fetched successfully!")

return macro, sector, industry, basicIndustry

  

else:

print(f"❌ Failed to fetch Industry for {symbol}. HTTP Status: {response.status_code}")

return None

  

except requests.exceptions.RequestException as e:

print(f"❌ Error fetching Industry for {symbol}: {e}")

return None

  

# Load symbols list

symbols = load_symbols(FILE_PATH)

  

# Get the last fetched symbol (to resume if interrupted)

last_saved_symbol = get_last_saved_index(OUTPUT_FILE)

  

# Determine starting index

start_index = 0

if last_saved_symbol:

if last_saved_symbol in symbols:

start_index = symbols.index(last_saved_symbol) + 1 # Resume from next symbol

else:

print(f"⚠️ Last saved symbol {last_saved_symbol} not found in the list! Starting from the beginning.")

  

# Start fetching FFMC data

cookie = input("Enter NSE session cookie: ").strip() # Prompt user for cookie

  

industry_data = []

  

# Resume fetching from where it left off

for i, symbol in enumerate(symbols[start_index:], start=start_index + 1):

macro, sector, industry, basicIndustry = get_industry(symbol, cookie)

  

if macro is not None:

industry_data.append({"Symbol": symbol, "Macro": macro, "Sector": sector, "Industry" : industry, "BasicIndustry": basicIndustry})

  

# Append to CSV (incremental saving to prevent data loss)

pd.DataFrame(industry_data).to_csv(OUTPUT_FILE, mode='a', header=not os.path.exists(OUTPUT_FILE), index=False)

  

# Respect NSE rate limits (Avoid blocking)

time.sleep(1) # Pause for 1 second per request

  

print("✅ Industry data collection complete!")
```
