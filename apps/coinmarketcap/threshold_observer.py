import numpy as np
import pandas as pd

from apps.coinmarketcap.coinmarketcap_api import CryptoMarket


def detect_threshold(data):
    cmc = CryptoMarket()
    df = cmc.get_listings(convert="EUR")
    df = df[["symbol", "quote.EUR.price"]].rename(
        columns={"symbol": "Symbol", "quote.EUR.price": "Price"}
    )

    df_obs = pd.DataFrame(
        data,
        columns=["Symbol", "ReferencePrice", "LowThreshold", "HighThreshold", "User"],
    )
    data = df_obs.merge(df, on="Symbol", how="left")
    data["decreasing"] = (data["LowThreshold"] < data["ReferencePrice"]) & (
        data["LowThreshold"] >= data["Price"]
    )
    data["increasing"] = (data["HighThreshold"] > data["ReferencePrice"]) & (
        data["HighThreshold"] <= data["Price"]
    )
    conditions = [
        (data["decreasing"] == True) & (data["increasing"] == False),
        (data["decreasing"] == False) & (data["increasing"] == True),
        (data["decreasing"] == True) & (data["increasing"] == True),
        (data["decreasing"] == False) & (data["increasing"] == False),
    ]
    choices = ["decreasing", "increasing", "error", "drop"]
    data["notification"] = np.select(conditions, choices)
    data = data.drop(["decreasing", "increasing"], axis=1)

    df_user_notifications = data[data["notification"] != "drop"]

    return df_user_notifications


def send_notification(data):
    pass


if __name__ == "__main__":
    # data = [
    #     ["BTC", 19870, 19860, 19875, "blackperl"],
    #     ["ETH", 1700, 1600, 1775, "blackperl"],
    #     ["ETH", 1574.6, np.nan, 1574.7, "gotama"],
    #     ["ETH", 1700, 1602, np.nan, "gotama"],
    # ]

    # WARNING: Don't run with debug turned on in production!
    DEBUG = "True"

    # The configuration
    get_config_mode = "Debug" if DEBUG else "Production"

    try:

        # Load the configuration using the default values
        app_config = config_dict[get_config_mode.capitalize()]

    except KeyError:
        exit("Error: Invalid <config_mode>. Expected values [Debug, Production] ")

    app = create_app(app_config)
    Migrate(app, db)

    with app.app_context():
        # TODO: Correct cartesian product offollowing query
        data = pd.read_sql(
            sql=db.session.query(
                User.username,
                Crypto.slug,
                Crypto.symbol,
                Alert.low_threshold,
                Alert.high_threshold,
                Notification.discord,
            )
            .distinct()
            .statement,
            con=db.session.bind,
        )

        df_user_notifications = detect_threshold(data)
        send_notification(df_user_notifications)

#
#     'apprise -vv -t "Test Message Title" -b "Test Message Body" \
#    discord://1016780345712054322/ZLqpN63QakgG1mIdMCBdfdPvQN95fmwFhcWb-TkFe8a8ieJ6zMCikLUV5Cmb4IdOjgm1'
# https://discord.com/api/webhooks/1016780345712054322/ZLqpN63QakgG1mIdMCBdfdPvQN95fmwFhcWb-TkFe8a8ieJ6zMCikLUV5Cmb4IdOjgm1
