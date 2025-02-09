#!/usr/bin/env python3
"""This script considers every minute that the NYSE, etc was open and identifies periods
where there are no bars. These are assumed to be missing periods and bars are inserted for
those periods.
"""
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from databases.trade.market_data import Calendar, Bars, marketDataEngine
from datetime import datetime, timedelta
from pandas import Interval, Timestamp
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.models import BarSet
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from data_util import alpaca_transtab, insert_barset
from pytz import utc

def merge_datetime_intervals(ivals: list[Interval]):
    merged: list[Interval] = []
    if ivals != []:
        sorted_ivals = sorted(ivals)
        last_m = sorted_ivals[0]
        for m in sorted_ivals[1:]:
            if m.overlaps(last_m):
                last_m = Interval(last_m.left, m.right, closed='both')
            else:
                merged.append(last_m)
                last_m = m
        if merged == [] or merged[-1] != last_m:
            merged.append(last_m)
    return merged


key = "PKPRLTD20W1NS6PW4QKW"
secret = "cSYBQBuEZRsZdG15fyr3ds0FA5aF0QAsL3yjBs2Q"

feed = StockHistoricalDataClient(key, secret)

def first(φ):
    return φ[0]

def rest(φ):
    return φ[1:]


transtab = alpaca_transtab()
syms = list(transtab.keys())

with Session(marketDataEngine) as session, session.begin():
    maybe_datetieme = session.execute(select(Bars.timestamp).order_by(Bars.timestamp).limit(1)).first()

    if maybe_datetieme != None:
        earliest_datetime = maybe_datetieme[0]
        market_periods = session.execute(
            select(Calendar.open, Calendar.close)
                .distinct()
                .where(
                    Calendar.open > earliest_datetime,
                    Calendar.close < datetime.now(utc)
                )
        ).all()

        for [open, close] in market_periods:
            # we get a list of every minute during the day
            minutes: list[datetime] = list(map(
                lambda n: (timedelta(minutes=n) + open).isoformat(),
                range(0, (close - open).seconds // 60)))
            #print(minutes)
            # then in a given day we find the minutes that are also not
            # included within the dataset
            missing_minutes = list(map(
                lambda φ: Interval(left=Timestamp(φ[0] - timedelta(minutes=1)), right=Timestamp(φ[0]), closed='both'),
                session.execute(
                    text("""
                         SELECT CAST(t.timestamp AS TIMESTAMP)
                         FROM unnest(:mins) as t(timestamp)
                         LEFT JOIN bars b on b.timestamp = CAST(t.timestamp AS TIMESTAMP)
                         WHERE b.timestamp is null
                         """),
                    {"mins": minutes}
                ).all()))

            for ival in merge_datetime_intervals(missing_minutes):
                print("adding bars in:", ival.left, ival.right)
                bars = feed.get_stock_bars(StockBarsRequest(
                    symbol_or_symbols=syms,
                    start=ival.left + timedelta(minutes=1),
                    end=ival.right,
                    feed=DataFeed.SIP,
                    timeframe=TimeFrame(1, TimeFrameUnit.Minute)))
                if type(bars) == BarSet:
                    insert_barset(bars, transtab)

    else:
        raise(Exception("There was no datetime given. Is your market_data.bars table empty?"))