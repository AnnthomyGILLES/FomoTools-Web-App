import json
import pprint
import sys
import tempfile
from pathlib import Path

import requests_cache
from loguru import logger
from requests import Timeout, TooManyRedirects

logger.remove()
logger.add(sys.stderr, format="{time} | <lvl>{level}</lvl> {level.icon} | <lvl>{message}</lvl>", colorize=True)


class Market(object):
    _session = None
    __DEFAULT_BASE_URL = 'https://pro-api.coinmarketcap.com'
    __DEFAULT_TIMEOUT = 30

    HEADERS = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '74868bae-9a4c-4b7f-9869-3a69f0b808ff'
    }

    def __init__(self, base_url=__DEFAULT_BASE_URL):
        self.base_url = base_url
        cache_filename = 'coinmarketcap_cache'
        self.cache_file_path = Path(tempfile.gettempdir(), cache_filename)
        self.session = requests_cache.CachedSession(cache_name=str(self.cache_file_path), backend='sqlite',
                                                    expire_after=120)
        self.session.headers.update(self.HEADERS)

    def get(self, url, **kwargs):
        url = self.base_url + url
        try:
            response = self.session.get(url, params=kwargs, timeout=self.__DEFAULT_TIMEOUT)

            info = json.loads(response.text)
            return info
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            logger.warning(f"Error while fetching Url: {url}, with Parameters: {params} and Error: {e}")

    def get_quotes(self, **kwargs):
        url = '/v1/cryptocurrency/quotes/latest'
        params = {}
        params.update(kwargs)
        info = self.get(url, **params)
        pprint.pprint(info)

    def get_listings(self, **kwargs):
        url = '/v1/cryptocurrency/listings/latest'
        params = {}
        params.update(kwargs)
        info = self.get(url, **params)
        pprint.pprint(info)


if __name__ == "__main__":
    cmc = Market()
    parameters = {'slug': 'bitcoin',
                  'convert': 'EUR'}
    # cmc.get_quotes(**parameters)
    cmc.get_listings()
