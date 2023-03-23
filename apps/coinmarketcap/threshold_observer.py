import numpy as np
import pandas as pd
from flask_migrate import Migrate

from apps import db, create_app
from apps.authentication.models import User, Alert, Crypto
from apps.coinmarketcap.coinmarketcap_api import CryptoMarket
from apps.config import config_dict
from apps.notifications.fomobot.bot import send_discord_bot_notification
from apps.notifications.notification_manager import Notifier


def detect_threshold(data):
    cmc = CryptoMarket()
    list_of_ids = data["cmc_id"].astype(str).tolist()
    list_of_ids = ",".join(list_of_ids)
    df = cmc.get_quotes(convert="EUR", id=list_of_ids)
    df = df[["name", "slug", "EUR.price", "symbol"]]
    df = df[["symbol", "EUR.price"]].rename(columns={"EUR.price": "price"})

    df_obs = data.copy()
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
        slug = row.get("slug")
        low_threshold = row.get("low_threshold")
        high_threshold = row.get("high_threshold")
        price = row.get("price")
        notification = row.get("notification")
        symbol = row.get("symbol")
        fomobot_username = row.get("fomobot")
        body = color = None
        if notification == "diminue":
            body = f"Le prix de {slug} ({symbol}) a dépassé votre seuil {low_threshold} et a atteint: {price}."
            color = 0xFF2600
        elif notification == "augmente":
            body = f"Le prix de {slug} ({symbol})  a dépassé votre seuil {high_threshold} et a atteint: {price}."
            color = 0x00FF00

        message = {
            "title": "Votre seuil a été atteint!",
            "body": body,
        }

        for method in row.get("notification_type").split(","):
            # row = row.to_dict()
            api_key = row.get(method)

            notifier = None
            if method == "discord":
                webhook_id, webhook_token = api_key.split("/")
                hook = {
                    "webhook_id": webhook_id,
                    "webhook_token": webhook_token,
                }
                notifier = Notifier.to_discord(**hook)

            elif method == "fomobot":
                send_discord_bot_notification(
                    fomobot_username, message["title"], message["body"], color
                )
            elif method == "telegram":
                notifier = Notifier.to_telegram("679706949")
            elif method == "slack":
                token_a, token_b, token_c, channel = api_key.split("/")
                slack_params = {
                    "token_a": token_a,
                    "token_b": token_b,
                    "token_c": token_c,
                    "channel": channel,
                }
                notifier = Notifier.to_slack(**slack_params)

            notifier.notify(**message)


if __name__ == "__main__":
    # The configuration
    get_config_mode = "Production"

    try:
        # Load the configuration using the default values
        app_config = config_dict[get_config_mode.capitalize()]

    except KeyError:
        exit("Error: Invalid <config_mode>. Expected values [Debug, Production] ")

    app = create_app(app_config)
    Migrate(app, db)

    with app.app_context():
        data = pd.read_sql(
            sql=(
                db.session.query(
                    User.username,
                    Crypto.slug,
                    Crypto.symbol,
                    Alert.low_threshold,
                    Alert.high_threshold,
                    Alert.reference_price,
                    Alert.cmc_id,
                    Alert.notification_type,
                    User.discord,
                    User.fomobot,
                    User.slack,
                    User.telegram,
                )
                .join(Crypto, Crypto.username == User.username)
                .join(Alert, Alert.cmc_id == Crypto.cmc_id)
            ).statement,
            con=db.session.bind,
        )

        if not data.empty:
            df_user_notifications = detect_threshold(data)
            send_notification(df_user_notifications)
