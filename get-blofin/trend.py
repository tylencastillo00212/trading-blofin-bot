import os
import csv
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from .blofin_apis import BlofinApis

class GetTrend:
    def __init__(self, time_interval, currency):
        env_path = Path('..') / '.env'
        load_dotenv(env_path)
        linebreak_num = os.getenv('LINEBREAK_NUM')
        time_interval = os.getenv('TIME_INTERVAL')
        data_path = Path('..') / 'data' / 'linebreak' / f'{time_interval}_{linebreak_num}_{currency}.csv'
        self.export_path = Path('..') / 'data' / 'trend' / f'{currency}.csv'
        
        df = pd.read_csv(data_path)
        self.df = df
        self.conf_val  =  os.getenv('LINEBREAK_CONF')
        self.lines = []
        self.distint_lines = []
        self.counts = []
        self.currency = currency
        self.blofin_api = BlofinApis()

    def conf(self):
        conf_val = float(self.conf_val) / 100
        height_o = self.df['open'] - self.df['close']
        open_conf  = self.df['open'] - height_o * conf_val
        close_conf =  self.df['close'] + height_o * conf_val
        self.df['open'] = round(open_conf, 0)
        self.df['close'] = round(close_conf, 0)

        height_h = self.df['high'] - self.df['low']
        high_conf  = self.df['high'] + height_h * conf_val
        low_conf = self.df['low'] - height_h * conf_val
        self.df['high'] = round(high_conf, 0)
        self.df['low'] = round(low_conf, 0)
        return self.df
    
    def get(self):
        df = self.conf()
        length = len(df)
        lines = []
        for i in range(length):
            lines.append(df.iloc[i]['open'])
            lines.append(df.iloc[i]['close'])
            lines.append(df.iloc[i]['high'])
            lines.append(df.iloc[i]['low'])
        self.lines = lines
        return lines
    
    def distint(self):
        distint_list = list(dict.fromkeys(self.lines))
        distint_list.sort()
        self.distint_lines = distint_list
        return distint_list
    
    def count_distint(self):
        line_data = self.lines
        distint_list = self.distint_lines
        counts = []
        for i in distint_list:
            print(f'the value is {i}')
            count = line_data.count(i)
            print(f'the count is {count}')
            counts.append(count)
        self.counts = counts
        return counts
    
    def export_data(self):
        self.get()
        self.distint()
        self.count_distint()

        with open('list.csv', 'w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(['value'])

            for value in self.lines:
                writer.writerow([value])

        with open(self.export_path, 'w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(['value', 'numbers'])

            for value, number in zip(self.distint_lines, self.counts):
                writer.writerow([value, number])
                
    def get_trend(self):
        price = self.blofin_api.get_tick_price(self.currency)
        