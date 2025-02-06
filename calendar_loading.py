#from alpaca.trading.models import Calendar
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetExchange
from data_util import query_exchange_id
from databases.trade.market_data import (
    marketDataEngine,
    Calendar
)
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Iterable
from uuid import UUID
from pytz import timezone, utc

key = "AK15ZEVU7HLP77KZ52MF"
secret = "M76YDIr13LLQeL5FM9BHzVSYoDZzv85O7yfF1q8d"

# a list of exchanges with common hours, at least for now
exchanges_with_common_hours: Iterable[UUID] = list(map(query_exchange_id, [
    AssetExchange.NYSE,
    AssetExchange.NASDAQ
]))

eastern_time = timezone('US/Eastern')

def et_to_utc(time: datetime) -> datetime:
    return eastern_time.localize(time).astimezone(utc)


cal = TradingClient(key, secret, paper=False).get_calendar()
if type(cal) == list:
    with Session(marketDataEngine) as session, session.begin():

        for cal_record in cal:
            time = cal_record.date
            open = cal_record.open
            close = cal_record.close
            print(time, et_to_utc(open).isoformat(), et_to_utc(close).isoformat())
            records = map(lambda exchange:
                Calendar(exchange=exchange, date=time, open=et_to_utc(open), close=et_to_utc(close)),
                exchanges_with_common_hours)
            for record in records:
                session.merge(record)
