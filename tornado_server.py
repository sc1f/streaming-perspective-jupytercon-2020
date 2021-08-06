import nbimporter
import random
import logging
import tornado.websocket
import tornado.web
import tornado.ioloop
import pyEX
import perspective
import threading

from datetime import datetime

from tornado_datasources import (
    IEXIntervalDataSource,
    IEXStaticDataSource,
)

from schemas import holdings_schema, last_quote_schema, charts_schema

# Construct our portfolio
symbols = ["AAPL", "MSFT", "AMZN", "TSLA", "SPY", "SNAP", "ZM"]
holdings = {symbol: random.randint(5, 10) for symbol in symbols}

# Initialize the pyEX client - the API key is stored under `IEX_TOKEN` as
# an environment variable.
client = pyEX.Client(version="sandbox")

# Create all the tables and views in one place
TABLES = {
    "holdings": perspective.Table(holdings_schema, index="symbol"),
    "holdings_total": perspective.Table(holdings_schema),
    "quotes": perspective.Table(last_quote_schema),
    "charts": perspective.Table(charts_schema),
}

VIEWS = {name: TABLES[name].view() for name in TABLES.keys()}

class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def get(self):
        self.render("index.html")


def clean_quote(tick):
    for t in tick:
        t["time"] = datetime.now()
    return tick


def clean_charts(tick):
    out = []
    for k, v in tick.items():
        chart = v["chart"]
        for c in chart:
            c["symbol"] = k
            c["quantity"] = holdings[k]
            out.append(c)
    return out


def make_app():
    """Create a `PerspectiveManager` and host our tables and views so they
    can be accessed over a Websocket."""
    MANAGER = perspective.PerspectiveManager()

    # Seed the initial holdings table
    TABLES["holdings"].update(
        {
            "symbol": symbols,
            "quantity": [holdings[symbol] for symbol in symbols],
        }
    )

    # Set up the on_update callbacks
    def update_total(port, delta):
        """When the indexed table updates with the latest price, update the
        unindexed table with the rows that changed."""
        TABLES["holdings_total"].update(delta)

    VIEWS["holdings"].on_update(update_total, mode="row")

    def update_holdings(port, delta):
        TABLES["holdings"].update(delta)

    VIEWS["quotes"].on_update(update_holdings, mode="row")

    MANAGER.host_table("holdings_table", TABLES["holdings"])
    MANAGER.host_table("holdings_total_table", TABLES["holdings_total"])
    MANAGER.host_table("quotes_table", TABLES["quotes"])
    MANAGER.host_table("charts_table", TABLES["charts"])
    
    return tornado.web.Application(
        [
            # create a websocket endpoint that the client Javascript can access
            (
                r"/websocket",
                perspective.PerspectiveTornadoHandler,
                {"manager": MANAGER, "check_origin": True},
            ),
            (r"/", MainHandler),
        ]
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    logging.critical("Listening on http://localhost:8888")
    loop = tornado.ioloop.IOLoop.current()

    # Initialize our datasources
    quotes = IEXIntervalDataSource(
        table=TABLES["quotes"],
        ioloop=loop,
        iex_source=client.last,
        data_cleaner=clean_quote,
        symbols=symbols,
    )

    charts = IEXStaticDataSource(
        table=TABLES["charts"],
        iex_source=client.batch,
        ioloop=loop,
        data_cleaner=clean_charts,
        symbols=symbols,
        fields="chart",
        range_="5y",
    )

    quotes.start()
    charts.start()
    loop.start()
