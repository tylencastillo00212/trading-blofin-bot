import os
import ccxt
import pandas as pd
import csv
import pytz
import time
from datetime import datetime
from itertools import cycle
from dotenv import load_dotenv
from pathlib import Path
from .settings import DATETIME_FORMAT, COLUMNS, HOSTS

class LiveData:

    def __init__(self, start, symbol, timezone, timeframe):
        
        self.symbol = symbol.replace('/', '')
        self.timezone = timezone
        self.timeframe = timeframe
        self.datetime = DATETIME_FORMAT
        self.mexc_host = HOSTS
        self.exchange = ccxt.binance({'enableRateLimit' : True})
        self.start = self.exchange.parse8601(start)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        self.csv_file = os.path.join(parent_dir, "source", "data", self.symbol, f"ohlcv_{self.symbol}_data.csv")

    def create_csv_file(self):
        with open(self.csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(COLUMNS)

    def read_csv_data(self):
        return pd.read_csv(self.csv_file)
    
    def fetch_new_data(self, since):
        limit = 1000
        start = since
        while True:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, start, limit)
            if len(ohlcv) == 0:
                break
            self.fit_to_style(ohlcv)
            time.sleep(self.exchange.rateLimit / 1000)
            start = ohlcv[-1][0] + 1
        # Avoid hitting rate limit
        print("Original Data Was Updated")
        return since
    
    def read_last_date_from_csv(self):
        df = self.read_csv_data()
        lasttime_str = df.iloc[-1]['date']
        lasttime = datetime.strptime(lasttime_str, self.datetime)
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
            realtime = datetime.strptime(realtime, self.datetime)
            timezone = pytz.utc
            if not realtime.tzinfo:
                realtime = timezone.localize(realtime)
            timezone = pytz.timezone(self.timezone)
            realtime = realtime.astimezone(timezone)
        return realtime.strftime('%Y-%m-%d %H:%M:%S')
    
    def fit_to_style(self, data):
        print(f"--Timestamp: {data[-1][0]}--")
        new_df = pd.DataFrame(data, columns=COLUMNS)
        new_df['date'] = pd.to_datetime(new_df['date'], unit='ms')
        new_df['date'] = new_df['date'].apply(self.convert_timestamp_to_realtime)
        new_df.to_csv(self.csv_file, mode='a', header=False, index=False)
        
    def latest_data(self):
        latest_data = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=1)
        if latest_data:
            latest_df = pd.DataFrame(latest_data, columns=COLUMNS)
            latest_df['date'] = pd.to_datetime(latest_df['date'], unit='ms')
            latest_df['date'] = latest_df['date'].apply(self.convert_timestamp_to_realtime)
        return latest_df 

    def get_latest_data(self):
        latest_df = self.latest_data
        df = pd.read_csv(self.csv_file)
        lasttime_str = df.iloc[-1]['date']
        print(lasttime_str)
        if(latest_df['date'] != lasttime_str).any():
            latest_df.to_csv(self.csv_file, mode='a', header=False, index=False)
            print(f"Added latest data for {latest_df['date'].iloc[0]}")
        # self.spinner.init()
        time.sleep(30) 
        return latest_df

    def update_csv_realtime(self):
        self.csv_file = os.path.join(f"source/data/{self.symbol}", f"ohlcv_{self.symbol}_data.csv")
        last_timestamp_ms = self.start
        if not os.path.exists(self.csv_file):
            os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
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
       
