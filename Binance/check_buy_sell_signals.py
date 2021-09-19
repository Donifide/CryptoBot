import ccxt,schedule,warnings,time,ast,config
warnings.filterwarnings('ignore')
from dateutil.tz import tzlocal
from datetime import datetime
from random import randint
from random import seed
import pandas as pd
import numpy as np
ccxt.binanceus({ 'options':{ 'adjustForTimeDifference':True}})
exchange = ccxt.binanceus({
"apiKey": config.BINANCE_KEY,
"secret": config.BINANCE_SECRET,
'enableRateLimit': True})
def check_buy_sell_signals(df,in_position,order_size,ticker,timeframe,min_sell_price,markup):
    print("Analyzing",ticker,"data... \n")
    print(df.tail(3)[['timestamp','close','volume','in_uptrend']])
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1 
    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("Changed to uptrend. Attempting purchase.")
        if not in_position:
            order = exchange.create_market_buy_order(f'{ticker}',order_size)
            print('\nStatus:'+order['info']['status'],
                  'Price:'+order['trades'][0]['info']['price'],
                  'Quantity:'+order['info']['executedQty'],
                  'Type:'+order['info']['side'])
            min_sell_price = float(order['trades'][0]['info']['price'])*markup
            in_position = True
            print("Purchased @ $",str(min_sell_price))
        else:
            print("Already in desired trading position, no task.")
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        bar = exchange.fetch_ohlcv(f'{ticker}', timeframe="1m", limit=1)
        price = float(bar[-1][3]) #identifies current low price
        print("Changed to downtrend. Attempting sale.")
        if in_position and price > min_sell_price:
            order = exchange.create_market_sell_order(f'{ticker}',order_size)
            print('Status:'+order['info']['status'],
                  'Price:'+order['trades'][0]['info']['price'],
                  'Quantity:'+order['info']['executedQty'],
                  'Type:'+order['info']['side'])
            in_position = False
            print('Sold @',str(order['trades'][0]['info']['price']),'and we gained ',str(float(1-order['trades'][0]['info']['price']/min_sell_price)),'%')
        else:
            print("Did not find an opportunity to sell, no task.")