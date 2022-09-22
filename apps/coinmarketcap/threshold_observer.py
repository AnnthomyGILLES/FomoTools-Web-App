import numpy as np
import pandas as pd
from flask_migrate import Migrate

from apps import db, create_app
from apps.authentication.models import User, Alert, Crypto, Notification
from apps.coinmarketcap.coinmarketcap_api import CryptoMarket
from apps.config import config_dict
from apps.notifications.notification_manager import Notifier


def detect_threshold(data):
    cmc = CryptoMarket()
    list_of_ids = data["cmc_id"].astype(str).tolist()
    list_of_ids = ",".join(list_of_ids)
    df = cmc.get_quotes(convert="EUR", id=list_of_ids)
    df = df[["name", "slug", "EUR.price", "symbol"]]
    df = df[["symbol", "EUR.price"]].rename(columns={"EUR.price": "price"})

    # TODO Remove this for production
    df_obs = data.copy()
    df_obs["reference_price"] = df_obs["low_threshold"] - 100
    data = df_obs.merge(df, on="symbol", how="left")

    data["diminue"] = (data["low_threshold"] < data["reference_price"]) & (
        data["low_threshold"] >= data["price"]
    )
    data["augmente"] = (data["high_threshold"] > data["reference_price"]) & (
        data["high_threshold"] <= data["price"]
    )
    conditions = [
        (data["diminue"] == True) & (data["augmente"] == False),
        (data["diminue"] == False) & (data["augmente"] == True),
        (data["diminue"] == True) & (data["augmente"] == True),
        (data["diminue"] == False) & (data["augmente"] == False),
    ]
    choices = ["diminue", "augmente", "error", "drop"]
    data["notification"] = np.select(conditions, choices)
    data = data.drop(["diminue", "augmente"], axis=1)

    df_user_notifications = data[data["notification"] != "drop"]

    return df_user_notifications


def send_notification(data):
    for index, row in data.iterrows():
        row = row.to_dict()
        discord_api_key = row.get("discord")
        username = row.get("username")
        slug = row.get("slug")
        low_threshold = row.get("low_threshold")
        high_threshold = row.get("high_threshold")
        reference_price = row.get("reference_price")
        price = row.get("price")
        notification = row.get("notification")
        symbol = row.get("symbol")
        webhook_id, webhook_token = discord_api_key.split("/")
        body = None
        if notification == "diminue":
            body = f"Le prix de {slug} ({symbol}) a dépassé votre seuil {low_threshold} et a atteint: {price}."
        elif notification == "augmente":
            body = f"Le prix de {slug} ({symbol})  a dépassé votre seuil {high_threshold} et a atteint: {price}."
        hook = {
            "webhook_id": webhook_id,
            "webhook_token": webhook_token,
        }
        message = {
            "title": "Votre seuil a été atteint!",
            "body": body,
        }
        notifier = Notifier.to_discord(**hook)
        notifier.notify(**message)


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
