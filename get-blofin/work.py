from .live_data import LiveData

live_data = LiveData('BTC-USDT')
live_data.update_csv_realtime()