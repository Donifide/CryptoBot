import ccxt
import my_config
import schedule
import pandas as pd
pd.set_option('display.max_rows', None)

import warnings
warnings.filterwarnings('ignore')

import numpy as np
from datetime import datetime
import time

#Elimanates time/order issues
ccxt.binanceus({ 'options':{ 'adjustForTimeDifference':True}})

exchange = ccxt.binanceus({
"apiKey": my_config.BINANCE_KEY,
"secret": my_config.BINANCE_SECRET,
'enableRateLimit': True})

def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr

def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()

    return atr

def supertrend(df, period=7, atr_multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
        
    return df

in_position = True
ticker = 'HBAR/USD'
bar = exchange.fetch_ohlcv(f'{ticker}', timeframe='1m', limit=5)
order_size = int(11/bar[4][1]-(.05*(11/bar[4][1]))) # Meet $10 order min_notional

def check_buy_sell_signals(df):
    global in_position,order_size,ticker

    print("Analyzing incoming data... In_position:",in_position)
    print(df.tail(3))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("Changed to uptrend - Buy")
        
        if not in_position:

            order = exchange.create_market_buy_order(f'{ticker}',order_size)
            print('Status:'+order['info']['status'],
                  'Price:'+order['trades'][0]['info']['price'],
                  'Quantity:'+order['info']['executedQty'],
                  'Type:'+order['info']['side'])
            
            #fake_order = exchange.fetch_ohlcv(f'{ticker}', timeframe='1m', limit=1)#
            #print("Fake-buy here:",fake_order)
            in_position = True
        else:
            print("Already in position, no task.")
    
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if in_position: 
            #If in position && previous purchase price << current/market price.
            print("Changed to downtrend - Sell")

            order = exchange.create_market_sell_order(f'{ticker}',order_size)
            print('Status:'+order['info']['status'],
                  'Price:'+order['trades'][0]['info']['price'],
                  'Quantity:'+order['info']['executedQty'],
                  'Type:'+order['info']['side'])
            in_position = False
            
            #fake_order = exchange.fetch_ohlcv(f'{ticker}', timeframe='1m', limit=1)#
            #print("Fake-sell here:",fake_order)
        else:
            print("No selling position, no task.")
            
def run_bot():
    print(f"\nFetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv(f'{ticker}', timeframe='1m', limit=50)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend(df)
    
    check_buy_sell_signals(supertrend_data)
    print()


schedule.every(15).seconds.do(run_bot)


while True:
    schedule.run_pending()
    time.sleep(1)