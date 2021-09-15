#Unpack necessities
from dateutil.tz import tzlocal
from datetime import datetime
import pandas as pd
import numpy as np
import my_config,schedule,time,csv,ccxt

import warnings
warnings.filterwarnings('ignore')

#Elimanates time/order issues, not really sure why this works...
ccxt.binanceus({ 'options':{ 'adjustForTimeDifference':True}})

exchange = ccxt.binanceus({
"apiKey": my_config.BINANCE_KEY,
"secret": my_config.BINANCE_SECRET,
'enableRateLimit': True})

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

####Parameters for INDEPENDENT HARD-VALUE TRADE AMOUNT####
ticker = str(input("Insert ticker: XXXX ")+'/USD')
trade_amount = int(input("Trade amount: $"))
timeframe = "5m" #str(input("Candlestick timeframe: (1m,3m,5m,10m,15m,30m,1d) "))

bal = pd.DataFrame(exchange.fetch_balance()['info']['balances'])
bal['free'] = pd.to_numeric(bal['free'])
bal = bal[bal.free!=0].drop(columns='locked').reset_index(drop=True)
bal = bal[bal['asset']==ticker[:4].replace('/','')].reset_index(drop=True).free[0]

bar = exchange.fetch_ohlcv(f'{ticker}', timeframe=timeframe, limit=5)
order_size = int(trade_amount/bar[4][1]-(.05*(trade_amount/bar[4][1])))
in_position = int(bal*bar[-1][1])>trade_amount

#Collects previous orders.
buys,sells = [],[]

#Decision maker.
def check_buy_sell_signals(df):
    global in_position,order_size,ticker,timeframe,trade_amount,bal,bar
    
    print("Analyzing",ticker,"data... ")
    print(df.tail(3)[['timestamp','open','in_uptrend']])
    print("Balance: $",bal*bar[-1][1])
    
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
            buys.append({'Date':datetime.now().isoformat(),
                              'Status':order['info']['status'],
                              'Price':order['trades'][0]['info']['price'],
                              'Quantity':order['info']['executedQty'],
                              'Type':order['info']['side']})   
            in_position = True
        else:
            print("Currently in position, no task.")
            print("Previous purchase price:",buys[len(buys)-1]['Price'])
    
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        bar = exchange.fetch_ohlcv(f'{ticker}', timeframe="5m", limit=5)
        price = bar[-1][1]
        print("Changed to downtrend.")
        try:
            if in_position and price > float(buys[len(buys)-1]['Price'])+float(buys[len(buys)-1]['Price'])*0.011: #Ensures sell price is 101.1% avg.price
                print("Purchase price < current_market_price - Sell.")
                order = exchange.create_market_sell_order(f'{ticker}',order_size)
                print('Status:'+order['info']['status'],
                      'Price:'+order['trades'][0]['info']['price'],
                      'Quantity:'+order['info']['executedQty'],
                      'Type:'+order['info']['side'])
                sells.append({'Date':datetime.now().isoformat(),
                              'Status':order['info']['status'],
                              'Price':order['trades'][0]['info']['price'],
                              'Quantity':order['info']['executedQty'],
                              'Type':order['info']['side']}) 
                in_position = False
            else:
                print("No selling position, no task.")
        except:
            if in_position and price > bar[0][3]: #Ensures sell price > low price in t-25mins
                
                print("No purchase price data. - Sell.")
                order = exchange.create_market_sell_order(f'{ticker}',order_size)
                print('Status:'+order['info']['status'],
                      'Price:'+order['trades'][0]['info']['price'],
                      'Quantity:'+order['info']['executedQty'],
                      'Type:'+order['info']['side'])
                sells.append({'Date':datetime.now().isoformat(),
                              'Status':order['info']['status'],
                              'Price':order['trades'][0]['info']['price'],
                              'Quantity':order['info']['executedQty'],
                              'Type':order['info']['side']}) 
                in_position = False
            else:
                print("No selling position, no task.")

#Run le bot.
def run_bot():
    print(f"\n\nFetching new bars for {datetime.now(tzlocal()).isoformat()}")
    print("In position:", in_position,";\nTimeframe: ",timeframe,"; Trade amount: $",trade_amount)
    bars = exchange.fetch_ohlcv(f'{ticker}', timeframe=timeframe, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    supertrend_data = supertrend(df)
    check_buy_sell_signals(supertrend_data)
    pd.DataFrame(buys).to_csv('buy_orders.csv',index=True)
    pd.DataFrame(sells).to_csv('sell_orders.csv',index=True)
schedule.every(4).minutes.do(run_bot)
while True:
    schedule.run_pending()
    time.sleep(1)