# this is code to stream alpaca
from alpaca.data.live.stock import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.models import BarSet
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import DataFeed
from alpaca.data.models import Bar
from databases.trade.market_data import Bars, marketDataEngine, Assets, PerBrokerAssetInfo
from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from data_util import alpaca_transtab, insert_barset, chunk_datetimes
from multiprocessing import Pool, cpu_count, Process
from pandas import interval_range
from time import sleep
from math import ceil

pool = Pool(cpu_count() // 2)

key = "PKPRLTD20W1NS6PW4QKW"
secret = "cSYBQBuEZRsZdG15fyr3ds0FA5aF0QAsL3yjBs2Q"


# we execute our catch up code here
# this code checks for any gaps and then loads them into the database
# note, this is done in a separate process and delayed to avoid a situation
# where the system starts close to a minute and then does not catch up


transtab = alpaca_transtab()
assets = list(transtab.keys())

def catch_up(start: datetime):
    sleep(10)
    with Session(marketDataEngine) as session, session.begin():
        client = StockHistoricalDataClient(key, secret)
        # we add 1 to the start time to ensure that previously added minutes are not requested. If that is not done they are.
        for ival in chunk_datetimes(start + timedelta(minutes=1), datetime.now(), timedelta(days=3)):
            print(ival)
            β = client.get_stock_bars(
                    StockBarsRequest(
                        symbol_or_symbols=assets,
                        start=ival.left,
                        end=ival.right,
                        feed=DataFeed.SIP,
                        timeframe=TimeFrame(1, TimeFrameUnit.Minute)))
            if type(β) == BarSet:
                print("Inserting barset of missed bars.")
                insert_barset(β, transtab)
            else:
                raise(Exception("Raw data returned, catch up wants BarSet."))




async def commit_async(φ: Bar):
    print("inserting", φ.symbol, "at", φ.timestamp)
    with marketDataEngine.begin() as conn:
        conn.execute(insert(Bars).values(
            asset=transtab[φ.symbol], # get the asset id for the symbol
            timestamp=φ.timestamp,
            open = φ.open,
            high = φ.high,
            low = φ.low,
            close = φ.close,
            volume = φ.volume,
            trade_count = φ.trade_count,
            vwap = φ.vwap
        ))

with Session(marketDataEngine) as session, session.begin():
    last_bar_time = session.execute(select(Bars.timestamp).order_by(Bars.timestamp.desc()).limit(1)).first()
    if last_bar_time != None:
        last_time = last_bar_time[0]
        p = Process(target=catch_up, args=(last_time,))
        p.start()
    else:
        raise(Exception("No last bar time was found, is the `bars` table empty?"))

data_feed = StockDataStream(key, secret, False, DataFeed.SIP)
data_feed.subscribe_bars(commit_async, *assets)
data_feed.run()