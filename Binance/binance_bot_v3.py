import ccxt,schedule,warnings,time,ast,config
from supertrend import supertrend as st
import check_buy_sell_signals as cbss
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
name=input("Enter name: ")
tick=input("Insert ticker: ")
ticker=tick+"/"+input("USD or USDT?")
timeframe=input("Timeframe (examples: 1m,5m,15m,30m,1h,2h,6h,1d): ")
order_size = float(input("Order size in "+tick+": "))
in_position = ast.literal_eval(input("Do not accumulate until next buy signal? - True/False: ").capitalize())
min_sell_price=float(input("Minimum sell price: "))
markup=1+float(input("Enter percentage of desired markup: %"))/100
def run_bot():
    print(f"\nFetching new bars for {datetime.now(tzlocal()).isoformat()}")
    print("In position:", in_position,";\nTimeframe: ",timeframe,"\n")
    bars = exchange.fetch_ohlcv(f'{ticker}', timeframe=timeframe, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize(None)
    supertrend_data = st(df)
    cbss(supertrend_data,in_position,order_size,ticker,timeframe,min_sell_price,markup)
    bal = pd.DataFrame(exchange.fetch_balance()['info']['balances'])
    bal['free'] = pd.to_numeric(bal['free'])
    bal = bal[bal.free!=0].drop(columns='locked').reset_index(drop=True)
    bal = bal[bal['asset']==ticker[:4].replace('/','')].reset_index(drop=True).free[0]
    print("\nBalance: $",bal*bars[-1][1],", Position:",bal)
    print("Minimum sell price:",min_sell_price,", Order size:",order_size)
    print(name,"'s profit margin set to:",markup,"%")
schedule.every(randint(42,299)).seconds.do(run_bot)
while True:
    schedule.run_pending()
    time.sleep(1)