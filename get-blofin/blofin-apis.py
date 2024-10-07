import os
import requests
import csv
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

class BlofinApis:
    def __init__(self):
        self.coins = []
        self.env_path = Path('..') / '.env'
        self.data_path = Path('..') / 'data'
        load_dotenv(self.env_path)
        self.base_url = os.getenv('BLOFIN_API_URL')
        
    def get_coins_list(self):
        url = self.base_url + 'instruments'
        coins_list_path = self.data_path / 'coins.csv'
        try:
            response = requests.get(url)
            if response.status_code != 200:
                coins = response.json().get("data", [])
                with coins_list_path.open(mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    for coin in coins:
                        coin_name = coin.get("instId")
                        self.coins.append(coin_name)
                        writer.writerow([coin_name])
            else:
                df = pd.read_csv(coins_list_path, header=None)
                self.coins = df[0].values.tolist()
                print(df)
                
        except Exception as e:
            print("An error occurred:", e)
    
    def get_coins_data(self, coin_name, bar=None, after=None, before=None, limit=None):
        """
        Retrieve candlestick chart data from the API.

        :param coin_name: Instrument ID (required).
        :param bar: Bar size (optional).
        :param after: After timestamp (optional).
        :param before: Before timestamp (optional).
        :param limit: Number of results per request (optional).
        :return: JSON response or None if the request fails.
        """
        if not coin_name:
            raise ValueError("The 'coin_name' parameter is required.")

        if coin_name not in self.coins:
            raise ValueError(f"Invalid 'coin_name': {coin_name}. It must be one of the following: {', '.join(self.coins)}")

        url = self.base_url + 'candles'
    
        params = {
            'instId': coin_name,
            'bar': bar,
            'after': after,
            'before': before,
            'limit': limit
        }

        # Remove keys with None values
        params = {key: value for key, value in params.items() if value is not None}
    
        try:
            # Perform the GET request
            response = requests.get(url, params=params)
        
            # Check if the request was successful
            if response.status_code == 200:
                print(response.json())
                return response.json()  # Return the JSON data
            else:
                print(f"Failed to retrieve data. HTTP Status Code: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print("An error occurred:", e)
            return None

blofin = BlofinApis()
blofin.get_coins_list()
blofin.get_coins_data("BTC-USDT")