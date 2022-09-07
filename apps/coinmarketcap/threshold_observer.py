import numpy as np
import pandas as pd

from apps.coinmarketcap.coinmarketcap_api import CryptoMarket

if __name__ == "__main__":
    cmc = CryptoMarket()
    df = cmc.get_listings(convert="EUR")
    df = df[["symbol", "quote.EUR.price"]].rename(
        columns={"symbol": "Symbol", "quote.EUR.price": "Price"}
    )

    data = [
        ["BTC", 19870, 19860, "blackperl"],
        ["ETH", 1574.9, 1575.02, "blackperl"],
        ["ETH", 1574.6, 1574.7, "gotama"],
        ["ETH", 1576, 1574.99, "gotama"],
    ]
    df_obs = pd.DataFrame(
        data, columns=["Symbol", "ReferencePrice", "Threshold", "User"]
    )

    data = df_obs.merge(df, on="Symbol", how="left")

    data["decreasing"] = (data["Threshold"] <= data["ReferencePrice"]) & (
        data["Threshold"] >= data["Price"]
    )
    data["increasing"] = (data["Threshold"] >= data["ReferencePrice"]) & (
        data["Threshold"] <= data["Price"]
    )
    conditions = [
        (data["decreasing"] == True) & (data["increasing"] == False),
        (data["decreasing"] == False) & (data["increasing"] == True),
        (data["decreasing"] == True) & (data["increasing"] == True),
        (data["decreasing"] == False) & (data["increasing"] == False),
    ]

    choices = ["decreasing", "increasing", "error", False]
    data["notification"] = np.select(conditions, choices)
    data = data.drop(["decreasing", "increasing"], axis=1)

#
#     'apprise -vv -t "Test Message Title" -b "Test Message Body" \
#    discord://1016780345712054322/ZLqpN63QakgG1mIdMCBdfdPvQN95fmwFhcWb-TkFe8a8ieJ6zMCikLUV5Cmb4IdOjgm1'
# https://discord.com/api/webhooks/1016780345712054322/ZLqpN63QakgG1mIdMCBdfdPvQN95fmwFhcWb-TkFe8a8ieJ6zMCikLUV5Cmb4IdOjgm1
