from .live_data import LiveData
from .gen_linebreak import LineBreak

live_data = LiveData('BTC-USDT')
live_data.update_csv_realtime()
linebreak = LineBreak(1, 100, 'BTC-USDT')
linebreak.get_candlestick_with_interval()
linebreak.get_linebreak_with_interval()