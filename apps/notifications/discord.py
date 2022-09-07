import apprise


def notify_discord(webhook_id, webhook_token, title, body):
    apobj = apprise.Apprise()

    apobj.add(f"discord://{webhook_id}/{webhook_token}")

    apobj.notify(
        body=body,
        title=title,
    )


if __name__ == "__main__":
    # Create an Apprise instance
    params = {
        "webhook_id": "1016780345712054322",
        "webhook_token": "ZLqpN63QakgG1mIdMCBdfdPvQN95fmwFhcWb-TkFe8a8ieJ6zMCikLUV5Cmb4IdOjgm1",
        "title": "Gotama is a damn genius",
        "body": "Yes you are baby!",
    }
    notify_discord(**params)
