#Unpack necessities
import my_config,schedule,time,csv,ccxt
from dateutil.tz import tzlocal
from datetime import datetime
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

#Connect to exchange.
exchange = ccxt.binanceus({
"apiKey": my_config.BINANCE_KEY,
"secret": my_config.BINANCE_SECRET,
'enableRateLimit': True})
ccxt.binanceus({ 'options':{ 'adjustForTimeDifference':True}})

#Parameters
name=input("Enter name: ")
tick=input("Insert ticker: ")
ticker=tick+"/"+input("USD or USDT?")
timeframe="5m" #1m,5m,15m,30m,1h,2h,6h,1d
order_size = input("Order size in "+tick+":")
in_position = input("Do not accumulate until next buy signal? - True/False: ")
min_sell_price=input("Minimum sell price: ")

#Create data collection dataframes
buys,sells = [],[]
pd.DataFrame(buys).to_csv(f"{ticker}_buy_orders_{name}.csv",index=True)
pd.DataFrame(sells).to_csv(f"{ticker}_sell_orders_{name}.csv",index=True)

#Super trend formula.
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

#Analysis & decision making
def check_buy_sell_signals(df):
    global in_position,order_size,ticker,timeframe,trade_amount,previous_price
    print("Analyzing",ticker,"data... ")
    print(df.tail(3)[['timestamp','open','in_uptrend']])
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1
#Buy 
    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("Changed to uptrend. Attempting to buy.")
        if not in_position:
            order = exchange.create_market_buy_order(f'{ticker}',order_size)
            print('Status:'+order['info']['status'],
                  'Price:'+order['trades'][0]['info']['price'],
                  'Quantity:'+order['info']['executedQty'],
                  'Type:'+order['info']['side'])
            buys.append({'Date':datetime.now().isoformat(),
                         'Ticker':ticker,
                         'Status':order['info']['status'],
                         'Price':order['trades'][0]['info']['price'],
                         'Quantity':order['info']['executedQty'],
                         'Type':order['info']['side']})
            previous_price=order['trades'][0]['info']['price']
            in_position = True
            min_sell_price = order['info']['status']
            print("Bought.")
        else:
            print("Already in traded position, no task.")
            try:
                print("Previous purchase price:",buys[len(buys)-1]['Price'])
            except:
                pass
#Sell
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        bar = exchange.fetch_ohlcv(f'{ticker}', timeframe="5m", limit=5)
        price = bar[-1][1]
        print("Changeed to downtrend.")
        try:
            if in_position and price > buys[len(buys)-1]['Price']+buys[len(buys)-1]['Price']*0.011:
                print("Purchase price < current_market_price - Sell.")
                order = exchange.create_market_sell_order(f'{ticker}',order_size)
                print('Status:'+order['info']['status'],
                      'Price:'+order['trades'][0]['info']['price'],
                      'Quantity:'+order['info']['executedQty'],
                      'Type:'+order['info']['side'])
                sells.append({'Date':datetime.now().isoformat(),
                              'Ticker':ticker,
                              'Status':order['info']['status'],
                              'Price':order['trades'][0]['info']['price'],
                              'Quantity':order['info']['executedQty'],
                              'Type':order['info']['side']})
                in_position = False
                print("Sold at or above 1.1% profit.")
        except:
            pass
        if in_position and price > min_sell_price:
            order = exchange.create_market_sell_order(f'{ticker}',order_size)
            print('Status:'+order['info']['status'],
                  'Price:'+order['trades'][0]['info']['price'],
                  'Quantity:'+order['info']['executedQty'],
                  'Type:'+order['info']['side'])
            sells.append({'Date':datetime.now().isoformat(),
                          'Ticker':ticker,
                          'Status':order['info']['status'],
                          'Price':order['trades'][0]['info']['price'],
                          'Quantity':order['info']['executedQty'],
                          'Type':order['info']['side']})
            in_position = False
            print('Sold at price greater than previous purchase price.')
        else:
            print("Did not find opportunity to sell, no task.")

#
def run_bot():
    print(f"\nFetching new bars for {datetime.now(tzlocal()).isoformat()}")
    print("In position:", in_position,";\nTimeframe: ",timeframe)
    bars = exchange.fetch_ohlcv(f'{ticker}', timeframe=timeframe, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize(None)
    supertrend_data = supertrend(df)
    check_buy_sell_signals(supertrend_data)
    try:
        pd.DataFrame(buys).to_csv(f"{ticker}_buy_orders_{name}.csv",index=True)
        pd.DataFrame(sells).to_csv(f"{ticker}_sell_orders_{name}.csv",index=True)
    except:
        pass
    bal = pd.DataFrame(exchange.fetch_balance()['info']['balances'])
    bal['free'] = pd.to_numeric(bal['free'])
    bal = bal[bal.free!=0].drop(columns='locked').reset_index(drop=True)
    bal = bal[bal['asset']==ticker[:4].replace('/','')].reset_index(drop=True).free[0]
    print("Balance: $",bal*bars[-1][1],"Position: ",bal)
schedule.every(299).seconds.do(run_bot)
while True:
    schedule.run_pending()
    time.sleep(1)