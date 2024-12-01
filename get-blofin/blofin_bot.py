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
        self.num_threads = int(num_threads)
        self.percent = 0
        self.positive_trend = 0.0
        self.trend = []
        self.coins_list_path = self.data_path / 'coins.csv'
        self.blofin_apis = BlofinApis()

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
        trend = get_trend.get_trend()
        print('----------------------------------------------------')
        print(f'-----------End Calculation of {currency}------------')
        print('----------------------------------------------------')
        return trend

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
    
    def blofin_websoket(self):
        
        url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    
blofin_bot = BlofinBot()
percent = blofin_bot.get_trend('BTC/USDT')

percent = blofin_bot.get_delta()
print(percent)