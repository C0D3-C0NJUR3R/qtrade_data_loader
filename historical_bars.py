"""A script for requesting historical bars and inserting them.
"""
import traceback
import logging
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.models import BarSet, Bar
from databases.trade.market_data import marketDataEngine, Assets, PerBrokerAssetInfo, Indexes
from sqlalchemy.dialects.postgresql import insert
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pandas import interval_range
import csv


logger = logging.getLogger(__name__)
logging.basicConfig(filename='5_year_data.log', encoding='utf-8', level=logging.WARN)

start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 1, 31)

key = "PKPRLTD20W1NS6PW4QKW"
secret = "cSYBQBuEZRsZdG15fyr3ds0FA5aF0QAsL3yjBs2Q"

def commit_bars(φ: BarSet):
    try:
        with open("market_data.csv", "a") as file:
            bars: list[list[UUID | datetime | float | int]] = []
            for vals in φ.data.values():
                for bar in vals:
                    if bar.symbol != None and bar.timestamp != None and bar.open != None and bar.high != None and bar.low != None and bar.low != None and bar.close != None and bar.volume != None and bar.trade_count != None and bar.vwap != None:
                        bars.append([
                            translation_table[bar.symbol], # get the asset id for the symbol
                            bar.timestamp,
                            bar.open,
                            bar.high,
                            bar.low,
                            bar.close,
                            bar.vwap,
                            int(bar.volume),
                            int(bar.trade_count),
                        ])
                    else:
                        logger.warning("Returned invalid bar:", bar)
            writer = csv.writer(file)
            writer.writerows(bars)
    except Exception as e:
        logger.error(traceback.format_exc())

def first(φ):
    return φ[0]

def rest(φ):
    return φ[1:]

with Session(marketDataEngine) as session, session.begin():
    sp500 = list(map(
        first,
        session.execute(
            text("""
                 SELECT a.symbol
                 FROM market_data.assets a
                    JOIN market_data.indexes i
                        ON a.id = i.asset_id
                 WHERE i.INDEX = 'S&P 500'
                """)).all()))
    all_alpaca_assets = session.query(PerBrokerAssetInfo.asset_id).where(PerBrokerAssetInfo.broker == "Alpaca").all()
    assets_cleaned = list(map(lambda φ: φ[0], all_alpaca_assets))
    # to translate be tween symbols and asset ids we create a translation table
    translation_table: dict[str, UUID] = {}
    for asset in session.query(Assets).where(
        Assets.id.in_(assets_cleaned),
        Assets.symbol.in_(sp500)
    ).all():
        translation_table[asset.symbol] = asset.id

# we then create a list of symbols from the table by simply taking the keys as a list
syms: list[str] = list(translation_table.keys())

# make the datafeed object
data_feed = StockHistoricalDataClient(key, secret)

for ival in interval_range(start_date, end_date, freq=timedelta(days=3)):
    print(f"Making request of {len(syms)} symbols over {(ival.right - ival.left).days} day(s) starting on {ival.left.date()} at {datetime.now().time()}")
    bars = data_feed.get_stock_bars(StockBarsRequest(
        symbol_or_symbols=syms,
        start=ival.left,
        end=ival.right,
        feed=DataFeed.SIP,
        timeframe=TimeFrame(1, TimeFrameUnit.Minute)))

    if type(bars) == BarSet:
        print("Committing bars.")
        commit_bars(bars)

print("All bars committed. Ending program.")
