from .live_data import LiveData
from .gen_linebreak import LineBreak
from .trend import GetTrend

live_data = LiveData('BTC-USDT')
live_data.update_csv_realtime()
linebreak = LineBreak(9, 1, 'BTC-USDT')
linebreak.get_candlestick_with_interval()
linebreak.get_linebreak_with_interval()
get_trend = GetTrend(9, 1, 'BTC-USDT')
lines = get_trend.export_data()
trend = get_trend.get_trend()
print(trend)