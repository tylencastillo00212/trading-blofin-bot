import os
import pandas as pd
from time import sleep
import sys
from .charts.chart import Chart
from .get-blofin.liveData import LiveData
from .get-blofin.lineBreak import LineBreak
from .get-blofin import settings
from .mexc.mexc_spot_v3 import mexc_trade
from .get-blofin.horLines import HorizontalLines

LINEBREAK = settings.LINEBREAK
CANDLESTICK = settings.CANDLESTICK
COLUMNS = settings.COLUMNS
configure = False
currentmode = LINEBREAK
currency = settings.SYMBOL
num_lines = settings.NUM_OF_LINES_TO_BREAK
time_interval = settings.NORMAL_INTERVAL
open_conf = settings.OPEN_CONF
close_conf = settings.OPEN_CONF
high_conf = settings.HIGH_CONF
low_conf = settings.LOW_CONF
timeframe = settings.TIMEFRAME
num_limit = settings.SHOW_LIMIT

def get_settings():
    settings_file = f'settings.xlsx'
    directory = os.path.dirname(os.path.abspath(__file__))
    directory = os.path.dirname(directory)
    path = os.path.join(directory, settings_file)
    setval = pd.read_excel(path)
    values = setval['Value'].tolist()
    return values

def store_data():
    live_data = LiveData(settings.START_TIME, currency, settings.TIMEZONE, timeframe)
    live_data.update_csv_realtime()

def cal_linebreak():
    store_data()
    linebreak_data = LineBreak(num_lines, time_interval, time_interval, configure, open_conf, close_conf, high_conf, low_conf, currency, num_limit)
    linebreak_data.get_candlestick_with_interval()
    linebreak_data.get_linebreak_with_interval()
    return

def get_bar_data(chart):
    if currency not in list(coins):
        print(f'No currency type for "{currency}"')
        df = pd.DataFrame()
    else:
        print(f"-------Settings of this Chart-------")
        print(f"-Current Mode       : {currentmode}")
        print(f"-Number_of_lines    : {num_lines}")
        print(f'-Time Interval      : {time_interval}')
        print(f'-Configure          : {configure}')
        print(f'-Open Conf Value    : {open_conf}')
        print(f'-Close Conf Value   : {close_conf}')
        print(f'-High Conf Value    : {high_conf}')
        print(f'-Low Conf Value     : {low_conf}')
        print(f'-Currency           : {currency}')
        print(f'-Limit num of bars  : {num_limit}')
        print(f'-Time Zone          : {settings.TIMEZONE}')
        print(f'------------------------------------')
        cal_linebreak()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        currency_dir = currency.replace("/", "")
        mode = currentmode
        conf = configure
        interval = time_interval
        if mode == settings.LINEBREAK: 
            chart.candle_style('rgba(39, 157, 130, 100)', 'rgba(200, 97, 100, 100)', False, False, '', '', '', '')
            if conf: csv_file = os.path.join(parent_dir,'source', 'data', currency_dir, f'conf_{interval}_{interval}_{num_lines}_{mode}_ohlcv_{currency_dir}_data.csv')
            else : csv_file = os.path.join(parent_dir,'source', 'data', currency_dir, f'{interval}_{interval}_{num_lines}_{mode}_ohlcv_{currency_dir}_data.csv')
        else :
            chart.candle_style('rgba(39, 157, 130, 100)', 'rgba(200, 97, 100, 100)', True, True, '', '', '', '')
            if conf: csv_file = os.path.join(parent_dir,'source', 'data', currency_dir, f'conf_{interval}_{interval}_{mode}_ohlcv_{currency_dir}_data.csv')
            else : csv_file = os.path.join(parent_dir,'source', 'data', currency_dir, f'{interval}_{interval}_{mode}_ohlcv_{currency_dir}_data.csv')
    try:
        print(csv_file)
        df = pd.read_csv(csv_file)
        # sys.exit()
        df = pd.DataFrame(df[-num_limit:].reset_index(drop=True), columns=COLUMNS)
        print('The csv data will be shown on the chart')
        print(df)
        if df.empty:
            print("DataFrame is empty")
            return None
    except Exception as e:
        print(f"Failed to read the CSV file: {e}")
        return None

    try:
        chart.set(df)
    except Exception as e:
        print(f"Failed to set data in chart: {e}")

    return df

def on_search(chart, searched_string):  # Called when the user searches.
    if searched_string not in list(coins):
        print(f'No Currency Type for {searched_string}')
        return
    chart.topbar['coin'].set(searched_string)
    global currency
    currency = searched_string
    get_bar_data(chart)
    
def configure_chart(chart):  # Called when the user changes the timeframe.
    global configure
    if chart.topbar['configure'].value == 'Origin': configure = False
    else : configure = True
    print(currentmode)
    get_bar_data(chart)
    
def showmode(chart):  # Called when the user changes the timeframe.
    global currentmode
    if chart.topbar['showmode'].value == "Linebreak": currentmode = LINEBREAK
    else : currentmode = CANDLESTICK
    print(currentmode)
    get_bar_data(chart)
    
def set_line_num(chart):
    global num_lines
    num_lines = int(chart.topbar['line_number'].value)
    get_bar_data(chart)
    
def on_horizontal_line_move(chart, line):
    print(f'Horizontal line moved to: {line.price}')

def auto_buy(chart):
    trade = mexc_trade(mexc_key=settings.MEXC_KEY, mexc_secret=settings.MEXC_SECRET, mexc_hosts=settings.HOSTS)
    params = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "quantity": 0.005,
        "price": "10000"
    }
    trade.get_order(params)

def auto_sell(chart):
    trade = mexc_trade(mexc_key=settings.MEXC_KEY, mexc_secret=settings.MEXC_SECRET, mexc_hosts=settings.HOSTS)
    params = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "quantity": 0.005,
        "price": "10000"
    }
    trade.post_order(params)

def get_coins():
    global coins
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "data", 'coins.csv')
    coins = pd.read_csv(path)
    coins = list(coins['Coin'])

def init():
    global answer, time_interval, currency, open_conf, close_conf, high_conf, low_conf, configure, currentmode, num_lines, timeframe, num_limit

    print(f"Do you want configure settings manually? Or we will use the existing value in settings.xlsx. Please type 'y' or 'n'")
    answer = input("Please enter your answer: ")
    if answer == 'y':
        while True:
            currency    = input("Please enter the currency type: ")
            if currency in coins:
                break
            else: print(f'Please type correct value')
        time_interval   = int(input("Please enter the time interval(min): "))
        open_conf       = int(input("Please enter the configure value of open value: "))
        close_conf      = int(input("Please enter the configure value of close value: "))
        high_conf       = int(input("Please enter the configure value of high value: "))
        low_conf        = int(input("Please enter the configure value of low value: "))
        return
    else :
        setval = get_settings()
        print(f'Existing setting value: {setval}')
        time_interval   = int(setval[1])
        num_lines       = int(setval[0])
        configure       = setval[2]
        open_conf       = int(setval[3])
        close_conf      = int(setval[4])
        high_conf       = int(setval[5])
        low_conf        = int(setval[6])
        num_limit       = int(setval[7])
        timeframe       = setval[8]
        while True:
            currency    = setval[9]
            if currency in coins:
                break
            else: print("Please recheck settings.xlsx and type currency correctly. You can get a coin type from 'coins.csv' file.")
        return
    
def draw_lines(chart, lines):
    for i in lines:
        chart.horizontal_line(i, func=on_horizontal_line_move)


def main():
    get_coins()
    init()
    chart = Chart(toolbox=True)

    chart.legend(True)

    chart.events.search += on_search

    chart.topbar.textbox("coin", currency)
    chart.topbar.switcher('configure', ('Origin', 'Adjust'), default='Origin',
                            func=configure_chart)
    if currentmode == LINEBREAK:
        chart.topbar.switcher('showmode', ('Candle Stick', 'Linebreak'), default='Linebreak', func=showmode)
    else: 
        chart.topbar.switcher('showmode', ('Candle Stick', 'Linebreak'), default='Candle Stick', func=showmode)
    chart.topbar.menu('line_number', (1, 2, 3, 4, 5, 6), default=1,
                            func=set_line_num)
    
    chart.topbar.button('buy', 'Buy', separator=True, func=auto_buy)
    

    get_bar_data(chart)
    
    horLines = HorizontalLines(num_lines, time_interval, currency, open_conf, close_conf, high_conf, low_conf)
    Lines = horLines.get()
    horLines.export_data()
    print(Lines)
    # draw_lines(chart, Lines)
    
    sleep(60)

    

    chart.show(block=True)

    while True:
        get_bar_data(chart)
        sleep(60)

if __name__ == '__main__':
    main()
