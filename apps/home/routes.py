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
        sql=db.session.query(
            User.username,
            Crypto.cmc_id,
            Crypto.slug,
            Crypto.symbol,
            Alert.low_threshold,
            Alert.high_threshold,
            Alert.reference_price,
            Alert.date_created,
        )
        .filter(
            User.username == Crypto.username,
        )
        .filter(
            Crypto.symbol == Alert.symbol,
        )
        .filter(
            User.username == username,
        )
        .statement,
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
                    symbol=symbol,
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
        cryptos_for_json= df_cryptos.to_dict(orient="records")

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment, cryptos=cryptos, cryptos_for_json=cryptos_for_json)

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
