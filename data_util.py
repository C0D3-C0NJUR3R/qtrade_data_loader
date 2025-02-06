from functools import cache
from sqlalchemy import select, text, Engine
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from databases.trade.market_data import marketDataEngine, Exchanges, Assets, PerBrokerAssetInfo, Bars, Brokers
from alpaca.trading.enums import AssetExchange
from alpaca.data.models import BarSet, Bar
from pandas import date_range, Interval, interval_range
from datetime import datetime, timedelta
from math import ceil
from uuid import UUID


# divide requests into sections to keep everything in memory compatible
def chunk_datetimes(start: datetime, end: datetime, δ: timedelta) -> list[Interval]:
    """Given a start and an end divide the period into chunks of roguhly δ size.

    Args:
        start (datetime): The start datetime for the period to be chunked.
        end (datetime): The end time for the period to be chunked.
        δ (timedelta): The difference between the start and the end of each chunk.

    Returns:
        list[Interval]: A list of tuples representing the start and end for each period.
    """
    periods = ceil((end - start) / δ)
    return list(interval_range(start, end, periods))


def insert_barset(β: BarSet, transtab: dict[str, UUID]):
    """Given a barset and translation tab insert into the

    Args:
        β (BarSet): a barset
        transtab (dict[str, UUID]): a translation tab for alpaca symbols
    """
    bars: list[Bars] = []
    for vals in β.data.values():
        for bar in vals:
            trade_count = int(bar.trade_count) if bar.trade_count != None else 0
            bars.append(
                Bars(
                    asset=transtab[bar.symbol], # get the asset id for the symbol
                    timestamp=bar.timestamp,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    vwap=bar.vwap,
                    volume=int(bar.volume),
                    trade_count=trade_count,
                )
            )

    with Session(marketDataEngine) as session, session.begin():
        session.add_all(bars)


def alpaca_transtab() -> dict[str, UUID]:
    """Collect all securities we have records for that are from Alpaca.

    Returns:
        dict[str, UUID]: A translation table for translating between UUIDs and symbols for all alpaca symbols.
    """
    assets: dict[str, UUID] = {}
    with Session(marketDataEngine) as session, session.begin():
        assets = dict(session.query(Assets.symbol, Assets.id)\
            .distinct(Assets.symbol)\
            .join(PerBrokerAssetInfo, PerBrokerAssetInfo.asset_id == Assets.id)\
            .join(Bars, Bars.asset == Assets.id)\
            .where(PerBrokerAssetInfo.broker == "Alpaca")\
            .all())
    return assets


def drop_all_tables(engine: Engine):
    """Yes, this drops *all* tables in a schema. It will absolutely wreck
    everything if you use it in prod. As such it requires a few inputs to
    actually do it.
    """
    φ1 = input(f"Type the name of the database as shown here \"{engine.url.database}\": ")
    φ2 = input(f"Are you sure you want to drop all tables in the database and schema? (yes/no) ")
    if φ1 == engine.url.database and φ2 == "yes":
        with engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA market_data CASCADE; CREATE SCHEMA market_data;"))


def query_exchange_id(φ: AssetExchange) -> UUID:
    with marketDataEngine.begin() as conn:
        row = conn.execute(
            select(Exchanges.id)\
                .where(Exchanges.name == φ.name)) \
                .first()
        if row is not None:
            return row[0]
        else:
            raise(Exception(f"invalid exchange requested {φ.name}"))


def query_asset_id(φ: AssetExchange, symbol: str):
    exchange_id = query_exchange_id(φ)
    with marketDataEngine.begin() as conn:
        row = conn.execute(
            select(Assets.id)\
                .where(Assets.symbol == symbol, Assets.exchange == exchange_id)) \
                .first()
        if row is not None:
            return row[0]
        else:
            raise(Exception(f"invalid asset requested {symbol}"))