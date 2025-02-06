from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from databases.trade.market_data import (
    marketDataEngine,
    Indexes,
    Assets,
    Exchanges,
    Brokers,
    PerBrokerAssetInfo,
    AssetClasses,
    Countries)
from uuid import uuid4
from alpaca.trading.enums import AssetExchange, AssetClass
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Asset
from data_util import query_asset_id, query_exchange_id, drop_all_tables
import csv

key = "AK15ZEVU7HLP77KZ52MF"
secret = "M76YDIr13LLQeL5FM9BHzVSYoDZzv85O7yfF1q8d"


# first


#drop_all_tables(engine=marketDataEngine)
#exit()
"""
# this defines and then inserts per-broker information
def make_per_broker_info(time, φ: Asset):
    asset_id = query_asset_id(φ.exchange, φ.symbol)
    return PerBrokerAssetInfo(
        timestamp = time,
        broker = "Alpaca",
        asset_id = asset_id,
        tradeable = φ.tradable,
        easy_to_borrow = φ.easy_to_borrow,
        shortable = φ.shortable,
        fractionable = φ.fractionable,
        min_order_size = φ.min_order_size,
        min_trade_increment = φ.min_trade_increment,
        price_increment = φ.price_increment,
        maintenance_margin_requirement = φ.maintenance_margin_requirement
    )


def alpaca_to_internal_asset_class(φ: AssetClass):
    return {
        AssetClass.CRYPTO: "crypto",
        AssetClass.US_EQUITY: "equity",
        AssetClass.US_OPTION: "option"
    }[φ]

def make_assets(φ: Asset):
    asset_class = alpaca_to_internal_asset_class(φ.asset_class)

    if asset_class == "crypto":
        country = "INT"
    else:
        country = "USA" # all alpaca securities and options
    #print(φ.symbol, φ.name, query_exchange_id(φ.exchange), φ.exchange.name)
    #print(φ)
    return Assets(
        id=uuid4(),
        symbol=φ.symbol,
        exchange=query_exchange_id(φ.exchange),
        asset_class=asset_class,
        name=φ.name,
        country=country,
        )


# first we deifne our exchanges and add them (assuming they are not added already)
with Session(marketDataEngine) as session, session.begin():
    # we define and add the broker
    alpaca = Brokers(name="Alpaca", url="https://alpaca.markets/")
    session.merge(alpaca)

    #session.execute(insert(Brokers).values(alpaca).on_conflict_do_nothing(
    #    index_elements=[Brokers.name]
    #))

    # we add the only country in our dataset so far
    session.merge(Countries(code="USA", name="United States of America"))
    session.merge(Countries(code="INT", name="International"))


    # we add the different asset classes we use
    for asset_class in [
        AssetClasses(name="crypto", description="Various differnet cryptocurrencies and crypto products."),
        AssetClasses(name="equity", description="Shares issued by a company that pay a dividend."),
        AssetClasses(name="option", description="Derivatives that allow the optional purchase or sale of an asset.")
    ]:
        session.merge(asset_class)

    # we then define and add our exchanges
    for exchange in list(map(
        lambda exchange: Exchanges(id=uuid4(), name=exchange.name),
        list(AssetExchange)[:-1]
    )):
        session.merge(exchange)

    session.commit()

# we request every asset



now = datetime.now()
all_assets = TradingClient(key, secret, paper=False).get_all_assets()
if type(all_assets) == list:
    with Session(marketDataEngine) as session, session.begin():
        print("Adding asset objects")
        # we first add the asset objects
        for asset in list(map(make_assets, all_assets)):
            session.merge(asset)
        #map(session.add, assets)
    with Session(marketDataEngine) as session, session.begin():
        print(session.execute(select(Assets)).first())
        print("Adding data")
        # then we add the per-asset information
        for info in list(map(lambda φ: make_per_broker_info(now, φ), all_assets)):
            session.merge(info)
else:
    raise(Exception("invalid return on all_assets request, got RawData, wanted List[Asset]"))
 """


# now that we have assets we can start adding indicies, For now only the S&P 500
with Session(marketDataEngine) as session, session.begin():

    print("adding indicies")

    all_alpaca_assets = session.query(PerBrokerAssetInfo.asset_id).where(PerBrokerAssetInfo.broker == "Alpaca").all()
    assets_cleaned = list(map(lambda φ: φ[0], all_alpaca_assets))

    with open("./src/main/sql/SP500.csv", "r") as file:
        reader = csv.reader(file)
        for line in reader:
            symbol: str = line[0]
            asset = session.query(Assets).where(
                Assets.id.in_(assets_cleaned),
                Assets.symbol == symbol
            ).first()
            if asset != None:
                print(asset.name)
                session.merge(Indexes(index="S&P 500", asset_id=asset.id))
            else:
                raise(Exception(f"Error, invalid asset requested: {asset, asset.id}"))
