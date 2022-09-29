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
    Notification,
)
from apps.coinmarketcap.coinmarketcap_api import CryptoMarket
from apps.home import blueprint


class NoInstanceFoundError(Exception):
    pass


@blueprint.route("/index")
@login_required
def index():
    cmc = CryptoMarket()

    df = cmc.get_cryptos_names().sort_values(by="rank").head(10)
    columns = ["CMC Id", "Name", "Rank", "Slug"]

    table_d = df.to_dict(orient="index")

    # User.query.filter_by(username='peter')
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
                Notification.discord,
                Notification.slack,
                Notification.telegram,
            )
            .join(Crypto, Crypto.username == User.username)
            .join(Alert, Alert.cmc_id == Crypto.cmc_id)
            .join(Notification)
            .filter(
                User.username == username,
            )
        ).statement,
        con=db.session.bind,
    )
    user_notification_method = (
        df[["discord", "slack", "telegram"]].dropna(how="all", axis=1).columns
    )
    df["notification_method"] = ", ".join(user_notification_method)
    cryptos = df.to_dict(orient="index")

    return render_template(
        "home/index.html",
        segment="index",
        table_data=table_d,
        columns=columns,
        cryptos=cryptos,
    )


@blueprint.route("/profile.html", methods=("GET", "POST"))
@login_required
def profile():
    try:
        segment = get_segment(request)
        user = User.query.filter_by(username=current_user.username).first()

        if request.method == "POST":
            default_value = ""
            discord_webhook = request.form.get("discord_webhook", default_value)
            discord_token = request.form.get("discord_token", default_value)

            slack_tokena = request.form.get("slack_tokena", default_value)
            slack_tokenb = request.form.get("slack_tokenb", default_value)
            slack_tokenc = request.form.get("slack_tokenc", default_value)
            slack_channel = request.form.get("slack_channel", default_value)

            tgram_chat_id = request.form.get("tgram_chat_id", default_value)
            # user.discord = "/".join([discord_webhook, discord_token])
            user.discord = ", ".join(filter(None, (discord_webhook, discord_token)))
            user.slack = "/".join(
                [slack_tokena, slack_tokenb, slack_tokenc, slack_channel]
            )
            user.discord = tgram_chat_id
            db.session.add(user)
            db.session.commit()

            return redirect(url_for("home_blueprint.index"))

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/profile.html", segment=segment, user_data=user)

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404


@blueprint.route("/<template>", methods=("GET", "POST"))
@login_required
def route_template(template):
    try:

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
            price_notification_method = request.form["price_notification_method"]
            slug = request.form["price_crypto_selected"]
            cmc_id, symbol, price_eur = df_cryptos[df_cryptos["slug"] == slug][
                ["id", "symbol", "price_eur"]
            ].values.tolist()[0]
            low_threshold = request.form["price_low_threshold"]
            high_threshold = request.form["price_high_threshold"]

            if not slug:
                flash("Slug is required!")
            elif not symbol:
                flash("Symbol is required!")
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
                )

                notification = get_or_create(
                    db.session,
                    Notification,
                    discord="1016780345712054322/ZLqpN63QakgG1mIdMCBdfdPvQN95fmwFhcWb-TkFe8a8ieJ6zMCikLUV5Cmb4IdOjgm1",
                    alerts=alert,
                )

                db.session.add(crypto)
                db.session.add(alert)
                db.session.add(notification)
                db.session.commit()
                return redirect(url_for("home_blueprint.index"))

        cryptos = df_cryptos.to_dict(orient="index")

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment, cryptos=cryptos)

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
