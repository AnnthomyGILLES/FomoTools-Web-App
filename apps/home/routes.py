# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound

from apps.coinmarketcap.coinmarketcap_api import CryptoMarket
from apps.home import blueprint


@blueprint.route('/index')
@login_required
def index():
    cmc = CryptoMarket()

    df = cmc.get_cryptos_names().sort_values(by='rank').head(10)
    columns = ["CMC Id", "Name", "Rank", "Slug"]

    table_d = df.to_dict(orient='index')

    return render_template('home/index.html', segment='index', table_data=table_d, columns=columns)


@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):
    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
