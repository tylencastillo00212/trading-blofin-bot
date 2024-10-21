import os
import pandas as pd
import time
import csv
from dotenv import load_dotenv
from pathlib import Path
from .blofin_apis import BlofinApis

class LineBreak:
    def __init__(self, lines, interval, symbol):
        self.num_lines = lines
        self.interval = interval
        self.symbol = symbol
        self.candlestick_data = []
        self.linebreak_data = []
        
        base_path = Path(__file__).resolve().parent.parent
        env_path = base_path / '.env'
        data_path = base_path / 'data'
        self.source_path = data_path / 'candlestick' / f"{symbol}.csv"
        self.custom_path = data_path / 'customstick' / f"{self.interval}m-{symbol}.csv"
        self.export_path = data_path / 'linebreak' / f"{self.interval}m-{self.num_lines}linebreak-{symbol}.csv"
        load_dotenv(env_path)
        conf = os.getenv("LINEBREAK_CONF")
        self.conf = float(conf) / 100
        columns_str = os.getenv("COLUMNS")
        self.columns = columns_str.split(",") if columns_str else []
    
    def conf_csv_file(self, df):
        conf = self.conf
        height_o = df['open'] - df['close']
        open_conf  = df['open'] - height_o * conf
        close_conf =  df['close'] + height_o * conf
        df['open'] = round(open_conf, 2)
        df['close'] = round(close_conf, 2)

        height_h = df['high'] - df['low']
        high_conf  = df['high'] + height_h * conf
        low_conf = df['low'] - height_h * conf
        df['high'] = round(high_conf, 2)
        df['low'] = round(low_conf, 2)
        print(f'--Candle Stick Data Configured--')
        return df
    
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
        base_data = pd.read_csv(self.source_path)
        last_date = exist_data.iloc[-1]['date']
        last_num = 0
        print(f'--Existing Last Date of Candlestick is: {last_date}--')
        with open(self.source_path, 'r') as file:
            reader = csv.DictReader(file)
            for index, row in enumerate(reader):
                if row['date'].startswith(last_date):
                    last_num = index
                    break
        print(f'--Last Data starts on this: {last_num} in Origin--')
        length = len(base_data)
        for index in range(last_num + self.interval, length, self.interval):
            self.calculate_candlestick(base_data, index, self.interval)

    def get_candlestick_with_interval(self):
        exist = 0
        if self.custom_path.exists():
            print("----Status: Current status is normal----------")
            print("----Already the Candle Stick File exists, Updating now----------")
            self.update_candle(self.custom_path)
            exist = 1
        else:
            print("----Status: Starting Candlestick calculation----------")
            df = pd.read_csv(self.source_path)
            self.calculate_candlestick(df, 0, self.interval)
            for index in range(self.interval, len(df), self.interval):
                self.calculate_candlestick(df, index, self.interval)
        
        candlestick_df = pd.DataFrame(self.candlestick_data, columns = self.columns)
        candlestick_df.to_csv(self.custom_path, mode='a', header=(exist == 0), index=False)
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

    def update_linebreak(self, path, base_path):
        exist_data = pd.read_csv(path)
        base_data = pd.read_csv(base_path)
        last_date = exist_data.iloc[-1]['date']
        last_num = 0
        print(f'--Existing Last Date of Linebreak is: {last_date}--')
        with open(self.custom_path, 'r') as file:
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
        
        exist = 0
        if self.export_path.exists():
            print("----Status: Current status is normal----------")
            print("----Already the File exists, Updating now----------")
            df = self.update_linebreak(self.export_path, self.custom_path)
            exist = 1
        else:
            print("----Start Newly----------")
            df = pd.read_csv(self.custom_path)
            exist = 0
        for index in range(len(df)):
            self.calculate_linebreak(df, index)
        
        linebreak_df = pd.DataFrame(self.linebreak_data, columns=self.columns)
        if exist: 
            print(f'--Some Lines are dropped: {linebreak_df.iloc[self.num_lines-1]}--')
            linebreak_df = linebreak_df.iloc[self.num_lines:]
        linebreak_df.to_csv(self.export_path, mode='a', header=(exist == 0), index=False)
        print(f'--Successfully calculated the {self.interval}m {self.num_lines} linebreak data--')