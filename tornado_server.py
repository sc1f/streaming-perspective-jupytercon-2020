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

client = pyEX.Client(version="sandbox")

symbols = ["AAPL", "MSFT", "AMZN", "TSLA", "SPY", "SNAP", "ZM", "JPM"]
holdings = {symbol: random.randint(5, 10) for symbol in symbols}

# Create the table from schema
holdings_table = perspective.Table(holdings_schema, index="symbol")
holdings_view = holdings_table.view()

# Update it with the symbols and quantities of each stock
holdings_table.update(
    {"symbol": symbols, "quantity": [holdings[symbol] for symbol in symbols]}
)

# Create the unindexed total table
holdings_total_table = perspective.Table(holdings_schema)
holdings_total_view = holdings_total_table.view()


def update_total(port, delta):
    """When the indexed table updates with the latest price, update the
    unindexed table with the rows that changed."""
    holdings_total_table.update(delta)


holdings_view.on_update(update_total, mode="row")

quotes_table = perspective.Table(last_quote_schema)
quotes_view = quotes_table.view()


def update_holdings(port, delta):
    holdings_table.update(delta)


quotes_view.on_update(update_holdings, mode="row")

# Clean the quotes to have the right format for sandbox data, which comes with randomly generated `time`s
def clean_quote(tick):
    for t in tick:
        t["time"] = datetime.now()
    return tick

# charts_schema conforms to the output of Historical Prices, with `quantity` added so we can easily join it with `holdings_table`.
charts_table = perspective.Table(charts_schema)
charts_view = charts_table.view()


def clean_charts(tick):
    out = []
    for k, v in tick.items():
        chart = v["chart"]
        for c in chart:
            c["symbol"] = k
            c["quantity"] = holdings[k]
            out.append(c)
    return out



class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def get(self):
        self.render("index.html")


def make_app():
    MANAGER = perspective.PerspectiveManager()

    MANAGER.host_table("holdings_table", holdings_table)
    MANAGER.host_view("holdings_view", holdings_view)

    MANAGER.host_table("holdings_total_table", holdings_total_table)
    MANAGER.host_view("holdings_total_view", holdings_total_view)

    MANAGER.host_table("quotes_table", quotes_table)
    MANAGER.host_view("quotes_view", quotes_view)

    MANAGER.host_table("charts_table", charts_table)
    MANAGER.host_view("charts_view", charts_view)

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

    quotes = IEXIntervalDataSource(
        table=quotes_table,
        ioloop=loop,
        iex_source=client.last,
        data_cleaner=clean_quote,
        symbols=symbols,
    )

    charts = IEXStaticDataSource(
        charts_table,
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
