import os
import pandas as pd
import time
import csv
from dotenv import load_dotenv
from pathlib import Path
from .settings import COLUMNS

class LineBreak:
    def __init__(self, lines, first, normal, conf, open_conf, close_conf, high_conf, low_conf, symbol, num_limit):
        self.num_lines = lines
        self.first_interval = first
        self.normal_interval = normal
        self.conf = conf
        self.open_conf = open_conf
        self.close_conf = close_conf
        self.high_conf = high_conf
        self.low_conf = low_conf
        self.symbol = symbol.replace("/", '')
        self.csv_file  = f"ohlcv_{self.symbol}_data.csv"
        self.candlestick_data = []
        self.linebreak_data = []
        self.selling_track = []
        self.num_limit = num_limit
    
    def conf_csv_file(self, df):
        open_conf = float(self.open_conf) / 100
        close_conf = float(self.close_conf) / 100
        high_conf = float(self.high_conf) / 100
        low_conf = float(self.low_conf) / 100
        height_o = df['open'] - df['close']
        open_conf  = df['open'] - height_o * open_conf
        close_conf =  df['close'] + height_o * close_conf
        df['open'] = round(open_conf, 2)
        df['close'] = round(close_conf, 2)

        height_h = df['high'] - df['low']
        high_conf  = df['high'] + height_h * high_conf
        low_conf = df['low'] - height_h * low_conf
        df['high'] = round(high_conf, 2)
        df['low'] = round(low_conf, 2)
        print(f'--Candle Stick Data Configured--')
        return df
    
    def get_directory(self, path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        return os.path.join(parent_dir, "data", self.symbol, path)
    
    def read_csv_file(self, path):
        input_data = self.get_directory(path)
        return pd.read_csv(input_data)
    
    def calculate_candlestick(self, df, first, interval):
        length       = len(df)
        date         = df.iloc[first]['date']
        open_value   = df.iloc[first]['open']
        if first + interval >= length: 
            close_value  = df.iloc[length-1]['close']
        else : close_value  = df.iloc[first + interval -1]['close']
        high_value   = df.iloc[first]['high']
        low_value    = df.iloc[first]['low']
        volume       = df.iloc[first]['volume']

        for i in range(interval):
            if first + i >= length: break
            if high_value < df.iloc[first + i]['high']:
                high_value = df.iloc[first + i]['high']
            if low_value > df.iloc[first + i]['low']:
                low_value = df.iloc[first + i]['low']
        print(f'--Candle Stick date: {date} is calculated--')
        self.candlestick_data.append({
            'date'  : date,
            'open'  : open_value,
            'high'  : high_value,
            'low'   : low_value,
            'close' : close_value,
            'volume': volume,
        })

    def update_candle(self, path):
        exist_data = pd.read_csv(path)
        base_data = self.read_csv_file(self.csv_file)
        last_date = exist_data.iloc[-1]['date']
        last_num = 0
        print(f'--Existing Last Date of Candlestick is: {last_date}--')
        with open(self.get_directory(self.csv_file), 'r') as file:
            reader = csv.DictReader(file)
            for index, row in enumerate(reader):
                if row['date'].startswith(last_date):
                    last_num = index
                    break
        print(f'--Last Data starts on this: {last_num} in Origin--')
        length = len(base_data)
        for index in range(last_num + self.normal_interval, length, self.normal_interval):
            self.calculate_candlestick(base_data, index, self.normal_interval)

    def get_candlestick_with_interval(self):
        conf_path = self.get_directory(f'conf_{self.first_interval}_{self.normal_interval}_candlestick_{self.csv_file}')
        nor_path = self.get_directory(f'{self.first_interval}_{self.normal_interval}_candlestick_{self.csv_file}')
        exist = 0
        if self.conf and os.path.exists(conf_path):
            print("----Status: Current status is conf----------")
            print("----Already the Candle Stick File exists, Updating now----------")
            self.update_candle(conf_path)
            exist = 1
        elif not self.conf and os.path.exists(nor_path):
            print("----Status: Current status is normal----------")
            print("----Already the Candle Stick File exists, Updating now----------")
            self.update_candle(nor_path)
            exist = 1
        else:
            print("----Status: Starting Candlestick calculation----------")
            df = self.read_csv_file(self.csv_file)
            self.calculate_candlestick(df, 0, self.first_interval)
            for index in range(self.first_interval, len(df), self.normal_interval):
                self.calculate_candlestick(df, index, self.normal_interval)
        
        candlestick_df = pd.DataFrame(self.candlestick_data, columns = COLUMNS)
        if self.conf : 
            conf_candle_df = self.conf_csv_file(candlestick_df)
            conf_candle_df.to_csv(f'source/data/{self.symbol}/conf_{self.first_interval}_{self.normal_interval}_candlestick_{self.csv_file}', mode='a', header=(exist == 0), index=False)
        else : 
            candlestick_df.to_csv(f'source/data/{self.symbol}/{self.first_interval}_{self.normal_interval}_candlestick_{self.csv_file}', mode='a', header=(exist == 0), index=False)
        time.sleep(10)

    def calculate_linebreak(self, df, index):
        date = df.iloc[index]['date']
        open_value = df.iloc[index]['open']
        high_value = df.iloc[index]['high']
        low_value = df.iloc[index]['low']
        close_value = df.iloc[index]['close']
        volume = df.iloc[index]['volume']

        if close_value > open_value: direction = 1
        else: direction = -1
        former_direction = 0
        if not self.linebreak_data:
            open_value = df.iloc[index]['open']
        else: 
            if self.linebreak_data[-1]['close'] > self.linebreak_data[-1]['open']: 
                former_direction = 1
            else : 
                former_direction = -1
            open_value = self.linebreak_data[-1]['close']
            high = max(max([line['high'] for line in self.linebreak_data[-self.num_lines:]]), max([line['open'] for line in self.linebreak_data[-self.num_lines:]]))
            low  = min(min([line['low'] for line in self.linebreak_data[-self.num_lines:]]), min([line['open'] for line in self.linebreak_data[-self.num_lines:]]))
            if direction * former_direction == 1:
                if direction == 1 and close_value < self.linebreak_data[-1]['high']: direction = 0
                if direction == -1 and close_value > self.linebreak_data[-1]['low']: direction = 0
            else:
                if direction == 1 and (close_value < high): direction = 0
                elif direction == -1 and (close_value > low): direction = 0
                else: open_value = self.linebreak_data[-1]['open']

        if direction != 0:
            print(f'--Linebreak Data: {date} is calculated--')
            self.linebreak_data.append({
                'date'  : date,
                'open'  : open_value,
                'high'  : high_value,
                'low'   : low_value,
                'close' : close_value,
                'volume': volume,
            })
            if direction * former_direction == -1:
                self.selling_track.append({
                    "date"      : date,
                    "price"     : open_value,
                    "direction" : direction,
                })

    def update_linebreak(self, path, base_path):
        exist_data = pd.read_csv(path)
        base_data = self.read_csv_file(base_path)
        last_date = exist_data.iloc[-1]['date']
        last_num = 0
        print(f'--Existing Last Date of Linebreak is: {last_date}--')
        with open(self.get_directory(base_path), 'r') as file:
            reader = csv.DictReader(file)
            for index, row in enumerate(reader):
                if row['date'].startswith(last_date):
                    last_num = index
                    break
        print(f'--Last Data starts on this: {last_num} in Origin--')
        filtered_df = base_data[base_data.index > last_num]
        if self.num_lines > len(exist_data):
            self.num_lines = len(exist_data)
        self.linebreak_data = exist_data[-self.num_lines:].to_dict(orient='records')
        return filtered_df

    def get_linebreak_with_interval(self):
        print(f'----Calculating Linebreak Starts Newly----')
        if self.conf : 
            base_path = f'conf_{self.first_interval}_{self.normal_interval}_candlestick_{self.csv_file}'
            df_base = self.read_csv_file(base_path)
        else : 
            base_path = f'{self.first_interval}_{self.normal_interval}_candlestick_{self.csv_file}'
            df_base = self.read_csv_file(base_path)
        
        conf_path = self.get_directory(f'conf_{self.first_interval}_{self.normal_interval}_{self.num_lines}_linebreak_{self.csv_file}')
        nor_path = self.get_directory(f'{self.first_interval}_{self.normal_interval}_{self.num_lines}_linebreak_{self.csv_file}')

        exist = 0
        if self.conf and os.path.exists(conf_path):
            print("----Status: Current status is conf----------")
            print("----Already the File exists, Updating now----------")
            df = self.update_linebreak(conf_path, base_path)
            exist = 1
        elif not self.conf and os.path.exists(nor_path):
            print("----Status: Current status is normal----------")
            print("----Already the File exists, Updating now----------")
            df = self.update_linebreak(nor_path, base_path)
            exist = 1
        else:
            print("----Start Newly----------")
            df = df_base
            exist = 0
        for index in range(len(df)):
            self.calculate_linebreak(df, index)
        
        linebreak_df = pd.DataFrame(self.linebreak_data, columns=COLUMNS)
        if exist: 
            print(f'--Some Lines are dropped: {linebreak_df.iloc[self.num_lines-1]}--')
            linebreak_df = linebreak_df.iloc[self.num_lines:]
        if self.conf : linebreak_df.to_csv(f'source/data/{self.symbol}/conf_{self.first_interval}_{self.normal_interval}_{self.num_lines}_linebreak_{self.csv_file}', mode='a', header=(exist == 0), index=False)
        else: linebreak_df.to_csv(f'source/data/{self.symbol}/{self.first_interval}_{self.normal_interval}_{self.num_lines}_linebreak_{self.csv_file}', mode='a', header=(exist == 0), index=False)
        trading_track_df = pd.DataFrame(self.selling_track)
        trading_track_df.to_csv(f'source/data/trading_track.csv')
