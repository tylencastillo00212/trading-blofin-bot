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
import websockets
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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

        self.position = 0
        self.direction = 'NONE'
        self.trigger = 0


    def get_trend(self, currency):
        print('----------------------------------------------------')
        print(f'---------Start Calculation of {currency}------------')
        print('----------------------------------------------------')
        live_data = LiveData(currency)
        live_data.update_csv_realtime()
        linebreak = LineBreak(self.interval, self.lines, currency)
        linebreak.get_candlestick_with_interval()
        linebreak.get_linebreak_with_interval()
        get_trend = GetTrend(self.interval, self.lines, currency)
        get_trend.export_data()
        self.horizon_lines = get_trend.horizon_lines
        # print(f'horizon_lines: {self.horizon_lines}')
        # trend = get_trend.get_trend()
        print('----------------------------------------------------')
        print(f'-----------End Calculation of {currency}------------')
        print('----------------------------------------------------')
        return 
    
    def get_updown(self):
        lastprice = self.blofin_apis.get_tick_price(self.maincoin)
        length = len(self.horizon_lines) 
        if not len(self.horizon_lines):
            return 0
        for i, value in enumerate(self.horizon_lines):
            if value < lastprice:
                self.downline_index = i
                self.downline_val = float(value)
            elif value > lastprice:
                self.upline_index = i
                self.upline_val = float(value)
                break
        if self.downline_index == 0:
            self.downline_index = -1
            self.downline_val = 0
        elif self.upline_index == 0:
            self.upline_index = length
            self.upline_val = float('inf')
        print(f'downline_index: {self.downline_index}')
        print(f'downline_val: {self.downline_val}')
        print(f'upline_index: {self.upline_index}')
        print(f'upline_val: {self.upline_val}')

    async def get_delta(self):
        coins = await self.blofin_apis.get_coins_list(type='volumn')
        # print(f'coins: {coins}')
        result = 0
        for coin in coins:
            try:
                # Fetch delta for each coin sequentially
                delta = await self.blofin_apis.get_delta(coin)
                result += delta
            except Exception as e:
                print(f"Error fetching delta for {coin}: {e}")
        
        print(f'Result for getting delta: {result}')
        return result
    
    async def websocket_config(self, coin):
        url = self.blofin_apis.web_socket_url + 'public'
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
        
        while True:
            try:
                async with websockets.connect(url) as ws:
                    await ws.send(json.dumps(params))

                    while True:
                        try:
                            # Receive and print a response (for validation or logging)
                            message = await ws.recv()
                            # print(f'message: {message}')
                            await self.on_message(ws, message)
                        except Exception as e:
                            print(f"Error: {e}")
                            break
            except Exception as e:
                print(f"WebSocket connection error: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)  # Wait before retrying
            # Close the connection when done

    def order_trigger(self, price):
        # print(f'upline index: {self.upline_index}')
        length = len(self.horizon_lines)
        # print(length)
        if price > self.upline_val:
            self.upline_index += 1
            self.downline_index += 1
            print(f'--Trigger: the price touched upper line--')
            if self.upline_index >= length:
                self.upline_val = float('inf')
            else:
                self.upline_val = float(self.horizon_lines[self.upline_index])
            self.downline_val = float(self.horizon_lines[self.downline_index])
            print(f'Horizon Range: [{self.downline_val, self.upline_val}]')
            return True
        elif price < self.downline_val:
            self.upline_index -= 1
            self.downline_index -= 1
            print(f'--Trigger: the price touched lower line--')
            self.upline_val = float(self.horizon_lines[self.upline_index])
            if self.downline_index == 0:
                self.downline_val = 0
            else: 
                self.downline_val = float(self.horizon_lines[self.downline_index])
            print(f'Horizon Range: [{self.downline_val, self.upline_val}]')
            return True
        else:
            # print(f'--No Trigger Occurred--')
            # print(f'Horizon Range: [{self.downline_val, self.upline_val}]')
            return False
    
    async def on_message(self, ws, message):
        data = json.loads(message)
        # print(f"web socket data: {data}")
        # current_price = float(data['p'])
        if 'data' in data:
            price = float(data['data'][0]['price'])
            self.live_price = price
            # print(f"web socket data: {self.live_price}")
            trigger = self.order_trigger(price)
            if (trigger):
                # delta = self.get_delta()
                if not self.trigger:
                    asyncio.create_task(self.fetch_and_process_delta())
    
    async def fetch_and_process_delta(self):
        try:
            self.trigger = 1
            delta = await self.get_delta()
            await self.auto_trading(delta)
            self.trigger = 0
            print(f'--------------------')
            print(f"Delta value: {delta}")
            print(f'--------------------')
        except Exception as e:
            self.trigger = 0
            print(f"Error fetching delta: {e}")

    async def auto_trading(self, delta):
        # Determine action based on current position
        if self.position == 0:
            await self.open_position(delta)
        elif (self.position > 0 and delta <= 0) or (self.position < 0 and delta > 0):
            await self.switch_position(delta)

    async def open_position(self, delta):
        """Open a new position based on delta."""
        side = 'buy' if delta > 0 else 'sell'
        direction = 'LONG' if delta > 0 else 'SHORT'
        self.position = 1 if delta > 0 else -1
        self.direction = direction
        price = await self.blofin_apis.get_delta(self.maincoin, self.position)
        print(f"{'Buy Long' if delta > 0 else 'Sell Short'}")

        position_data = self.create_order_data(self.maincoin, direction.lower(), side, price)
        await self.blofin_apis.place_order(position_data)

    async def switch_position(self, delta):
        """Switch position from long to short or vice versa."""
        closing_side = 'short' if self.position > 0 else 'long'
        closing_data = self.create_closing_data(closing_side)
        self.position = 0

        await self.blofin_apis.close_position(closing_data)

        # Switch direction after closing position
        await self.open_position(delta)

    def create_order_data(self, instId, positionSide, side, price):
        """Helper function to create order data JSON."""
        return json.dumps({
            "instId": instId,
            "marginMode": "isolated",
            "positionSide": positionSide,
            "side": side,
            "price": price,
            "size": "2",
            "orderType": "limit"
        })

    def create_closing_data(self, positionSide):
        """Helper function to create closing position data JSON."""
        return json.dumps({
            "instId": "BTC-USDT",
            "marginMode": "isolated",
            "positionSide": positionSide
        })
    
    def execute(self):
        self.get_trend(self.binancecoin)
        self.get_updown()
        # self.get_delta()
        # self.blofin_apis.get_position()
        # position_data = json.dumps({
        #             "positionMode":"long_short_mode",
        #         })
        # self.blofin_apis.set_position(position_data)
        
        # position_data = json.dumps({
        #             "instId": "BTC-USDT",
        #             "marginMode":"isolated",
        #             "positionSide":"short",
        #             "side":"sell",
        #             "price":"120000",
        #             "size":"2",
        #             "orderType": "limit"
        #         })
        # self.blofin_apis.place_order(position_data)

        # position_data = json.dumps({
        #             "instId": "BTC-USDT",
        #             "marginMode":"isolated",
                #     "positionSide":"short",
                # })
        # self.blofin_apis.close_position(position_data)
        asyncio.run(self.websocket_config(self.maincoin))
        # self.get_delta()
        
    
blofin_bot = BlofinBot()
blofin_bot.execute()
# print(percent)

    
# print(f'live price: {live_price}')