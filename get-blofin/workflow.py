import os
import threading
from .live_data import LiveData
from .gen_linebreak import LineBreak
from .trend import GetTrend
from .blofin_apis import BlofinApis
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

class WorkFlow:
    def __init__(self):
        base_path = Path(__file__).resolve().parent.parent
        env_path = base_path / '.env'
        self.data_path = base_path / 'data'
        load_dotenv(env_path)
        self.lines  =  os.getenv('LINEBREAK_NUM')
        self.interval  =  os.getenv('TIME_INTERVAL')
        num_threads = os.getenv('NUM_THREADS')
        self.num_threads = int(num_threads)
        self.percent = 0
        self.positive_trend = 0.0
        
    
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
    
    def get_percent(self, *coins):
        for coin in coins:
            coin_trend = self.get_trend(coin)
            if coin_trend:
                self.positive_trend += 1
    
    # Create and start 10 threads
    def multi_thread(self):
        coins_list_path = self.data_path / 'coins.csv'
        df = pd.read_csv(coins_list_path, header=None)
        coins = df[0].values.tolist()
        num_coins = len(coins)
        chunk_size = round(num_coins / self.num_threads)
        threads = []
        for i in range(self.num_threads):
            coin_subset = coins[i * chunk_size:(i + 1) * chunk_size]
            print(coin_subset)
            thread = threading.Thread(target=self.get_percent, args=(coin_subset))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        percent = float(self.positive_trend / num_coins) * 100
        return percent
    
workflow = WorkFlow()
# percent = workflow.multi_thread()
trend = workflow.get_trend("BTC/USDT")
print(trend)