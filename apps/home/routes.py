# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from doctest import DocFileCase
import pandas as pd
from flask import render_template, request, flash, url_for, redirect
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound

from apps import db
from apps.authentication.models import Crypto, Alert, User
from apps.coinmarketcap.coinmarketcap_api import CryptoMarket
from apps.home import blueprint


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
            Crypto.slug,
            Crypto.symbol,
            Alert.low_threshold,
            Alert.high_threshold,
        )
        .filter(
            User.username == Crypto.users_name,
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

        df = cmc.get_cryptos_names()

        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        if request.method == "POST":
            slug = request.form["exampleInputEmail1"]
            symbol = request.form["exampleInputSymbol"]

            low_threshold = request.form["exampleInputLowThreshold"]
            high_threshold = request.form["exampleInputHighThreshold"]

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
                    users_name=current_user.username,
                )

                alert = get_or_create(
                    db.session,
                    Alert,
                    low_threshold=low_threshold,
                    high_threshold=high_threshold,
                    user_id=user_id,
                    symbol=symbol,
                )

                db.session.add(crypto)
                db.session.add(alert)
                db.session.commit()
                return redirect(url_for("home_blueprint.index"))

        # asset_name = cmc.get_cryptos_names().name.to_string(index=False)
        # asset_symbol = cmc.get_cryptos_names().name.to_string(index=False)
        cryptos = cmc.get_cryptos_names().to_dict(orient="index")

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment, cryptos=cryptos)

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404

    except:
        return render_template("home/page-500.html"), 500


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
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
