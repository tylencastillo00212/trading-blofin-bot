import os
import pandas as pd
import csv
import pytz
import time
from datetime import datetime
from itertools import cycle
from dotenv import load_dotenv
from pathlib import Path
from .blofin_apis import BlofinApis

class LiveData:
    def __init__(self, symbol):
        self.blofin_api = BlofinApis()
        base_path = Path(__file__).resolve().parent.parent
        self.env_path = base_path / '.env'
        load_dotenv(self.env_path)
        self.timeformat = os.getenv('DATETIME_FORMAT')
        columns_str = os.getenv("COLUMNS")
        self.columns = columns_str.split(",") if columns_str else []
        self.timezone = os.getenv("TIMEZONE")
        self.timeframe = os.getenv("TIMEFRAME")
        self.num_limit = os.getenv("NUM_LIMIT")
        rate_limit = os.getenv("BLOFIN_API_RATE_LIMIT")
        self.rate_limit = float(rate_limit)
        start_time = os.getenv("START_TIME")
        timestamp = datetime.strptime(start_time, self.timeformat)
        self.start = int(timestamp.timestamp() * 1000)
        self.data_path = base_path / 'data'
        self.symbol = symbol
        self.csv_file = self.data_path / 'candlestick' / f"{self.symbol}.csv"
        self.current_timestamp = datetime.now().timestamp() * 1000
        print(f'Current Timestamp: {self.current_timestamp}')
        self.timerange = self.rate_limit * 60 * 1000
        
    def create_csv_file(self):
        with open(self.csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.columns)

    def read_csv_data(self):
        return pd.read_csv(self.csv_file)
    
    def fetch_new_data(self, since):
        start = since
        while True:
            ohlcv = self.blofin_api.get_coins_data(self.symbol, bar=self.timeframe, after=start)
            if len(ohlcv) == 0:
                start += self.timerange
                break
            if start + self.timerange > self.current_timestamp:
                print('--Reached the latest data--')
                break
            else:
                self.fit_to_style(ohlcv)
                # time.sleep(60 / self.rate_limit)
                start = int(ohlcv[-1][0]) + 1
        # Avoid hitting rate limit
        print("Original Data Was Updated")
        return since
    
    def read_last_date_from_csv(self):
        df = self.read_csv_data()
        lasttime_str = df.iloc[-1]['date']
        lasttime = datetime.strptime(lasttime_str, self.timeformat)
        timezone = pytz.timezone(self.timezone)

        if not lasttime.tzinfo:
            lasttime = timezone.localize(lasttime)
        
        lasttime = lasttime.astimezone(pytz.utc)
        last_timestamp = pd.to_datetime(lasttime)
        # Convert to milliseconds since unix epoch for ccxt
        last_timestamp_ms = int(last_timestamp.timestamp()) * 1000
        return last_timestamp_ms

    def convert_timestamp_to_realtime(self, realtime):
        if isinstance(realtime, pd.Timestamp):
            timezone = pytz.utc
            realtime = timezone.localize(realtime)
            realtime = realtime.tz_convert(self.timezone)
        else:
            realtime = datetime.strptime(realtime, self.timeformat)
            timezone = pytz.utc
            if not realtime.tzinfo:
                realtime = timezone.localize(realtime)
            timezone = pytz.timezone(self.timezone)
            realtime = realtime.astimezone(timezone)
        return realtime.strftime(self.timeformat)
    
    def fit_to_style(self, data):
        print(f"--Timestamp: {data[-1][0]}--")
        new_df = pd.DataFrame(data, columns=self.columns)
        if not pd.api.types.is_numeric_dtype(new_df['date']):
            new_df['date'] = pd.to_numeric(new_df['date'], errors='coerce')
        new_df['date'] = pd.to_datetime(new_df['date'], unit='ms')
        new_df['date'] = new_df['date'].apply(self.convert_timestamp_to_realtime)
        new_df.to_csv(self.csv_file, mode='a', header=False, index=False)
        
    def latest_data(self):
        latest_data = self.blofin_api.get_coins_data(self.symbol, bar=self.timeframe, limit=1)
        if latest_data:
            latest_df = pd.DataFrame(latest_data, columns=self.columns)
            latest_df['date'] = pd.to_datetime(latest_df['date'], unit='ms')
            latest_df['date'] = latest_df['date'].apply(self.convert_timestamp_to_realtime)
        return latest_df 

    def get_latest_data(self):
        latest_df = self.latest_data
        df = pd.read_csv(self.csv_file)
        lasttime_str = df.iloc[-1]['date']
        print(lasttime_str)
        if (latest_df['date'].apply(str) != str(lasttime_str)).any():
            latest_df.to_csv(self.csv_file, mode='a', header=False, index=False)
            print(f"Added latest data for {latest_df['date'].iloc[0]}")
        # self.spinner.init()
        time.sleep(30) 
        return latest_df

    def update_csv_realtime(self):
        last_timestamp_ms = self.start
        if not self.csv_file.exists():
            self.csv_file.parent.mkdir(parents=True, exist_ok=True)
            self.create_csv_file()
            print(f'--Updating on this Timestamp: {last_timestamp_ms}--')
        else: 
            last_timestamp_ms = self.read_last_date_from_csv()
            print(f'--Updating on this Timestamp: {last_timestamp_ms}--')
        try:
            self.fetch_new_data(last_timestamp_ms+1)
            # if new_data:
                # self.fit_to_style(new_data)
                # time.sleep(30)
        except Exception as e:
            print(f"An error occurred: {e}")
       
