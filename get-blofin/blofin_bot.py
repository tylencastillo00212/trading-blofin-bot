import os
import threading
from .live_data import LiveData
from .gen_linebreak import LineBreak
from .trend import GetTrend
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from .blofin_apis import BlofinApis
import time
import json
from websocket import create_connection

class BlofinBot:
    def __init__(self):
        base_path = Path(__file__).resolve().parent.parent
        env_path = base_path / '.env'
        self.data_path = base_path / 'data'
        load_dotenv(env_path)
        self.result_path = self.data_path / 'result.csv'
        self.lines  =  os.getenv('LINEBREAK_NUM')
        self.interval  =  os.getenv('TIME_INTERVAL')
        num_threads = os.getenv('NUM_THREADS')
        self.timeformat = os.getenv('DATETIME_FORMAT')
        self.maincoin = os.getenv('MAIN_COIN')
        self.horizon_num = os.getenv('HORIZON_NUM')
        self.binancecoin = self.maincoin.replace("-", "/")
        self.num_threads = int(num_threads)
        self.percent = 0
        self.positive_trend = 0.0
        self.trend = []
        self.coins_list_path = self.data_path / 'coins.csv'
        self.blofin_apis = BlofinApis()
        self.live_price = 0
        self.upline_val = 0
        self.downline_val = 0
        self.upline_index = 0
        self.downline_index = 0
        self.horizon_lines = []

    def get_trend(self, currency):
        print('----------------------------------------------------')
        print(f'---------Start Calculation of {currency}------------')
        print('----------------------------------------------------')
        # live_data = LiveData(currency)
        # live_data.update_csv_realtime()
        # linebreak = LineBreak(self.interval, self.lines, currency)
        # linebreak.get_candlestick_with_interval()
        # linebreak.get_linebreak_with_interval()
        get_trend = GetTrend(self.interval, self.lines, currency)
        get_trend.export_data()
        self.horizon_lines = get_trend.horizon_lines
        print(f'horizon_lines: {self.horizon_lines}')
        # trend = get_trend.get_trend()
        print('----------------------------------------------------')
        print(f'-----------End Calculation of {currency}------------')
        print('----------------------------------------------------')
        return 
    
    def get_updown(self):
        lastprice = self.blofin_apis.get_tick_price(self.maincoin)
        if not len(self.horizon_lines):
            return 0
        for i, value in enumerate(self.horizon_lines):
            if value < lastprice:
                self.downline_index = i
                self.downline_val = value
            elif value > lastprice:
                self.upline_index = i
                self.upline_val = value
                break
        print(f'downline_index: {self.downline_index}')
        print(f'downline_val: {self.downline_val}')
        print(f'upline_index: {self.upline_index}')
        print(f'upline_val: {self.upline_val}')

    def get_delta(self):
        coins = self.blofin_apis.get_coins_list(type='volumn')
        # print(f'coins: {coins}')
        result = 0
        for coin in coins:
            value = self.blofin_apis.get_delta(coin)
            result += value
            print(f'delta for {coin}: ', value)
        print(f'result: {result}')
        return result
    
    def websocket_config(self, coin):
        url = self.blofin_apis.web_socket_url + 'public'
        ws = create_connection(url)
        params = {
            "op": "subscribe",
            "args": [
                {
                    "channel": "trades",
                    "instId": f"{coin}"
                }
            ]
        }
        print(f"Connected to Blofin WebSocket for {coin}")

        # print({url, ws, params})

        # Convert the parameters dictionary to a JSON string
        params_json = json.dumps(params)

        # Send the parameters through the WebSocket connection
        ws.send(params_json)

        while True:
            try:
                # Receive and print a response (for validation or logging)
                message = ws.recv()
                # print(f'message: {message}')
                self.on_message(ws, message)
            except Exception as e:
                print(f"Error: {e}")
                break
        # Close the connection when done
        ws.close()
    
    def on_message(self, ws, message):
        data = json.loads(message)
        # print(f"web socket data: {data}")
        # current_price = float(data['p'])
        if 'data' in data:
            self.live_price = data['data'][0]['price']
        print(f"web socket data: {self.live_price}")

        # Check if the current price exceeds the threshold
        # if current_price > PRICE_THRESHOLD:
            # print("Alert: BTC price is above the threshold!")

    def execute(self):
        self.get_trend(self.binancecoin)
        self.get_updown()
        # self.get_delta()
        # self.websocket_config(self.maincoin)
        
    
blofin_bot = BlofinBot()
blofin_bot.execute()
# print(percent)

    
# print(f'live price: {live_price}')