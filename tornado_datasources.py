import json
import logging
import time
import asyncio
import multiprocessing
import threading
import tornado.ioloop

from functools import partial
from zlib import crc32

# A set of datasources designed to work with Tornado - instead of using
# multiprocessing, they submit all work to the Tornado IOLoop to be scheduled.


class BaseDataSource(object):
    def __init__(
        self, table, ioloop, data_cleaner=None
    ):
        """A base class for a datasource that feeds data into Perspective
        
        Subclasses must implement `get_data`, which retrieves data and
        updates the Perspective table.
        
        Args:
            table (perspective.Table) a Perspective table instance that will
                be updated with new data.
            
            ioloop (tornado.ioloop.IOLoop) a reference to a Tornado IOLoop.
                
        Keyword Args:
            data_cleaner (func) A function that receives data input and
                returns cleaned data before the Perspective table is updated.
        """
        self.table = table  # An already-created Perspective table
        self.ioloop = ioloop
        self._data_cleaner = data_cleaner

    def start(self):
        """Start both the data getter subprocess."""
        self.ioloop.add_callback(self.get_data)
        logging.info("[DataSource] Started")

    def get_data(self):
        """A method that gets data and updates the Perspective Table - must be
        implemented by the child class."""
        raise NotImplementedError("Not implemented!")


def bytes_to_float(b):
    return float(crc32(b) & 0xFFFFFFFF) / 2 ** 32


def str_to_float(s, encoding="utf-8"):
    return bytes_to_float(s.encode(encoding))


class IEXIntervalDataSource(BaseDataSource):
    def __init__(
        self, table, ioloop, iex_source, interval=1000, should_hash=False, **kwargs
    ):
        """A datasource that consumes data from IEX once per `interval` seconds.
        
        Because IEX does not provide streaming APIs for simple quotes, OHLC,
        etc, use this datasource to query the API for updates. If `should_hash` is
        True, the datasource will hash incoming ticks and discard duplicates.
        
        Args:
            iex_source (func) a function from pyEX that returns a single piece of
                data, such as `quote` or `batch`.
        
        Keyword Args:
            kwargs (dict) keyword arguments which will be applied when calling
                the IEX data source. See the pyEX documentation for more details.
        """
        data_cleaner = kwargs.pop("data_cleaner")
        super(IEXIntervalDataSource, self).__init__(
            table, ioloop, data_cleaner=data_cleaner
        )
        self._iex_source = iex_source
        self._iex_source_kwargs = kwargs
        self._interval = interval

        # Hash the dataset so it does not repeatedly enqueue identical datasets.
        self._should_hash = should_hash
        self._last_hash = ""

    def get_data(self):
        """Retrieve data every `interval` seconds, hashing and discarding duplicates
        if necessary."""
        logging.info(
            "[IEXIntervalDataSource] started: fetching every %d seconds",
            self._interval,
        )

        def _get(self):
            data = self._iex_source(**self._iex_source_kwargs)
            if data:
                should_update = True
                if self._should_hash:
                    hashed = str_to_float(json.dumps(data, sort_keys=True))
                    should_update = hashed != self._last_hash
                    if should_update:
                        self._last_hash = hashed
                if should_update:
                    if self._data_cleaner:
                        data = self._data_cleaner(data)
                    self.table.update(data)
        
        callback = tornado.ioloop.PeriodicCallback(callback=partial(_get, self), callback_time=self._interval)
        callback.start()


class IEXStaticDataSource(BaseDataSource):
    def __init__(self, table, ioloop, iex_source, **kwargs):
        """A data source for static data - calls the source once, and then stops.
        
        Good for non-streaming data such as charts and fundamentals."""
        data_cleaner = kwargs.pop("data_cleaner")
        super(IEXStaticDataSource, self).__init__(
            table, ioloop, data_cleaner=data_cleaner
        )
        self._iex_source = iex_source
        self._iex_source_kwargs = kwargs

    def get_data(self):
        data = self._iex_source(**self._iex_source_kwargs)
        if self._data_cleaner:
            data = self._data_cleaner(data)
        self.table.update(data)
