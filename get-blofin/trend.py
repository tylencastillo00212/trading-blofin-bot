import os
import csv
import ccxt
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import math

class GetTrend:
    def __init__(self, time_interval, linebreak_num, currency):
        self.currency = currency.replace('/', '')
        base_path = Path(__file__).resolve().parent.parent
        env_path = base_path / '.env'
        load_dotenv(env_path)
        data_path = base_path / 'data' / 'linebreak' / f'{time_interval}m-{linebreak_num}linebreak-{self.currency}.csv'
        self.export_path = base_path / 'data' / 'horlines' / f'lines-{time_interval}m-{linebreak_num}linebreak-{self.currency}.csv'
        self.binance = ccxt.binance()
        last_high_value = df['high'].iloc[-1]
        precision = -int(math.floor(math.log10(abs(last_high_value))) + 1)
        self.round = precision + 5
    

        df = pd.read_csv(data_path)
        self.df = df
        self.conf_val  =  os.getenv('LINEBREAK_CONF')
        self.lines = []
        self.distint_lines = []
        self.counts = []

    def conf(self):
        conf_val = float(self.conf_val) / 100
        height_o = self.df['open'] - self.df['close']
        open_conf  = self.df['open'] - height_o * conf_val
        close_conf =  self.df['close'] + height_o * conf_val
        self.df['open'] = round(open_conf, self.round)
        self.df['close'] = round(close_conf, self.round)

        height_h = self.df['high'] - self.df['low']
        high_conf  = self.df['high'] + height_h * conf_val
        low_conf = self.df['low'] - height_h * conf_val
        self.df['high'] = round(high_conf, self.round)
        self.df['low'] = round(low_conf, self.round)
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
            count = line_data.count(i)
            print(f'the value is {i} the count is {count}')
            counts.append(count)
        self.counts = counts
        return counts
    
    def export_data(self):
        self.get()
        self.distint()
        self.count_distint()

        with open(self.export_path, 'w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(['value', 'numbers'])

            for value, number in zip(self.distint_lines, self.counts):
                writer.writerow([value, number])
                
    def get_trend(self):
        ticker = self.binance.fetch_ticker(self.currency)
        price = ticker['last']
        lower_index = None
        higher_index = None

        # Find closest indices
        for i, value in enumerate(self.distint_lines):
            if value < price:
                lower_index = i
            elif value > price and not higher_index:
                higher_index = i
                break  # Break as soon as we find the first greater value

        closest_values = []
    
        # Get the closest smaller value and its predecessor (if it exists)
        if lower_index is not None:
            closest_values.append(self.distint_lines[lower_index])
            if lower_index > 0:
                closest_values.insert(0, self.distint_lines[lower_index - 1])  # Predecessor
        
        # Get the closest greater value and its successor (if it exists)
        if higher_index is not None:
            closest_values.append(self.distint_lines[higher_index])
            if higher_index < len(self.distint_lines) - 1:
                closest_values.append(self.distint_lines[higher_index + 1])  # Successor
        
        # Check if any of these values have a count greater than 1
        for value in closest_values:
            index = self.distint_lines.index(value)
            if self.counts[index] > 1:
                return True

        return False