import os
import requests
import csv
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import hmac
import hashlib
import base64
import time
import uuid
import aiohttp

class BlofinApis:
    def __init__(self):
        self.coins = []
        self.last_price = 0
        base_path = Path(__file__).resolve().parent.parent
        self.env_path = base_path / '.env'
        self.data_path = base_path / 'data'
        load_dotenv(self.env_path)
        self.base_url = os.getenv('BLOFIN_API_URL')
        self.demo_base_url = os.getenv('DEMO_BLOFIN_API_URL')
        self.web_socket_url = os.getenv('BLOFIN_WEBSOKET_URL')
        rate_limit = os.getenv('BLOFIN_API_RATE_LIMIT')
        self.bid_size = os.getenv('BID_SIZE')
        self.rate_limit = int(rate_limit)
        self.time_range = 60 * 1000 * self.rate_limit
        self.live_price = 0

        self.api_key = os.getenv('BLOFIN_API_KEY')
        self.secret_key = os.getenv('BLOFIN_API_SECRET')
        self.passphrase = os.getenv('PASSPHRASE')

    def get_header(self, request_path, method, body = ''):
        timestamp = str(int(time.time() * 1000))  # Convert to milliseconds
        nonce = str(uuid.uuid4())  # Generating a random nonce

        prehash_string = f"{request_path}{method}{timestamp}{nonce}{body}"
        signature = hmac.new(
            self.secret_key.encode(),
            prehash_string.encode(),
            hashlib.sha256
        ).hexdigest()
        access_sign = base64.b64encode(signature.encode()).decode()

        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": access_sign,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-NONCE": nonce,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }

        return headers

        
    async def get_coins_list(self, type='apis'):
        request_path = '/api/v1/market/instruments'
        url = self.base_url + request_path
        print(url)
        coins_list_path = self.data_path / 'coins.csv'
        if type == 'volumn':
            coins_list_path = self.data_path / 'coins_volumn.csv'

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        coins = (await response.json()).get("data", [])
                        print(f'---Successfully get the coins list---')
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
                    return self.coins
                    
            except Exception as e:
                print("An error occurred:", e)
    
    def get_coins_data(self, coin_name, bar=None, after=None, before=None, limit=None):

        if not coin_name:
            raise ValueError("The 'coin_name' parameter is required.")

        # if coin_name not in self.coins:
        #     raise ValueError(f"Invalid 'coin_name': {coin_name}. It must be one of the following: {', '.join(self.coins)}")
        request_path = '/api/v1/market/candles'

        url = self.base_url + request_path
        
        if after:
            after += self.time_range
            limit = self.rate_limit
            
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
            response_json = response.json()
        
            # Check if the request was successful
            if response.status_code == 200:
                data = response_json['data']
                correct_order_data = data[::-1]
                return correct_order_data  # Return the JSON data
            else:
                print(f"Failed to retrieve data. HTTP Status Code: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print("An error occurred:", e)
            return None

    def get_tick_price(self, coin_name):
        request_path = '/api/v1/market/tickers'
        url = self.base_url + request_path
        print(url)
        try:
            if not coin_name:
                raise ValueError("The 'coin_name' parameter is required.")

        
            params = { 'instId': coin_name, 'size': 20 }
            
            response = requests.get(url, params = params)
            if response.status_code == 200:
                tickers = response.json()
                last_price = tickers['data'][0]['last']
                self.last_price = float(last_price)
            else:
                print('No price data returned')
            return self.last_price
                
        except Exception as e:
            print("An error occurred:", e)

    async def get_delta(self, coin_name):
        request_path = '/api/v1/market/books'
        url = self.base_url + request_path
        async with aiohttp.ClientSession() as session:
            try: 
                if not coin_name:
                    raise ValueError("The 'coin_name' parameter is required.")
                coin_name = coin_name.replace("/", "-")
                bid_size = int(self.bid_size)
                params = { 'instId': coin_name, 'size': bid_size }
                async with session.get(url, params = params) as response:
                    if response.status == 200:
                        volumn = await response.json()
                        # print(f'volumn for {coin_name}: ', volumn)
                        asks = volumn['data'][0]['asks']
                        bids = volumn['data'][0]['bids']
                        ask_volumn = 0
                        bid_volumn = 0
                        for ask in asks:
                            ask_volumn += float(ask[1])
                        for bid in bids:
                            bid_volumn += float(bid[1])
                        delta = ask_volumn - bid_volumn
                        result = 1 if delta > 0 else -1
                        print(f"-----delta for {coin_name}: {result}-----")
                        return result
                    else:
                        print('No price data returned')
            except Exception as e:
                print("An error occurred:", e, f'for {coin_name}')

    def place_order(self, data):
        request_path = '/api/v1/trade/order'
        url = self.demo_base_url + request_path
        print(url)
        method = 'POST'
        body = data
        print(data)
        header = self.get_header(request_path, method, body=body)
        print(f'header: ', header)
        response = requests.post(url, headers=header, data = body)
        if response.status_code == 200:
            data = response.json()
            print(f'Response Data for setting an order: {data}')
        else:
            print('No price data returned')

    def get_position(self):
        request_path = '/api/v1/account/positions'
        url = self.base_url + request_path
        print(url)
        method = 'GET'
        header = self.get_header(request_path, method)
        print(f'header: ', header)
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            data = response.json()
            print(f'Response Data for setting an order: {data}')
        else:
            print('No price data returned')

# Use cases        
# blofin = BlofinApis()
# blofin.get_coins_list()
# data = blofin.get_coins_data("BTC-USDT")
# lastprice = blofin.get_tick_price("BTC-USDT")
# print(f'Last Price: {lastprice}')