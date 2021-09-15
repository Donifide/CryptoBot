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

in_position = False
ticker = 'BNB/USD'
trade_amount = 30
bar = exchange.fetch_ohlcv(f'{ticker}', timeframe='1d', limit=5) #Timeframe(1m,3m,5m,10m,15m,30m,1d) "))
order_size = float(trade_amount/bar[4][1]-(.05*(trade_amount/bar[4][1])))

#timeframe
tf = "1d"

#Collects previous orders.
buys,sells = [],[]

#Decision maker.
def check_buy_sell_signals(df):
    global in_position,order_size,ticker,tf,trade_amount
    print("Analyzing",ticker,"data... \nIn_position:",in_position,'\n')
    print(df.tail(2)[['timestamp','open','in_uptrend']])
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
            buys.append({'Status':order['info']['status'],
                  'Price':order['trades'][0]['info']['price'],
                  'Quantity':order['info']['executedQty'],
                  'Type':order['info']['side']})  
            in_position = True
        else:
            print("Currently in position, no task.")
            print("Previous purchase price:",buys[len(buys)-1]['Price'])
    
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        bar = exchange.fetch_ohlcv(f'{ticker}', timeframe=timeframe, limit=5)
        price = bar[-1][1]
        if in_position and price > buys[len(buys)-1]['Price']:
            print("Changed to downtrend - Sell")
            order = exchange.create_market_sell_order(f'{ticker}',order_size)
            print('Status:'+order['info']['status'],
                  'Price:'+order['trades'][0]['info']['price'],
                  'Quantity:'+order['info']['executedQty'],
                  'Type:'+order['info']['side'])
            sells.append({'Status':order['info']['status'],
                  'Price':order['trades'][0]['info']['price'],
                  'Quantity':order['info']['executedQty'],
                  'Type':order['info']['side']}) 
            in_position = False
        else:
            print("No selling position, no task.")
#Run
def run_bot():
    print(f"\n\nFetching new bars for {datetime.now().isoformat()}")
    print("In position:", in_position,"; Balance: $",bal*bar[-1][1],"; Timeframe: ",timeframe,"; Trade amount: ",trade_amount)
    bars = exchange.fetch_ohlcv(f'{ticker}', timeframe=tf, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    supertrend_data = supertrend(df)
    check_buy_sell_signals(supertrend_data)
    print("Timeframe: ",tf,"\nTrade amount: ",trade_amount)

schedule.every(200).minutes.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)