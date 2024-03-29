import json
import sys
import tempfile
from pathlib import Path
from typing import Union

import pandas as pd
import requests_cache
from loguru import logger
from requests import Timeout, TooManyRedirects

logger.remove()
logger.add(
    sys.stderr,
    format="{time} | <lvl>{level}</lvl> {level.icon} | <lvl>{message}</lvl>",
    colorize=True,
)


class CryptoMarket(object):
    _session = None
    __DEFAULT_BASE_URL = "https://pro-api.coinmarketcap.com"
    __DEFAULT_TIMEOUT = 30

    HEADERS = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": "xxxxx-xxxxx-xxx-xxxx-xxxxxxx",
    }

    ENDPOINTS = {
        "listings": "/v1/cryptocurrency/listings/latest",
        "quotes": "/v1/cryptocurrency/quotes/latest",
        "map": "/v1/cryptocurrency/map",
    }

    def __init__(self, base_url=__DEFAULT_BASE_URL):
        self.base_url = base_url
        cache_filename = "coinmarketcap_cache"
        self.cache_file_path = Path(tempfile.gettempdir(), cache_filename)
        self.session = requests_cache.CachedSession(
            cache_name=str(self.cache_file_path), backend="sqlite", expire_after=1800
        )
        self.session.headers.update(self.HEADERS)

    def get(self, url, **kwargs):
        url = self.base_url + url
        try:
            response = self.session.get(
                url, params=kwargs, timeout=self.__DEFAULT_TIMEOUT
            )

            info = json.loads(response.text)
            return info
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            logger.warning(
                f"Error while fetching Url: {url}, with Parameters: {kwargs} and Error: {e}"
            )

    def get_quotes(self, **params: Union[dict, object]) -> pd.DataFrame:
        """See also: https://coinmarketcap.com/api/documentation/v1/#operation/getV2CryptocurrencyQuotesLatest"""
        url = self.ENDPOINTS["quotes"]
        response = self.get(url, **params)
        df = pd.DataFrame(response["data"]).T
        df_price_details = pd.json_normalize(df["quote"]).reset_index(drop=True)
        df = df.drop(["quote"], axis=1).reset_index(drop=True)
        data = pd.concat([df, df_price_details], axis=1)
        return data

    def get_listings(self, **params: Union[dict, object]) -> pd.DataFrame:
        """See also: https://coinmarketcap.com/api/documentation/v1/#operation/getV1CryptocurrencyListingsLatest"""
        url = self.ENDPOINTS["listings"]
        response = self.get(url, **params)
        df = pd.json_normalize(response["data"])
        return df

    def get_cryptos_names(self, **params: Union[dict, object]):
        """See also https://coinmarketcap.com/api/documentation/v1/#operation/getV1CryptocurrencyMap"""
        # TODO: Ordonner par Market cap
        url = self.ENDPOINTS["map"]
        response = self.get(url, **params)
        df = pd.json_normalize(response["data"])
        return df[["id", "name", "symbol", "slug", "rank"]]


if __name__ == "__main__":
    cmc = CryptoMarket()
    parameters = {"slug": "bitcoin", "convert": "EUR"}
    # info = cmc.get_quotes(**parameters)
    # pprint.pprint(info)
    #
    df = cmc.get_listings(convert="EUR")
    df = df[["symbol", "slug", "quote.EUR.price"]].rename(
        columns={"quote.EUR.price": "price_eur"}
    )
    print(df.head())

    # cmc.get_cryptos_names()
