import random

from faker import Faker
from flask_migrate import Migrate

from apps import db, create_app
from apps.authentication.models import (
    Crypto,
    Alert,
    User,
)
from apps.config import config_dict
from apps.home.routes import get_or_create


def create_fake_users(nb_users, nb_cryptos):
    """Generate fake users."""
    try:
        db.create_all()
        faker = Faker()
        for i in range(nb_users):
            username = faker.last_name()

            user = User(
                username=username,
                password="test_password",
                email=faker.email(),
                discord=faker.pystr(20, 40),
                fomobot=faker.pystr(20, 40),
                slack=faker.pystr(20, 40),
                telegram=faker.pystr(20, 40),
            )
            db.session.add(user)
            db.session.commit()

            for _ in range(nb_cryptos):
                cmc_id = random.randint(1, 10000)
                symbol, slug = faker.cryptocurrency()
                crypto = get_or_create(
                    db.session,
                    Crypto,
                    slug=slug,
                    symbol=symbol,
                    username=username,
                    cmc_id=cmc_id,
                )

                alert = get_or_create(
                    db.session,
                    Alert,
                    low_threshold=random.randint(1, 1000),
                    high_threshold=random.randint(1000, 10000),
                    user_id=i + 1,
                    cmc_id=cmc_id,
                    reference_price=random.randint(1, 10000),
                    notification_type=random.choice(
                        ["discord", "slack", "telegram", "fomobot"]
                    ),
                )

                db.session.add(crypto)
                db.session.add(alert)
                db.session.commit()
            print(f"Added {nb_users} fake users to the database.")

    except Exception as e:
        db.session.rollback()


if __name__ == "__main__":
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
        create_fake_users(nb_users=2, nb_cryptos=4)
