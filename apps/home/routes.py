# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import pandas as pd
from flask import render_template, request, flash, url_for, redirect
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from loguru import logger
from sqlalchemy.exc import StatementError

from apps import db
from apps.authentication.models import (
    Crypto,
    Alert,
    User,
)
from apps.coinmarketcap.coinmarketcap_api import CryptoMarket
from apps.home import blueprint

NOTIFICATIONS_METHODS = ("discord", "slack", "telegram")


class NoInstanceFoundError(Exception):
    pass


@blueprint.route("/index")
@login_required
def index():
    cmc = CryptoMarket()

    df = cmc.get_cryptos_names().sort_values(by="rank").head(10)
    columns = ["Logo", "Name", "Rank", "Slug"]

    table_d = df.to_dict(orient="index")

    username = current_user.username

    df = pd.read_sql(
        sql=(
            db.session.query(
                User.username,
                Crypto.cmc_id,
                Crypto.slug,
                Crypto.symbol,
                Alert.low_threshold,
                Alert.high_threshold,
                Alert.reference_price,
                Alert.date_created,
                Alert.notification_type,
                User.discord,
                User.slack,
                User.telegram,
            )
            .join(Crypto, Crypto.username == User.username)
            .join(Alert, Alert.cmc_id == Crypto.cmc_id)
            .filter(
                User.username == username,
            )
        ).statement,
        con=db.session.bind,
    )
    cryptos = df.to_dict(orient="index")

    return render_template(
        "home/index.html",
        segment="index",
        table_data=table_d,
        columns=columns,
        cryptos=cryptos,
    )


@blueprint.route("/profile", methods=("GET", "POST"))
@login_required
def profile():
    try:
        segment = get_segment(request)
        user = User.query.filter_by(username=current_user.username).first()

        if request.method == "POST":
            DEFAULT_VALUE = None
            discord_webhook = request.form.get("discord_webhook", DEFAULT_VALUE)
            discord_token = request.form.get("discord_token", DEFAULT_VALUE)

            slack_tokena = request.form.get("slack_tokena", DEFAULT_VALUE)
            slack_tokenb = request.form.get("slack_tokenb", DEFAULT_VALUE)
            slack_tokenc = request.form.get("slack_tokenc", DEFAULT_VALUE)
            slack_channel = request.form.get("slack_channel", DEFAULT_VALUE)

            tgram_chat_id = request.form.get("tgram_chat_id", DEFAULT_VALUE)
            discord_key = "/".join(
                filter(DEFAULT_VALUE, (discord_webhook, discord_token))
            )
            slack_key = "/".join(
                filter(
                    DEFAULT_VALUE,
                    (slack_tokena, slack_tokenb, slack_tokenc, slack_channel),
                )
            )
            if discord_key != "":
                user.discord = discord_key
            if slack_key != "":
                user.slack = slack_key
            if tgram_chat_id != "":
                user.telegram = tgram_chat_id

            db.session.add(user)
            db.session.commit()

            return redirect(url_for("home_blueprint.index"))

        user_data = user.__dict__.copy()
        notifications = {k: user_data.get(k, None) for k in NOTIFICATIONS_METHODS}

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template(
            "home/profile.html", segment=segment, user_data=notifications
        )

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404


@blueprint.route("/<template>", methods=("GET", "POST"))
@login_required
def route_template(template):
    try:
        user = User.query.filter_by(username=current_user.username).first()
        user_data = user.__dict__.copy()
        notifications = {k: user_data.get(k, None) for k in NOTIFICATIONS_METHODS}
        user_tokens = {
            k: "true" if v is not None else "false" for k, v in notifications.items()
        }
        cmc = CryptoMarket()
        df_cryptos = cmc.get_listings(convert="EUR")
        df_cryptos = df_cryptos[["id", "symbol", "slug", "quote.EUR.price"]].rename(
            columns={"quote.EUR.price": "price_eur"}
        )
        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        if request.method == "POST":
            price_notification_method = request.form.getlist(
                "price_notification_method"
            )
            slug = request.form.get("price_crypto_selected")
            low_threshold = request.form.get("price_low_threshold")
            high_threshold = request.form.get("price_high_threshold")

            if slug is None:
                slug = request.form.get("percent_crypto_selected")
            if not price_notification_method:
                price_notification_method = request.form.getlist(
                    "percent_notification_method"
                )

            cmc_id, symbol, price_eur = df_cryptos[df_cryptos["slug"] == slug][
                ["id", "symbol", "price_eur"]
            ].values.tolist()[0]

            if low_threshold is None:
                low_threshold = int(request.form["percent_low_threshold"])
                low_threshold = price_eur - (price_eur * (low_threshold / 100))

            if high_threshold is None:
                high_threshold = int(request.form["percent_high_threshold"])
                high_threshold = price_eur + (price_eur * (high_threshold / 100))

            if not slug:
                flash("Slug is required!")
            elif not symbol:
                flash("Symbol is required!")
            elif not float(low_threshold) <= price_eur <= float(high_threshold):
                flash(
                    "Les seuils définis doivent contenir le prix de référence. Le prix de référence ne peut pas être "
                    "inférieur au seuil inférieur, et supérieur au seuil supérieur."
                )
            else:
                user_id = (
                    User.query.filter(User.username == current_user.username).first().id
                )
                crypto = get_or_create(
                    db.session,
                    Crypto,
                    slug=slug,
                    symbol=symbol,
                    username=current_user.username,
                    cmc_id=cmc_id,
                )

                alert = get_or_create(
                    db.session,
                    Alert,
                    low_threshold=low_threshold,
                    high_threshold=high_threshold,
                    user_id=user_id,
                    cmc_id=cmc_id,
                    reference_price=price_eur,
                    notification_type=",".join(price_notification_method),
                )

                db.session.add(crypto)
                db.session.add(alert)
                db.session.commit()
                return redirect(url_for("home_blueprint.index"))

        cryptos = df_cryptos.to_dict(orient="index")

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template(
            "home/" + template,
            segment=segment,
            cryptos=cryptos,
            user_tokens=user_tokens,
        )

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404

    except:
        return render_template("home/page-500.html"), 500


def get_or_create(session, model, **kwargs):
    try:
        instance = session.query(model).filter_by(**kwargs).first()
        if not instance:
            raise NoInstanceFoundError
        return instance
    except (StatementError, NoInstanceFoundError):
        logger.debug(f"No results found for query following query: {kwargs}")
        instance = model(**kwargs)
        return instance


# Helper - Extract current page name from request
def get_segment(request):
    try:

        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None
